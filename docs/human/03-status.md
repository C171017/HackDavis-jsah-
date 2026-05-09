# Live Status

> Mirror: [`docs/agent/09-tasks.md`](../agent/09-tasks.md). Sync index: [`docs/SYNC.md`](../SYNC.md).
>
> **Update before every standup (every 4 hours).** Check off completed items, add blockers in [§Blockers](#blockers).

## Current block

- **Block:** A — Setup & decisions
- **T+:** 0
- **Next standup:** T+2

## Block A — Setup (T+0 → T+2)

- [ ] Repo created, branch protections off (hackathon mode)
- [ ] `.env.local` template committed (no secrets)
- [ ] All 5 API keys provisioned (OpenAI, Mapbox, Google Places, ElevenLabs, Twilio)
- [ ] Next.js + Tailwind + shadcn scaffolded, deploys to Vercel
- [ ] Supabase project created, tables migrated
- [ ] Python AI service scaffolded, `/healthz` returns 200
- [ ] Map page renders (empty) at user location
- [ ] Twilio outbound number provisioned and verified

## Block B — Skeleton end-to-end (T+2 → T+6)

- [ ] `/api/pantries` returns mock data; markers render
- [ ] Camera upload component posts to `/api/fridge/scan` (mocked)
- [ ] Recipe page renders 3 mocked recipes
- [ ] Marker click → side panel
- [ ] Python service returns ingredients from one test fridge image (Phase 1 v1)
- [ ] Phase 2 prompt v1 returns 3 fake pantries

## Block C — Phase 1 + 2 real (T+6 → T+12)

- [ ] Phase 1 returns ingredients + 3 recipes for arbitrary fridge photo
- [ ] Preferences (cuisine, diet, max time) flow into Phase 1
- [ ] Phase 2 hits Google Places, returns real pantries within 10mi
- [ ] LLM re-ranks pantries by openNow + distance
- [ ] Map clusters ≥10 pantries cleanly
- [ ] DB caches pantry lookups (`pantries`, `pantry_lookups` tables)

## Block D — Phase 3 voice (T+12 → T+17)

- [ ] ElevenLabs agent + Twilio outbound: one test call works end-to-end
- [ ] `/api/calls/start` accepts N pantries, fans out N parallel calls
- [ ] Live transcripts stream to dashboard via SSE
- [ ] Per-call structured summary (`openUntil`, `hasItems`, `requirements`)
- [ ] Aggregate summary card across all N calls
- [ ] Audio recording stored in Supabase Storage, playable in dashboard

## Block E — Polish & demo (T+17 → T+20)

- [ ] Production deploy stable for 30 min straight
- [ ] Seed demo data loaded for the demo city
- [ ] 90-sec demo video recorded and uploaded
- [ ] Submission form filled
- [ ] Pre-recorded fallback call ready in case Phase 3 fails on stage

## <a id="blockers"></a>Blockers

| Time | Owner | Blocker | Help needed | Resolved? |
|---|---|---|---|---|
| _none yet_ | | | | |

## MVP cuts taken

| Time | What we cut | Why |
|---|---|---|
| _none yet_ | | |

## Demo dry-run results

- [ ] Dry-run 1 at T+18 — runs `_:_:_`, judge questions: ___
- [ ] Dry-run 2 at T+19 — runs `_:_:_`
