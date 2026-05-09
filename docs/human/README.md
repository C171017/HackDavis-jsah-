# Food Pantry App — Human Docs

> Mirror: [`docs/agent/README.md`](../agent/README.md). Sync index: [`docs/SYNC.md`](../SYNC.md).

A 20-hour hackathon project. We help people who are food-insecure (or just curious) **see what's in their fridge, find a nearby food pantry on a map, and let an AI voice agent call the pantries on their behalf to ask what's available**.

## The 30-second pitch

> "Open the camera. Snap your fridge. Our AI tells you what you have and 3 recipes you can make tonight. If you're short on something, an agent finds the nearest food pantries on a map — and with one tap, calls all of them at once with an AI voice to ask what's in stock and when they're open. You get the answers in a single dashboard."

## The team

| Name | Role | Owns |
|---|---|---|
| **Howie** | Frontend | Map UI, pantry detail panel, voice-call dashboard |
| **Jam** | Frontend | Camera/upload UI, recipe view, preferences form, design system |
| **Aryan** | Backend | API, DB, auth-lite, integration glue, deployment |
| **Sahil** | AI (3 phases) | Phase 1 vision → recipes, Phase 2 pantry locator agent, Phase 3 ElevenLabs voice calls |

## The three phases (what Sahil is building)

1. **Phase 1 — Fridge vision → recipes.** User uploads a fridge photo → vision model lists ingredients → recipe model (with user preferences: cuisine, diet, time) returns 3 recipes.
2. **Phase 2 — Pantry locator agent.** AI agent takes user location + missing ingredients → returns ranked nearby food pantries (with phone, hours, distance) → frontend pins them on the map.
3. **Phase 3 — Parallel voice calls.** User selects N pantries → ElevenLabs Conversational AI agent calls all of them simultaneously asking "do you have X, when are you open?" → results stream back into a live dashboard.

## Doc map (this folder)

- [`01-plan.md`](./01-plan.md) — 20-hour plan, ownership matrix, hour-by-hour timeline, MVP cuts.
- [`02-tech-decisions.md`](./02-tech-decisions.md) — stack rationale, the map choice, what we said no to.
- [`03-status.md`](./03-status.md) — live checklist. Update at every standup.
- [`04-risks.md`](./04-risks.md) — what can break, fallback plans, demo backup.

## Doc map (the AI side)

If you want the precise specs an AI coding agent will read, see [`docs/agent/`](../agent/). Pairs are listed in [`docs/SYNC.md`](../SYNC.md).

## Standup cadence

Every 4 hours: 5-minute standup. Each person says (1) what shipped, (2) what's blocking, (3) next 4-hour goal. Update [`03-status.md`](./03-status.md) before standing up.
