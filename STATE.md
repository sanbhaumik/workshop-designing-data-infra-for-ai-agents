# NovaBridge Workshop — Current State

A living snapshot of the workshop's intent and build status. Companion to
`CLAUDE.md` (repo guardrails) and `CLAUDE-CODE-build-brief.md` (original spec).

## What it is
A **4-hour, live, online, hands-on workshop**: *Designing Data Infrastructure
for AI Agents & LLMs.* Participants run a real (small) agent against a real
database, watch it fail in two production-grade ways, and fix it. Delivered in a
"Philosophical Pragmatist" (Barry O'Reilly-style) voice: paradox →
deconstruction → historical detour → grounded metaphor → mindset shift.

**Thesis (the spine):** An AI agent is a *non-deterministic, concurrent,
retrying, crash-prone producer of side effects.* Your data infrastructure was
built for none of that. The goal is not **correctness** — it is **criticality**:
designing for resilience to conditions you cannot enumerate.

**Honest promise:** "You'll diagnose two production-grade data failures, choose
and test safe boundaries for writes and state, and read the traces to
reconstruct an agent's actions."

**Deliberately out of scope (and named as such):** retrieval/RAG and evaluation
— "everyone teaches those; we teach what breaks when the agent acts."

## Who it's for
Senior technical audience: **developers, data engineers, data architects**
building agent/LLM systems. Design principle: labs are technically small
(~20 lines) but cognitively demanding — the value is the **design decision**,
not the code. It must feel senior, not like a beginner kata.

## The four invariants (the mental model participants leave with)
Each failure = a condition an agent creates + the invariant it demands:
1. **Idempotency** — "it runs twice" (retry)
2. **Isolation** — "two customers at once"
3. **Recovery / durability** — "it crashes halfway"
4. **Provenance** — "something went wrong; can you reconstruct why?"

## Structure & what's covered

| Block | Time | Content |
|---|---|---|
| Opening | 0:00–0:20 | Paradox, the criticality reframe, the four invariants, readiness check |
| **Lab 1 — Write Path** | 0:20–1:10 | Agent bills a client's $2,500 fee; a retry double-charges the card. Aha: a UNIQUE constraint protects your DB records, not the customer's card — the money moved before the record. Fix: enforce "once" at the effect boundary, keyed on intent. Detour: Two Generals Problem. |
| Break | 1:10–1:20 | — |
| **Lab 2 — State/Memory/Recovery** | 1:20–2:10 | Shared memory leaks Tenant Alpha's summary showing Beta's $1.1M balance. Then the false-confidence trap: run-ID isolation passes, but crash-and-resume restores the wrong state. Fix: define the unit of work + recovery boundary. Detour: Ship of Theseus. |
| Provenance | 2:10–2:55 | Facilitator demo: reconstruct the incident from a trace; the database alone can't say why. |
| Capstone | 2:55–3:40 | Group exercise: score an unfamiliar architecture against the four invariants (author-owned seeded-flaw design). |
| Close | 3:40–4:00 | Recap, mindset shift, Q&A. |

**Teaching loop per lab:** present → predict → run the lab → connect. The lab is
an *instrument* that tests a hypothesis the slides set up; the aha comes from the
gap between the participant's prediction and reality.

## Value delivered
Participants leave able to (a) recognize these failure modes in their own
systems, (b) articulate the design decision (idempotency boundary, unit of work,
recovery/ownership, provenance), and (c) defend the trade-off. They get a
reusable **four-invariant scorecard** for their own architectures.

## Current build state (what's actually real in the repo)
- **Engine (`nova/`):** real hand-rolled agent loop; `PaymentGateway` + `charges`
  table (Lab 1); `summaries` table + memory-isolation model (Lab 2); deterministic
  cooperative scheduler; tracer.
- **Two LLM backends (`NOVA_LLM`):** real **Ollama** (`llama3.2:1b`) for
  labs/demos; **FrozenLLM** (recorded-real outputs) for the deterministic tests.
- **Two DB backends (`DATABASE_URL`):** real **Postgres** for labs; **SQLite**
  for tests.
- **Delivery model:** participants run the **frozen (recorded-real) path** for
  reliability (no model install); facilitator/opt-in runs the live model.
- **One codebase, one `setup.sh`;** thin Colab notebooks + `.devcontainer` call
  it. Verified end-to-end in a Colab-matching Debian container (setup +
  preflight + both labs + SQL all green). Pushed to GitHub; runs in Colab.
- **Tests:** 10 pass / 4 intentional fail-naive (2 per lab); all pass with
  `_reference/` fixes. State cross-tenant leak still fires 20/20.

## Key open item
The **"adversarial design investigation" upgrade** — make each lab a real design
decision with a hidden false-confidence test — is **built**. Both labs now ship
naive and walk through an obvious fix that passes a visible test but fails a
hidden one:
- **Lab 1:** naive charges every time → the "table-key" fix dedupes the row but
  double-charges the card (lived, effect-boundary aha) → guarding the effect but
  keying on the *memo* passes a replayed retry, fails a regenerated one (hidden,
  non-deterministic-id aha) → key on intent (client + period). Participant edits
  `charge_client_fee` + `charge_key`.
- **Lab 2:** the participant edits one function, `state_key(run_id, tenant)`.
  Constant key → live leak; `run_id` → passes live isolation but a crash + reused
  attempt id + resume restores another tenant's checkpoint (hidden recovery test);
  `tenant` (the unit of work) → both pass. Engine gained `MemoryStore` +
  `save_from_checkpoint`.

## Strategic through-line of the design so far
The labs were repeatedly moved *up* in seniority: from "add a UNIQUE constraint"
(too basic) → effect-boundary idempotency and multi-tenant memory isolation →
"criticality over correctness" as the framing that justifies the title. Standing
risk to watch: each lab must demand genuine design judgment, and the workshop
must earn the "data infrastructure" title honestly.

## Also authored this session (not yet in repo as final)
- A full slide-by-slide content outline (~50 slides) for the 4-hour flow, for
  handoff to a design tool. Lives in the conversation; not committed as authored
  teaching content per the `CLAUDE.md` boundary.
