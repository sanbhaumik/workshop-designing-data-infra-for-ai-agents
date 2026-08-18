# CLAUDE.md — nova-agent-infra

Standing context for this repo. Read on every session. These rules hold regardless of the task in front of you.

## What this is

The Python engine and lab harness for a **4-hour live online workshop**, *Designing Data Infrastructure for AI Agents*. Participants run it in **GitHub Codespaces** (primary) or **Google Colab** (fallback), on Windows or Mac browsers. The code is teaching material — clarity is a feature, not a nicety.

Full task spec: `CLAUDE-CODE-build-brief.md`. This file is the always-on guardrail.

## The 4-hour shape (what has code and what doesn't)

Six agenda blocks. Only two are hands-on labs.

| Block | Has participant code? |
|---|---|
| Opening / readiness review | No — authored content, stub folder |
| **Write Problems** | **Yes — hands-on lab** |
| **State, Memory & Recovery** | **Yes — hands-on lab** |
| Provenance | No — facilitator demo; build the tracer + viewer only |
| Capstone architecture review | No — authored content, stub folder |
| Close / buffer | No |

There are **exactly two labs** (Write, State). Never add a third. Provenance is a demo (build `Tracer`, `generate_trace.py`, `walk_trace.py` — no `your_fix.py`, no test). The opening and capstone are authored by a human — stub their folders with `# AUTHOR TODO`.

## Architecture (revised — real agent, real DB, local & offline)

This workshop uses a **real agent against a real local open-source LLM and a real Postgres database.** This deliberately revises the original "frozen fixtures / no network" design. Read this section carefully — future sessions must not "restore" the fixture-only approach.

- **Two LLM backends, chosen by `NOVA_LLM`.** Lab *runners and demos* use `OllamaLLM` (a real local model, default `llama3.2:1b`, via `nova/ollama_llm.py`). The *pytest suite* uses `FrozenLLM` (`NOVA_LLM=frozen`) so the fail-naive / pass-reference contract stays deterministic and offline. Never make the test suite depend on Ollama.
- **Local, not networked.** Ollama runs on `localhost`; there are no external API calls and no API keys. A local model is a real LLM that preserves the offline property. Do not add a hosted/cloud LLM call.
- **Two store backends, chosen by `DATABASE_URL`.** Labs run against **Postgres** (`nova` DB, via `psycopg`); the test suite runs against **SQLite** (fast, offline, deterministic). Both implement the same store interface. Participant `your_fix.py` never writes raw SQL, so it is portable across both.
- **One codebase, thin per-client launchers.** The engine is environment-agnostic and configured entirely by env vars (`NOVA_LLM`, `DATABASE_URL`, `OLLAMA_HOST`, `OLLAMA_MODEL`). A single `setup.sh` provisions Postgres + Ollama + the model + deps. Colab notebooks and the `.devcontainer` are thin launchers that both call `setup.sh`. Never fork the core code per environment.

## Golden rules (never violate)

1. **Determinism where it's tested.** The pytest suite must fire each engineered failure 100% of runs, offline, on SQLite + FrozenLLM. Concurrency is *simulated* via the scripted cooperative `Scheduler` — no real threads, no `time.sleep`, no wall-clock timing, no unseeded randomness. Live lab runs may use the real (non-deterministic) model — that non-determinism is the point of the Write lab — but the tests never depend on it. Re-run the 20× determinism check after touching concurrency.
2. **Cross-platform, no OS-specific code in the engine.** `pathlib` everywhere; keep OS specifics inside `setup.sh`. The engine must behave identically on a laptop, Codespaces, and Colab.
3. **Dependencies hard-pinned.** Python 3.11.x. Never bump a version or add a dependency without being asked. New deps pinned with `==` (`psycopg[binary]` is the one added for Postgres).
4. **Transparency over abstraction.** The agent loop and labs are read by learners. Keep modules small, every step visible, nothing important hidden inside a framework or a clever helper. No agent framework (no LangGraph/LangChain), and no ORM — hand-rolled SQL per backend.
5. **Legible failures.** Corrupted records and wrong-client briefings are shown via `rich` and must read clearly when screen-shared at 720p. Participants can also see them directly in Postgres via SQL.

## IP fence (hard stop)

Never write, implement, or reference the **Evaluation Graph**, **Reverse Strategy Framework**, or **Three Debts** anywhere in this repo. Never author conceptual provenance, evaluation, or governance *teaching* content — build only the mechanical `Tracer` and trace tooling. If a task seems to require any of the above, stop and leave a `# AUTHOR TODO` comment instead. This material is reserved for a separate book; keeping it out of this repo is a firm requirement.

## Out of scope for code

Do not build slides, Canva/Excalidraw diagrams, talk tracks, teaching narration, decision-prompt wording, the opening architecture-review content, the capstone architecture/flaw key, or realistic fixture *content*. `LAB.md` files stay mechanical (run this, observe, fix, test). When these come up, leave an `# AUTHOR TODO` marker — they are authored by a human, elsewhere.

## Commands

```bash
python preflight.py                        # environment self-check → GREEN/RED
pytest                                     # engine + both lab tests
python modules/02_write_path/naive.py      # show the write-conflict corruption
python modules/03_state/naive_state.py     # show the wrong-client briefing
python scripts/generate_trace.py           # regenerate fixtures/traces/incident_047.json
python modules/04_provenance/walk_trace.py # facilitator forensic viewer
```

## Testing contract

- Lab tests must **fail** with the shipped naive `your_fix.py` and **pass** with the matching `_reference/` solution. Preserve both directions when editing tests.
- `_reference/` holds correct solutions used only to validate tests. Never ship it to participants and never merge it into a `your_fix.py`.
- Determinism check: naive paths must fail 20/20 runs. Treat a flaky failure as a scheduler bug, not a test to loosen.
- `preflight.py` must print GREEN on a fresh Codespace and on Colab.
- Provenance and capstone have no tests — they are a demo and an authored exercise.

## Fixtures

`fixtures/llm_responses/` holds **real model outputs recorded once** from the local Ollama model (keyed by prompt hash). This is deliberate: the participant/default path runs `NOVA_LLM=frozen`, replaying these recordings so the labs are real-feeling and 100% reproducible without a live model. To re-record after a prompt change, run the recorder against a running Ollama (see the record step in git history) or set `NOVA_LLM=ollama` and regenerate. Client docs under `fixtures/clients/` are synthetic sample content, clearly marked `SAMPLE / FICTIONAL`. Keep recorded Lab-1 outputs divergent (two different wordings) and Lab-3 Alpha output free of the word "beta", or the deterministic tests break.

## Conventions

- Type hints and a one-line docstring on every public function.
- Small, single-purpose modules. Prefer readable over short.
- Seed all randomness explicitly.
- Participants edit only `your_fix.py` in each lab — never require edits to `nova/` or `store.py` to complete a lab.

## Repo map

```
nova/         engine (models, store, frozen_llm, embeddings, agent, scheduler, trace)
modules/      01_opening (stub) · 02_write_path (lab) · 03_state (lab)
              04_provenance (demo tooling) · 05_capstone (stub)
_reference/   correct solutions — never shipped
fixtures/     recorded LLM responses, embeddings, sample client docs, traces
colab/        one notebook per hands-on lab + preflight
scripts/      generate_trace.py
preflight.py  environment self-check
```

When a requirement is ambiguous, build the simplest thing that satisfies the acceptance criteria in `CLAUDE-CODE-build-brief.md` and leave an `# AUTHOR TODO`, rather than inventing content.