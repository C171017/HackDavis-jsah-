# 🥫 PantryPal — AI-Powered Food Pantry Coordinator

**HackDavis 2026**

Photograph your fridge → AI extracts ingredients → suggests meals → deploys a swarm of AI voice agents that simultaneously call nearby food pantries to check availability and negotiate substitutions in real-time → returns an optimized pickup plan.

## Quick Start (5 min)

```bash
# 1. Clone / enter directory
cd pantry-pal

# 2. Install dependencies
pip install -r requirements.txt

# 3. Set up environment
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY (minimum required)

# 4. Run
python server.py
# → Open http://localhost:8000
```

That's it for demo mode. The app works end-to-end with just an Anthropic API key — voice calls are simulated by AI.

## Full Setup (with real phone calls)

### Twilio (voice calls)
1. Create account at https://twilio.com
2. Get a phone number
3. Add to `.env`: `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_PHONE_NUMBER`
4. Install ngrok: `npm install -g ngrok`
5. Run: `ngrok http 8000`
6. Set `BASE_URL` in `.env` to your ngrok URL (e.g., `https://abc123.ngrok.io`)
7. Uncheck "Demo mode" in the app

### ElevenLabs (natural voice)
1. Get API key from https://elevenlabs.io
2. Add to `.env`: `ELEVENLABS_API_KEY`
3. Optional: choose a voice ID from their library

### Google Sheets (live logging)
1. Create a Google Cloud service account
2. Share your Google Sheet with the service account email
3. Add sheet ID and service account JSON to `.env`

## Architecture

```
User's Phone/Browser
    │
    ├── 📸 Camera → Fridge photo
    │       ↓
    ├── 🧠 Claude Vision API → Ingredient extraction
    │       ↓
    ├── 🍳 Claude API → Meal suggestions + missing ingredients
    │       ↓
    ├── 📍 Claude API → Find nearby food pantries
    │       ↓
    ├── 📞 Twilio + ElevenLabs → Concurrent voice agent swarm
    │       ↓ (WebSocket real-time updates)
    ├── 📊 Google Sheets → Live call results logging
    │       ↓
    └── 🗺️ Claude API → Optimized pickup plan
```

## Tech Stack

| Layer | Tech |
|-------|------|
| Frontend | React 18 (CDN, no build step) |
| Backend | Python FastAPI |
| AI Vision | Claude Sonnet (Anthropic API) |
| AI Planning | Claude Sonnet (Anthropic API) |
| Voice Calls | Twilio + ElevenLabs |
| Real-time | WebSockets |
| Database | Google Sheets API |
| Tunnel | ngrok (for Twilio webhooks) |

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Serves frontend |
| POST | `/api/analyze-fridge` | Upload fridge photo → ingredient list |
| POST | `/api/suggest-meals` | Ingredients → meal suggestions |
| POST | `/api/find-pantries` | Location → nearby pantry list |
| POST | `/api/call-pantries` | Deploy voice agent swarm (real Twilio) |
| POST | `/api/demo/call-pantries` | Simulated calls (no Twilio needed) |
| POST | `/api/optimize-plan` | Call results → optimal pickup plan |
| WS | `/ws/{session_id}` | Real-time call status updates |

## Demo Tips

1. **Start in demo mode** — works without Twilio, simulates realistic call results
2. Have a real fridge photo ready (or use any food photo from the internet)
3. Use a local zip code so pantry results feel real
4. The Google Sheet updating live is a great visual — have it open on another screen
5. If demoing real calls, call your own phone first to test

## Credits

Built for HackDavis 2026 — Social Good Hackathon
