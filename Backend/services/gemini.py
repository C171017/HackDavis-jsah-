import json
import os
import sys
import asyncio
from io import BytesIO
from pathlib import Path
from google import genai
from google.genai import types
from PIL import Image


PROMPT = """You are a vision system for a food-security planning app.
 
List every food item visible in this fridge photo. For each item, infer:
- name: simple food name (e.g. "milk", "spinach", "leftover pasta")
- quantity: visible amount (e.g. "half gallon", "3 eggs"), or null
- expiry_estimate: one of "today" | "1-2_days" | "3-5_days" | "1-2_weeks" | "long_shelf"
  Use visible cues: wilting, browning, mold, condensation, dated containers, freshness
  of produce. When unsure, default to category norms (greens "3-5_days", milk "1-2_weeks",
  condiments "long_shelf").
- confidence: 0..1 on the identification.
 
Be inclusive — half-used containers and leftovers count.
 
Respond with STRICT JSON ONLY (no markdown fences):
{
  "ingredients": [
    {"name": "...", "quantity": "...", "expiry_estimate": "...", "confidence": 0.9}
  ],
  "notes": "short overall observation or null"
}
"""


def prepare_image(image_bytes: bytes, max_dim: int = 1568) -> tuple[bytes, str]:
    """Resize + fix EXIF rotation. Phone photos are huge; ~1500px is plenty for VLM."""
    img = Image.open(BytesIO(image_bytes))


    orientation = img.getexif().get(274)
    if orientation == 3:
        img = img.rotate(180, expand=True)
    elif orientation == 6:
        img = img.rotate(270, expand=True)
    elif orientation == 8:
        img = img.rotate(90, expand=True)
 
    if max(img.size) > max_dim:
        scale = max_dim / max(img.size)
        img = img.resize((int(img.width * scale), int(img.height * scale)), Image.LANCZOS)
 
    if img.mode != "RGB":
        img = img.convert("RGB")
 
    buf = BytesIO()
    img.save(buf, format="JPEG", quality=88)
    return buf.getvalue(), "image/jpeg"
 
 
async def extract_ingredients(image_bytes: bytes) -> dict:
    """Send a fridge photo to Gemini, get back structured ingredients with expiry hints."""
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY env var not set")
 
    client = genai.Client(api_key=api_key)
    image_bytes, mime_type = prepare_image(image_bytes)
 
    response = await client.aio.models.generate_content(
        model="gemini-2.5-flash",
        contents=[
            types.Part.from_bytes(data=image_bytes, mime_type=mime_type),
            PROMPT,
        ],
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            temperature=0.2,
        ),
    )
 
    try:
        return json.loads(response.text)
    except json.JSONDecodeError as e:
        raise ValueError(f"Gemini returned non-JSON response: {e}\nRaw: {response.text[:500]}")
 
 
async def main():
    if len(sys.argv) < 2:
        print("usage: python extract_ingredients.py <image_path>")
        sys.exit(1)
 
    path = Path(sys.argv[1])
    if not path.exists():
        print(f"file not found: {path}")
        sys.exit(1)
 
    print(f"reading {path.name} ({path.stat().st_size:,} bytes)...")
    result = await extract_ingredients(path.read_bytes())
 
    ingredients = result.get("ingredients", [])
    print(f"\nfound {len(ingredients)} items:\n")
    for ing in ingredients:
        name = ing.get("name", "?")
        qty = ing.get("quantity") or "?"
        exp = ing.get("expiry_estimate", "?")
        conf = ing.get("confidence")
        conf_str = f"conf={conf:.2f}" if conf is not None else ""
        print(f"  • {name:<22} expires: {exp:<12} qty: {qty:<18} {conf_str}")
 
    if result.get("notes"):
        print(f"\nnotes: {result['notes']}")
 
    near_expiry = [i for i in ingredients if i.get("expiry_estimate") in ("today", "1-2_days")]
    if near_expiry:
        print(f"\n near-expiry (Backboard should prioritize these in recipes):")
        for i in near_expiry:
            print(f"   - {i['name']} ({i['expiry_estimate']})")
 
 
if __name__ == "__main__":
    asyncio.run(main())
