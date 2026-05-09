"""
PantryPal — AI-Powered Food Pantry Coordinator
HackDavis 2026

Single-file backend: FastAPI serves the API + static frontend.
Run: uvicorn server:app --reload --port 8000
Expose: ngrok http 8000  (needed for Twilio webhooks)
"""

import os
import json
import uuid
import asyncio
import base64
import tempfile
import time
from pathlib import Path
from typing import Optional
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, UploadFile, File, Form, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from twilio.rest import Client as TwilioClient
from twilio.twiml.voice_response import VoiceResponse, Gather

load_dotenv()

# ─── Config ───────────────────────────────────────────────────────────────────
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY", "")
ELEVENLABS_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID", "21m00Tcm4TlvDq8ikWAM")  # Rachel default
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID", "")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN", "")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER", "")
BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")  # Set to ngrok URL in prod
GOOGLE_SHEETS_ID = os.getenv("GOOGLE_SHEETS_ID", "")
GOOGLE_SERVICE_ACCOUNT_JSON = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON", "")

AUDIO_DIR = Path("audio")
AUDIO_DIR.mkdir(exist_ok=True)

# ─── In-memory state ─────────────────────────────────────────────────────────
sessions: dict = {}          # session_id -> session data
ws_connections: dict = {}    # session_id -> WebSocket
call_states: dict = {}       # call_sid -> call conversation state

# ─── App ──────────────────────────────────────────────────────────────────────
app = FastAPI(title="PantryPal")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
app.mount("/audio", StaticFiles(directory="audio"), name="audio")
app.mount("/static", StaticFiles(directory="static"), name="static")


# ─── Helpers ──────────────────────────────────────────────────────────────────

async def call_claude(messages: list, system: str = "", max_tokens: int = 1024) -> str:
    """Call Claude API."""
    async with httpx.AsyncClient(timeout=60) as client:
        body = {
            "model": "claude-sonnet-4-20250514",
            "max_tokens": max_tokens,
            "messages": messages,
        }
        if system:
            body["system"] = system
        resp = await client.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": ANTHROPIC_API_KEY,
                "content-type": "application/json",
                "anthropic-version": "2023-06-01",
            },
            json=body,
        )
        data = resp.json()
        return data["content"][0]["text"]


async def call_claude_vision(image_b64: str, media_type: str, prompt: str) -> str:
    """Call Claude with an image."""
    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": ANTHROPIC_API_KEY,
                "content-type": "application/json",
                "anthropic-version": "2023-06-01",
            },
            json={
                "model": "claude-sonnet-4-20250514",
                "max_tokens": 1024,
                "messages": [{
                    "role": "user",
                    "content": [
                        {"type": "image", "source": {"type": "base64", "media_type": media_type, "data": image_b64}},
                        {"type": "text", "text": prompt},
                    ],
                }],
            },
        )
        data = resp.json()
        return data["content"][0]["text"]


async def generate_speech(text: str) -> str:
    """Generate speech with ElevenLabs, return URL path to audio file."""
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            f"https://api.elevenlabs.io/v1/text-to-speech/{ELEVENLABS_VOICE_ID}",
            headers={
                "xi-api-key": ELEVENLABS_API_KEY,
                "Content-Type": "application/json",
            },
            json={
                "text": text,
                "model_id": "eleven_monolingual_v1",
                "voice_settings": {"stability": 0.5, "similarity_boost": 0.75},
            },
        )
        filename = f"{uuid.uuid4().hex}.mp3"
        filepath = AUDIO_DIR / filename
        filepath.write_bytes(resp.content)
        return f"{BASE_URL}/audio/{filename}"


async def notify_ws(session_id: str, data: dict):
    """Send real-time update to connected WebSocket client."""
    ws = ws_connections.get(session_id)
    if ws:
        try:
            await ws.send_json(data)
        except Exception:
            pass


async def update_google_sheet(row_data: list):
    """Append a row to Google Sheets. Fails silently if not configured."""
    if not GOOGLE_SHEETS_ID or not GOOGLE_SERVICE_ACCOUNT_JSON:
        return
    try:
        import gspread
        from google.oauth2.service_account import Credentials
        creds_dict = json.loads(GOOGLE_SERVICE_ACCOUNT_JSON)
        creds = Credentials.from_service_account_info(creds_dict, scopes=[
            "https://www.googleapis.com/auth/spreadsheets",
        ])
        gc = gspread.authorize(creds)
        sheet = gc.open_by_key(GOOGLE_SHEETS_ID).sheet1
        sheet.append_row(row_data)
    except Exception as e:
        print(f"Google Sheets error: {e}")


