# Risks & Fallbacks

> Mirror: [`docs/agent/02-conventions.md#fallback-rules`](../agent/02-conventions.md#fallback-rules). Sync index: [`docs/SYNC.md`](../SYNC.md).

## Top risks (in order of likelihood)

### 1. ElevenLabs / Twilio outbound calling won't work on time

**Why:** outbound voice agents are the most failure-prone piece. Twilio account verification can take time, ElevenLabs Conversational AI quotas may need approval, and audio plumbing is fiddly.

**Detection:** at **T+14**, if we don't have one real outbound call working end-to-end, escalate.

**Fallback ladder (apply in order):**
1. Drop parallel — call 2 pantries sequentially (still demos the idea).
2. Drop live transcript streaming — show the transcript only after the call completes.
3. Replace live call with a **pre-recorded** call we made earlier today, played back as if live.
4. Show a static "what this would look like" mock screen with a voiceover in the demo video.

### 2. Google Places billing card requirement blocks us

**Why:** Google requires a credit card to enable Places API even on the free tier.

**Detection:** at **T+1**, if no one on the team is willing to attach a card.

**Fallback:**
- Use **Mapbox Geocoding + a curated 30-pantry seed dataset** for the demo city. Sahil generates this with a single GPT call from public data; Aryan loads it into Supabase. Demo still works; Phase 2 just queries the seed set instead of Google.

### 3. Vision model misreads fridge contents

**Why:** GPT-4o vision is good but not perfect; weird angles, glare, opaque containers will trip it.

**Fallback:**
- Allow user to **edit the ingredient list** before generating recipes (add/remove chips). This is a UX win anyway — ship it in Block C.
- Provide a "Use sample fridge" button that runs the demo on a known-good test image. Critical for the demo so we can recover if the live photo fails.

### 4. Map tile loading is slow on conference Wi-Fi

**Fallback:**
- Pre-warm the demo map view (centered on demo city, zoom 12) on page load.
- Keep `prefers-reduced-motion` styles ready in case animations stutter.

### 5. Single point of failure: Sahil

**Why:** Sahil owns all 3 AI phases. If he gets stuck or sleep-deprived, the demo collapses.

**Mitigation:**
- Aryan is the backup on every phase. Aryan reviews Phase 1 end-of-Block-B, Phase 2 end-of-Block-C, and pairs on Phase 3 in Block D.
- Each phase has a "**stub-mode**" env flag (`PHASE_1_STUB=true` etc.) that returns canned responses. Frontend never knows the difference. See [`docs/agent/02-conventions.md`](../agent/02-conventions.md#stub-mode).

### 6. Mobile Safari quirks

**Why:** judges will likely open it on iPhone. Safari hates: large image uploads, getUserMedia without HTTPS, autoplay audio.

**Mitigation:**
- Test on a real iPhone at end of Block C and Block D.
- Always ship over HTTPS (Vercel handles this).
- Audio playback in the call dashboard requires user gesture — gate it behind a play button.

## <a id="ethical-call-policy"></a>Ethical call policy

We are an AI calling real businesses. We must:

- **Never auto-dial real pantries during dev or demo.** Use Twilio test numbers we own.
- For the live demo, our "pantries" are 3 of our own phones (or Twilio numbers), each running a script that simulates a pantry receptionist. This still exercises the full pipeline and looks real to judges.
- The agent must **identify itself as an AI** in the first sentence of every call. ElevenLabs prompt enforces this.
- Submit project with a `README` note acknowledging this and proposing real-world consent flow (pantries opt in to receive AI inquiries) as future work.

## Demo-day backup plan

- **Primary:** live demo on judge's phone via deployed URL.
- **Backup 1:** live demo on our own laptop on tethered hotspot (no conference Wi-Fi dependency).
- **Backup 2:** pre-recorded 90-sec demo video on a USB stick.
- **Backup 3:** screenshots in slides.

Always have all four ready.
