# 20-Hour Plan, Ownership & Timeline

> Mirror: [`docs/agent/09-tasks.md`](../agent/09-tasks.md). Sync index: [`docs/SYNC.md`](../SYNC.md).
>
> **Rule:** any change to a task here must be reflected in the agent task list, and vice versa.

## Ownership matrix

| Area | Primary | Backup |
|---|---|---|
| Map (render, markers, popups, geolocation) | **Howie** | Jam |
| Camera/upload UI, recipe page, preferences form | **Jam** | Howie |
| Voice-call live dashboard | **Howie** | Jam |
| Design system (Tailwind tokens, shadcn theme) | **Jam** | — |
| Next.js app shell, routing, auth-lite (anon session id) | **Aryan** | Howie |
| REST API, DB schema, Supabase setup | **Aryan** | — |
| Deployment (Vercel + AI service host) | **Aryan** | Sahil |
| Phase 1 — vision + recipes | **Sahil** | Aryan |
| Phase 2 — pantry locator agent | **Sahil** | Aryan |
| Phase 3 — ElevenLabs voice calls | **Sahil** | Aryan |
| Demo script + 90-sec video | **Howie** | Jam |

## Hour-by-hour timeline

> Times are relative to T+0 (kickoff). Each block ends with a 5-min standup.

### Block A — Setup & decisions (T+0 → T+2)

| H | Howie | Jam | Aryan | Sahil |
|---|---|---|---|---|
| 0–1 | Repo clone, Next.js + Tailwind + shadcn scaffold | Figma sketch (3 screens: Home, Map, Recipe) | Supabase project, env vars in `.env.local`, Vercel link | API keys: OpenAI, Mapbox, Google Places, ElevenLabs, Twilio |
| 1–2 | Map page renders empty Mapbox at user location | Camera/upload component skeleton | `/api/health` works, DB tables created | Python AI service scaffold (FastAPI), `/healthz` works |

**Standup A.** Decisions locked: stack, env, repo conventions. No more bikeshedding.

### Block B — Skeleton works end-to-end (T+2 → T+6)

| H | Howie | Jam | Aryan | Sahil |
|---|---|---|---|---|
| 2–4 | Markers from `/api/pantries` mock data | Upload → POST `/api/fridge/scan` (mocked) | Mock endpoints return canned JSON matching contracts | Phase 1 prompt v1, returns ingredients from one test image |
| 4–6 | Marker click → side panel | Recipe page renders mocked 3 recipes + preferences form | Wire mock endpoints to real Python service via proxy | Phase 1 returns recipes; Phase 2 prompt v1 (returns 3 fake pantries) |

**Standup B.** A tester can: upload fridge → see fake recipes; open map → see fake pantries. **Skeleton must work end-to-end before Block C.**

### Block C — Phase 1 + Phase 2 real (T+6 → T+12)

| H | Howie | Jam | Aryan | Sahil |
|---|---|---|---|---|
| 6–9 | Cluster markers, distance sort, "near me" button | Preferences UX (cuisine chips, diet, max time), loading states | Cache pantry lookups in DB, rate-limit guard | Phase 1 polished; Phase 2 calls Google Places + LLM ranks results |
| 9–12 | Map ↔ panel ↔ "Call this pantry" button | Empty/error states, mobile layout, basic theming | Persist user session, fridge scans, pantry call jobs | Phase 1 + 2 production-quality on real demo data |

**Standup C.** Map shows real pantries. Real fridge photos return real recipes. **If behind, see [§MVP cuts](#mvp-cuts).**

### Block D — Phase 3 voice calls (T+12 → T+17)

| H | Howie | Jam | Aryan | Sahil |
|---|---|---|---|---|
| 12–14 | Dashboard layout: list of in-flight calls + transcripts | Pantry select UI ("Call these 3"), confirmation modal | `/api/calls/start`, `/api/calls/:id/stream` (SSE or WS) | ElevenLabs agent + Twilio outbound configured, can call ONE pantry and return transcript |
| 14–17 | Stream transcripts live, status badges, summary card | Polish, animations, audio playback of call recordings | Job orchestration: fan out N calls in parallel, aggregate | All N calls run in parallel, structured summary returned (`has_item`, `hours`, `notes`) |

**Standup D.** End-to-end demo flow works. **No new features after this.**

### Block E — Polish, demo, fallback (T+17 → T+20)

| H | Howie | Jam | Aryan | Sahil |
|---|---|---|---|---|
| 17–18 | Demo script v1, screen-record raw flows | Visual polish pass, 404/empty states | Production deploy, smoke tests, seed demo data | Pre-record one perfect call as fallback, freeze prompts |
| 18–19 | 90-sec video edit | Mobile QA, tweak copy | Lock branch, only hotfix commits | Stand by for fixes |
| 19–20 | Submit, sleep | Submit, sleep | Submit, sleep | Submit, sleep |

## Phase details (the human-readable version)

### Phase 1

**Goal:** photo of fridge → ingredient list → 3 recipes tailored to user prefs.

- Inputs: image (jpeg/png, ≤8MB), preferences `{cuisine[], diet[], maxMinutes, servings}`.
- Outputs: `{ingredients: [{name, qty?, confidence}], recipes: [{title, time, ingredientsUsed[], ingredientsMissing[], steps[]}]}`.
- Why this matters for demo: the missing ingredients feed Phase 2's search query.

### Phase 2

**Goal:** user location + missing ingredients → ranked pantries with hours/phone/distance.

- Inputs: `{lat, lng}` (or address), optional `{neededItems[]}`.
- Outputs: `[{id, name, lat, lng, address, phone, hours, distanceMeters, openNow}]`.
- Strategy: Google Places `Nearby Search` for "food pantry" within 10mi → LLM agent re-ranks based on `openNow`, distance, and any cached "they had X yesterday" notes from past Phase 3 calls.

### Phase 3

**Goal:** call N pantries in parallel with an AI voice, ask scripted questions, return a structured summary.

- Inputs: `{pantryIds[], questions[]}` (default questions: "Are you open today and until when?", "Do you have <items> available?", "Do I need to bring ID or proof of address?").
- Outputs (per call): `{pantryId, status, durationSec, transcript, structured: {openUntil, hasItems[], requirements[], notes}, audioUrl}`.
- Tech: ElevenLabs Conversational AI agent + Twilio outbound number; one job per pantry, fanned out in parallel; results streamed to the frontend via SSE.
- **Ethics gate:** in dev/demo we **only call our own test phone numbers** (Twilio numbers we own). Never auto-dial real pantries without consent. See [`04-risks.md`](./04-risks.md#ethical-call-policy).

## MVP cuts (drop in this order if behind)

1. Drop voice **recordings** download (keep transcript only).
2. Drop **parallel** in Phase 3 — sequential calls of 2 pantries instead of N.
3. Drop **preferences form** — hardcode "any cuisine, no diet, 30 min".
4. Drop **clusters** — plain markers only.
5. Drop **real Phase 2** — return curated 5-pantry seed list for demo city.
6. Drop **Phase 3 entirely** — show pre-recorded call as a video in the demo.

If you cut, update [`03-status.md`](./03-status.md) and tell the team in standup.

## Definition of done (demo-ready)

- [ ] Open app on phone → upload fridge photo → see 3 recipes in <15s.
- [ ] Open map → see ≥10 real pantries near demo location.
- [ ] Tap "Call these 3 pantries" → see live transcripts → see structured summary in <90s.
- [ ] Deployed at a public URL, works on judge's phone.
- [ ] 90-sec demo video uploaded.