# ─── Routes ───────────────────────────────────────────────────────────────────

@app.get("/")
async def index():
    return FileResponse("static/index.html")


@app.post("/api/analyze-fridge")
async def analyze_fridge(image: UploadFile = File(...)):
    """Analyze a fridge photo and extract ingredients."""
    contents = await image.read()
    b64 = base64.b64encode(contents).decode()
    media_type = image.content_type or "image/jpeg"

    prompt = """Look at this photo of a fridge/pantry/food items. 
    Extract every visible food ingredient. Be specific (e.g., "cheddar cheese" not just "cheese").
    
    Return ONLY a JSON array of strings, no other text. Example:
    ["eggs", "whole milk", "cheddar cheese", "spinach", "leftover rice"]"""

    result = await call_claude_vision(b64, media_type, prompt)

    try:
        # Strip markdown code fences if present
        cleaned = result.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        ingredients = json.loads(cleaned)
    except json.JSONDecodeError:
        ingredients = [item.strip().strip('"').strip("'") for item in result.strip("[]").split(",")]

    session_id = uuid.uuid4().hex
    sessions[session_id] = {
        "ingredients": ingredients,
        "missing": [],
        "meals": [],
        "pantries": [],
        "call_results": [],
    }

    return {"session_id": session_id, "ingredients": ingredients}


@app.post("/api/suggest-meals")
async def suggest_meals(request: Request):
    """Suggest meals from available ingredients and identify missing items."""
    body = await request.json()
    session_id = body.get("session_id", "")
    ingredients = body.get("ingredients", [])
    specific_request = body.get("specific_request", "")

    if session_id in sessions:
        sessions[session_id]["ingredients"] = ingredients

    prompt_extra = ""
    if specific_request:
        prompt_extra = f"\n\nThe user specifically wants to make: {specific_request}. Prioritize this but also suggest alternatives."

    prompt = f"""Given these available ingredients: {json.dumps(ingredients)}
{prompt_extra}
Suggest 3-5 meals they can make. For each meal, list what ingredients they already have 
and what they're missing.

Return ONLY valid JSON in this exact format, no other text:
{{
    "meals": [
        {{
            "name": "Meal Name",
            "description": "Brief description",
            "have": ["ingredient1", "ingredient2"],
            "missing": ["ingredient3", "ingredient4"],
            "difficulty": "easy|medium|hard",
            "time_minutes": 30
        }}
    ]
}}"""

    result = await call_claude(
        [{"role": "user", "content": prompt}],
        system="You are a helpful cooking assistant focused on practical, budget-friendly meals. Return only JSON."
    )

    try:
        cleaned = result.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        data = json.loads(cleaned)
    except json.JSONDecodeError:
        data = {"meals": [{"name": "Error parsing meals", "description": result, "have": [], "missing": [], "difficulty": "unknown", "time_minutes": 0}]}

    if session_id in sessions:
        sessions[session_id]["meals"] = data.get("meals", [])
        all_missing = set()
        for meal in data.get("meals", []):
            all_missing.update(meal.get("missing", []))
        sessions[session_id]["missing"] = list(all_missing)

    return data


@app.post("/api/find-pantries")
async def find_pantries(request: Request):
    """Find nearby food pantries using Claude."""
    body = await request.json()
    location = body.get("location", "")
    session_id = body.get("session_id", "")

    prompt = f"""Find real food pantries, food banks, and community fridges near {location}.

Search for actual organizations with real phone numbers. I need at least 3-5 options.

Return ONLY valid JSON in this format, no other text:
{{
    "pantries": [
        {{
            "name": "Pantry Name",
            "address": "Full address",
            "phone": "+1XXXXXXXXXX",
            "hours": "Operating hours if known",
            "notes": "Any relevant notes"
        }}
    ]
}}

If you cannot find real pantries, make your best attempt with organizations you know exist in that area.
Use real phone number format with country code."""

    # Use Claude with a search-oriented prompt
    result = await call_claude(
        [{"role": "user", "content": prompt}],
        system="You are a social services assistant. Find real food assistance resources. Return only JSON.",
        max_tokens=2048,
    )

    try:
        cleaned = result.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        data = json.loads(cleaned)
    except json.JSONDecodeError:
        data = {"pantries": []}

    if session_id in sessions:
        sessions[session_id]["pantries"] = data.get("pantries", [])

    return data


