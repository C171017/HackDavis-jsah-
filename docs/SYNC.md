# Docs Sync Map

Two parallel trees, one source of truth per topic. Humans read `human/`, AI agents read `agent/`. **When you change one side, update its mirror in the same commit.**

## How to read this

- `human/` — narrative, decisions, ownership, status. Optimized for skim + standup.
- `agent/` — precise specs (file paths, schemas, env vars, function signatures). Optimized for code generation.
- Every file in either tree has a banner at the top pointing to its mirror.
- This file is the index of pairs. Update the "Last synced" column whenever you touch a pair.

## Mirror table

| Topic | Human doc | Agent doc | Owner | Last synced |
|---|---|---|---|---|
| Project overview | [`human/README.md`](./human/README.md) | [`agent/README.md`](./agent/README.md) | All | 2026-05-09 |
| Plan, timeline, ownership | [`human/01-plan.md`](./human/01-plan.md) | [`agent/09-tasks.md`](./agent/09-tasks.md) | All | 2026-05-09 |
| Tech & architecture | [`human/02-tech-decisions.md`](./human/02-tech-decisions.md) | [`agent/01-architecture.md`](./agent/01-architecture.md) | Aryan | 2026-05-09 |
| Frontend | [`human/02-tech-decisions.md`](./human/02-tech-decisions.md#frontend) | [`agent/04-frontend-spec.md`](./agent/04-frontend-spec.md) | Howie + Jam | 2026-05-09 |
| Backend & API | [`human/02-tech-decisions.md`](./human/02-tech-decisions.md#backend) | [`agent/03-api-contracts.md`](./agent/03-api-contracts.md), [`agent/05-backend-spec.md`](./agent/05-backend-spec.md) | Aryan | 2026-05-09 |
| Phase 1 — Fridge vision → recipes | [`human/01-plan.md`](./human/01-plan.md#phase-1) | [`agent/06-phase1-fridge-vision.md`](./agent/06-phase1-fridge-vision.md) | Sahil | 2026-05-09 |
| Phase 2 — Pantry locator agent | [`human/01-plan.md`](./human/01-plan.md#phase-2) | [`agent/07-phase2-pantry-locator.md`](./agent/07-phase2-pantry-locator.md) | Sahil | 2026-05-09 |
| Phase 3 — Voice calls (ElevenLabs) | [`human/01-plan.md`](./human/01-plan.md#phase-3) | [`agent/08-phase3-voice-calls.md`](./agent/08-phase3-voice-calls.md) | Sahil | 2026-05-09 |
| Status / progress | [`human/03-status.md`](./human/03-status.md) | [`agent/09-tasks.md`](./agent/09-tasks.md) | All | 2026-05-09 |
| Risks & fallbacks | [`human/04-risks.md`](./human/04-risks.md) | [`agent/02-conventions.md`](./agent/02-conventions.md#fallback-rules) | All | 2026-05-09 |

## Update rules

1. **Source of truth lives in `agent/` for anything an AI will implement** (schemas, endpoints, env vars, file paths). The human doc summarizes it.
2. **Source of truth lives in `human/` for decisions, ownership, status, and rationale.** The agent doc only records the resolved decision.
3. When you ship a change, do **both** edits in the same commit. Commit message format: `docs: <topic> — <one-line change>`.
4. If the two ever drift, the side that disagrees with shipped code is wrong. Reconcile immediately.

## File tree

```
docs/
├── SYNC.md                      ← you are here
├── human/
│   ├── README.md
│   ├── 01-plan.md               ← 20-hour plan, ownership, hour-by-hour
│   ├── 02-tech-decisions.md     ← stack rationale, map choice
│   ├── 03-status.md             ← live checklist
│   └── 04-risks.md              ← what can break, fallbacks
└── agent/
    ├── README.md
    ├── 01-architecture.md
    ├── 02-conventions.md        ← code style, commits, env, fallback rules
    ├── 03-api-contracts.md
    ├── 04-frontend-spec.md
    ├── 05-backend-spec.md
    ├── 06-phase1-fridge-vision.md
    ├── 07-phase2-pantry-locator.md
    ├── 08-phase3-voice-calls.md
    └── 09-tasks.md              ← per-person, per-hour task list
```
