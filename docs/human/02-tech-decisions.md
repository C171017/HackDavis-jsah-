# Tech Decisions & Rationale

> Mirrors: [`docs/agent/01-architecture.md`](../agent/01-architecture.md) (system shape), [`docs/agent/04-frontend-spec.md`](../agent/04-frontend-spec.md) (frontend), [`docs/agent/03-api-contracts.md`](../agent/03-api-contracts.md) + [`docs/agent/05-backend-spec.md`](../agent/05-backend-spec.md) (backend). Sync index: [`docs/SYNC.md`](../SYNC.md).

## TL;DR stack

- **Frontend:** Next.js 15 (App Router) + TypeScript + Tailwind + shadcn/ui + `react-map-gl` + Mapbox GL JS.
- **Backend (app):** Next.js API routes (TypeScript) for CRUD/sessions/streaming. Hosted on Vercel.
- **Backend (AI):** FastAPI (Python) microservice for Phases 1–3, owned by Sahil. Hosted on Render or Fly.io.
- **DB / Auth:** Supabase (Postgres + Storage for fridge photos). Anonymous session id; no real auth for hackathon.
- **Map renderer:** Mapbox GL JS via `react-map-gl`.
- **Pantry data:** Google Places API (`Nearby Search`, keyword=`food pantry`), cached in Supabase.
- **AI vision + recipes:** OpenAI GPT-4o (single multimodal call for ingredients + recipes; tool-call for structured output).
- **Voice calls:** ElevenLabs Conversational AI agent + Twilio outbound voice for Phase 3.
- **Deploy:** Vercel (web) + Render (Python AI service) + Supabase (DB).

## <a id="frontend"></a>Frontend

- **Why Next.js App Router:** server components let us keep API keys server-side (Mapbox token excepted), file-based routing is fast to set up, Vercel deploy is one click, and SSE streaming for Phase 3 is trivial via Route Handlers.
- **Why Tailwind + shadcn/ui:** copy-paste components, consistent look in <2 hours, no design debate.
- **Why `react-map-gl`:** ergonomic React API around Mapbox GL JS, declarative markers/popups, plays nicely with our component model.

## <a id="backend"></a>Backend

- **Two services, one repo (monorepo) is overkill for 20h.** Two repos slows us down. We'll do **one repo, two services**: Next.js app at root, Python AI service in `services/ai/`. Aryan owns the boundary contract.
- **Why Supabase:** Postgres + Storage + Realtime, free tier, no infra to manage, generous limits.
- **Why Python for AI:** Sahil's existing comfort, best ecosystem for OpenAI/ElevenLabs/Twilio SDKs, easy FastAPI scaffolding.
- **Streaming Phase 3 transcripts:** Python service writes events to Supabase `call_events` table → Next.js Route Handler subscribes via Supabase Realtime and re-emits as SSE to the browser. (Avoids exposing the Python service to the public internet.)

## The map decision

We considered four options. **We chose Mapbox + Google Places.**

| Option | Why we considered | Why we passed |
|---|---|---|
| **Mapbox GL JS** ✅ chosen | Best polish per hour spent; great React bindings; free at our scale | Needs a token (2-min signup, no card) |
| Google Maps JS API | Best built-in pantry data via Places API | Requires billing card on the Google account, slower to style |
| Leaflet + OSM | Zero config, no key | Looks plain by default; markers/clustering require more glue |
| MapLibre GL | OSS Mapbox alternative | Tile provider story is fiddlier than just using Mapbox |

**Pantry data:** we still use **Google Places API** server-side (one shared API key in Aryan's `.env`) just for the data — not for rendering. Best of both worlds: Mapbox visuals, Google's data.

**Geolocation:** `navigator.geolocation` with manual zip/address fallback (Mapbox Geocoding API).

**Fallback:** if Google Places billing is a blocker, we ship a **30-row curated seed dataset** for one demo city. See [`04-risks.md`](./04-risks.md#pantry-data-blocked).

## What we said no to

- **Real auth (Clerk/NextAuth).** Anonymous session cookie is enough for a hackathon. Add real auth post-demo.
- **Native mobile app.** PWA + responsive web only.
- **Custom CV model for fridge.** GPT-4o vision is faster and more accurate than anything we'd train in 20h.
- **LangChain / LangGraph.** Adds setup cost. We use raw OpenAI tool calls; orchestrate the 3 phases in plain Python.
- **Realtime collab on the map.** Single user only.
- **Fancy clustering library beyond `supercluster`.** Default behavior is fine.
- **Internationalization.** English only for demo.

## Environment variables (overview)

Owned by Aryan. Full list in [`docs/agent/02-conventions.md`](../agent/02-conventions.md#environment-variables). Stored in 1Password vault "FoodPantryHack" — share with team at T+0.

## Open questions (decide in Block A)

- [ ] Demo city? (affects seed pantry data) — proposal: **wherever the hackathon is held**.
- [ ] Twilio number provisioned? (10-min signup, ~$1/mo, instant outbound). Aryan to do at T+0.
- [ ] ElevenLabs Conversational AI quota check on our account. Sahil to verify at T+0.