@app.post("/api/call-pantries")
async def call_pantries(request: Request):
    """Deploy voice agent swarm to call pantries simultaneously."""
    body = await request.json()
    session_id = body.get("session_id", "")
    pantries = body.get("pantries", [])
    missing_ingredients = body.get("missing_ingredients", [])
    selected_meal = body.get("selected_meal", "")

    if not TWILIO_ACCOUNT_SID or not TWILIO_AUTH_TOKEN:
        return JSONResponse(
            status_code=400,
            content={"error": "Twilio not configured. Set TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN in .env"}
        )

    twilio_client = TwilioClient(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

    call_ids = []
    for pantry in pantries:
        phone = pantry.get("phone", "")
        if not phone:
            continue

        call_id = uuid.uuid4().hex
        call_states[call_id] = {
            "session_id": session_id,
            "pantry": pantry,
            "missing_ingredients": missing_ingredients,
            "selected_meal": selected_meal,
            "conversation": [],
            "results": {},
            "status": "initiating",
        }

        try:
            call = twilio_client.calls.create(
                to=phone,
                from_=TWILIO_PHONE_NUMBER,
                url=f"{BASE_URL}/api/twilio/voice/{call_id}",
                status_callback=f"{BASE_URL}/api/twilio/status/{call_id}",
                status_callback_event=["completed"],
                timeout=30,
            )
            call_states[call_id]["twilio_sid"] = call.sid
            call_states[call_id]["status"] = "ringing"
            call_ids.append(call_id)

            # Notify frontend
            await notify_ws(session_id, {
                "type": "call_started",
                "call_id": call_id,
                "pantry": pantry["name"],
                "status": "ringing",
            })
        except Exception as e:
            call_states[call_id]["status"] = "failed"
            call_states[call_id]["error"] = str(e)
            await notify_ws(session_id, {
                "type": "call_error",
                "call_id": call_id,
                "pantry": pantry["name"],
                "error": str(e),
            })

    return {"call_ids": call_ids, "message": f"Initiating calls to {len(call_ids)} pantries"}


@app.api_route("/api/twilio/voice/{call_id}", methods=["GET", "POST"])
async def twilio_voice_webhook(call_id: str, request: Request):
    """Initial Twilio webhook — first message to pantry."""
    state = call_states.get(call_id)
    if not state:
        resp = VoiceResponse()
        resp.say("Sorry, an error occurred.")
        resp.hangup()
        return HTMLResponse(str(resp), media_type="application/xml")

    ingredients_list = ", ".join(state["missing_ingredients"][:5])
    greeting = (
        f"Hello! I'm calling on behalf of someone in the community who needs help "
        f"finding a few food items. Could you let me know if you currently have any of "
        f"the following available: {ingredients_list}? "
        f"Please let me know which ones you have."
    )

    state["conversation"].append({"role": "assistant", "text": greeting})
    state["status"] = "in_progress"

    # Notify frontend
    await notify_ws(state["session_id"], {
        "type": "call_update",
        "call_id": call_id,
        "pantry": state["pantry"]["name"],
        "status": "connected",
        "message": "Agent is speaking with pantry...",
    })

    # Try ElevenLabs voice, fall back to Twilio TTS
    resp = VoiceResponse()
    try:
        if ELEVENLABS_API_KEY:
            audio_url = await generate_speech(greeting)
            resp.play(audio_url)
        else:
            resp.say(greeting, voice="Polly.Joanna")
    except Exception:
        resp.say(greeting, voice="Polly.Joanna")

    gather = Gather(
        input="speech",
        action=f"{BASE_URL}/api/twilio/gather/{call_id}",
        timeout=8,
        speech_timeout="auto",
        language="en-US",
    )
    resp.append(gather)
    resp.say("I didn't catch that. Thank you for your time, goodbye.")
    resp.hangup()

    return HTMLResponse(str(resp), media_type="application/xml")


@app.api_route("/api/twilio/gather/{call_id}", methods=["GET", "POST"])
async def twilio_gather_webhook(call_id: str, request: Request):
    """Handle pantry's spoken response."""
    form = await request.form()
    speech_result = form.get("SpeechResult", "")

    state = call_states.get(call_id)
    if not state:
        resp = VoiceResponse()
        resp.say("Thank you. Goodbye.")
        resp.hangup()
        return HTMLResponse(str(resp), media_type="application/xml")

    state["conversation"].append({"role": "pantry", "text": speech_result})

    # Notify frontend of what pantry said
    await notify_ws(state["session_id"], {
        "type": "call_update",
        "call_id": call_id,
        "pantry": state["pantry"]["name"],
        "status": "listening",
        "message": f"Pantry said: {speech_result}",
    })

    # Use AI to analyze the response and decide next action
    conversation_history = "\n".join(
        [f"{'Agent' if c['role'] == 'assistant' else 'Pantry worker'}: {c['text']}" for c in state["conversation"]]
    )

    analysis_prompt = f"""You are analyzing a phone conversation between an AI agent and a food pantry worker.
The agent is looking for these ingredients: {json.dumps(state['missing_ingredients'])}
The user wants to make: {state.get('selected_meal', 'any meal')}

Conversation so far:
{conversation_history}

Analyze the pantry worker's latest response. Return ONLY valid JSON:
{{
    "available": ["list of ingredients they confirmed having"],
    "unavailable": ["list of ingredients they confirmed NOT having"],
    "unclear": ["ingredients with unclear availability"],
    "should_continue": true/false,
    "follow_up_message": "what the agent should say next (ask about unclear items, suggest substitutions for unavailable items, or thank them and hang up)",
    "substitutions_to_ask": ["if something is unavailable, suggest alternatives to ask about"]
}}"""

    analysis = await call_claude(
        [{"role": "user", "content": analysis_prompt}],
        system="You are analyzing a food pantry phone call. Be concise. Return only JSON."
    )

    try:
        cleaned = analysis.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        result = json.loads(cleaned)
    except json.JSONDecodeError:
        result = {
            "available": [], "unavailable": [], "unclear": [],
            "should_continue": False,
            "follow_up_message": "Thank you so much for your help. Have a great day!",
            "substitutions_to_ask": [],
        }

    # Update call state with findings
    state["results"] = {
        "available": result.get("available", []),
        "unavailable": result.get("unavailable", []),
        "substitutions_to_ask": result.get("substitutions_to_ask", []),
    }

    resp = VoiceResponse()

    if result.get("should_continue", False) and len(state["conversation"]) < 8:
        follow_up = result.get("follow_up_message", "Thank you for your help!")
        state["conversation"].append({"role": "assistant", "text": follow_up})

        try:
            if ELEVENLABS_API_KEY:
                audio_url = await generate_speech(follow_up)
                resp.play(audio_url)
            else:
                resp.say(follow_up, voice="Polly.Joanna")
        except Exception:
            resp.say(follow_up, voice="Polly.Joanna")

        gather = Gather(
            input="speech",
            action=f"{BASE_URL}/api/twilio/gather/{call_id}",
            timeout=8,
            speech_timeout="auto",
            language="en-US",
        )
        resp.append(gather)
        resp.say("Thank you for your time. Goodbye!")
        resp.hangup()
    else:
        thank_you = result.get("follow_up_message", "Thank you so much for your help. Have a wonderful day!")
        state["conversation"].append({"role": "assistant", "text": thank_you})
        state["status"] = "completed"

        try:
            if ELEVENLABS_API_KEY:
                audio_url = await generate_speech(thank_you)
                resp.play(audio_url)
            else:
                resp.say(thank_you, voice="Polly.Joanna")
        except Exception:
            resp.say(thank_you, voice="Polly.Joanna")
        resp.hangup()

        # Notify frontend of completion
        await notify_ws(state["session_id"], {
            "type": "call_complete",
            "call_id": call_id,
            "pantry": state["pantry"]["name"],
            "results": state["results"],
        })

        # Update Google Sheets
        await update_google_sheet([
            time.strftime("%Y-%m-%d %H:%M"),
            state["pantry"]["name"],
            state["pantry"].get("phone", ""),
            json.dumps(state["results"].get("available", [])),
            json.dumps(state["results"].get("unavailable", [])),
            state.get("selected_meal", ""),
        ])

    return HTMLResponse(str(resp), media_type="application/xml")


@app.api_route("/api/twilio/status/{call_id}", methods=["GET", "POST"])
async def twilio_status_callback(call_id: str, request: Request):
    """Handle call status updates from Twilio."""
    form = await request.form()
    call_status = form.get("CallStatus", "")

    state = call_states.get(call_id)
    if state:
        state["status"] = call_status
        await notify_ws(state["session_id"], {
            "type": "call_status",
            "call_id": call_id,
            "pantry": state["pantry"]["name"],
            "status": call_status,
        })

    return HTMLResponse("OK")


@app.post("/api/optimize-plan")
async def optimize_plan(request: Request):
    """Given all call results, compute the optimal pantry visit plan."""
    body = await request.json()
    session_id = body.get("session_id", "")
    call_results = body.get("call_results", [])
    user_location = body.get("user_location", "")
    selected_meal = body.get("selected_meal", "")

    prompt = f"""Given these food pantry call results, create an optimal plan for the user.

User wants to make: {selected_meal}
User location: {user_location}

Pantry results:
{json.dumps(call_results, indent=2)}

Create the most efficient plan — minimize travel, maximize ingredients obtained.
If no pantry has everything, suggest which pantries to visit and in what order.
If key ingredients are unavailable anywhere, suggest recipe modifications.

Return ONLY valid JSON:
{{
    "plan": [
        {{
            "pantry_name": "Name",
            "address": "Address",
            "items_to_get": ["item1", "item2"],
            "visit_order": 1
        }}
    ],
    "still_missing": ["items not found anywhere"],
    "recipe_modifications": "Suggestions if ingredients are missing",
    "summary": "Brief human-readable summary of the plan"
}}"""

    result = await call_claude(
        [{"role": "user", "content": prompt}],
        system="You are a logistics optimizer. Return only JSON.",
        max_tokens=1024,
    )

    try:
        cleaned = result.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        data = json.loads(cleaned)
    except json.JSONDecodeError:
        data = {"plan": [], "still_missing": [], "recipe_modifications": "", "summary": result}

    return data


# ─── WebSocket ────────────────────────────────────────────────────────────────

@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    await websocket.accept()
    ws_connections[session_id] = websocket
    try:
        while True:
            data = await websocket.receive_text()
            # Keep-alive / client messages
    except WebSocketDisconnect:
        ws_connections.pop(session_id, None)


# ─── Demo mode (no Twilio) ───────────────────────────────────────────────────

@app.post("/api/demo/call-pantries")
async def demo_call_pantries(request: Request):
    """Simulated pantry calls for demo/testing without Twilio."""
    body = await request.json()
    session_id = body.get("session_id", "")
    pantries = body.get("pantries", [])
    missing_ingredients = body.get("missing_ingredients", [])
    selected_meal = body.get("selected_meal", "")

    async def simulate_call(pantry, delay):
        await asyncio.sleep(delay)
        await notify_ws(session_id, {
            "type": "call_started",
            "call_id": uuid.uuid4().hex,
            "pantry": pantry["name"],
            "status": "ringing",
        })
        await asyncio.sleep(2)
        await notify_ws(session_id, {
            "type": "call_update",
            "call_id": uuid.uuid4().hex,
            "pantry": pantry["name"],
            "status": "connected",
            "message": "Agent is speaking with pantry...",
        })

        # Use AI to generate realistic results
        prompt = f"""Simulate a food pantry's inventory response. The pantry is "{pantry['name']}".
Someone is asking about: {json.dumps(missing_ingredients)}

Food pantries typically have: canned goods, pasta, rice, beans, bread, peanut butter,
cereal, milk, eggs, some produce, cooking oil. They less commonly have: fresh meat,
specialty items, spices, dairy variety.

Return ONLY valid JSON — simulate what this pantry might realistically have:
{{
    "available": ["items they have"],
    "unavailable": ["items they don't"],
    "substitutions": {{"unavailable_item": "suggested substitute they do have"}}
}}"""

        result = await call_claude(
            [{"role": "user", "content": prompt}],
            system="Simulate a realistic food pantry inventory. Return only JSON."
        )

        try:
            cleaned = result.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
            data = json.loads(cleaned)
        except json.JSONDecodeError:
            import random
            available = random.sample(missing_ingredients, min(len(missing_ingredients), len(missing_ingredients) // 2 + 1))
            unavailable = [i for i in missing_ingredients if i not in available]
            data = {"available": available, "unavailable": unavailable, "substitutions": {}}

        await asyncio.sleep(3)
        await notify_ws(session_id, {
            "type": "call_complete",
            "call_id": uuid.uuid4().hex,
            "pantry": pantry["name"],
            "results": data,
        })

        return {"pantry": pantry["name"], "results": data}

    # Launch all calls concurrently with staggered starts
    tasks = [simulate_call(p, i * 1.5) for i, p in enumerate(pantries)]
    results = await asyncio.gather(*tasks)

    return {"results": results, "message": "Demo calls completed"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
