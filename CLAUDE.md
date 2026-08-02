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

## Golden rules (never violate)

1. **No network at runtime.** LLM and embeddings come from fixtures. The only outbound-call code lives behind `NOVA_LIVE_LLM=1` and is off by default. Never add another network call.
2. **Determinism is sacred.** Every engineered failure must fire on 100% of runs. No real threads racing, no `time.sleep`, no wall-clock timing, no unseeded randomness. Concurrency is *simulated* via the scripted cooperative `Scheduler`. If you touch anything concurrency-related, re-run the 20× determinism check before calling it done.
3. **Cross-platform, no OS-specific code.** `pathlib` everywhere. No shell-outs, no platform branches. Must behave identically on Codespaces and Colab.
4. **Python 3.11.9, dependencies hard-pinned.** Never bump a version or add a dependency without being asked. New deps must be pinned with `==`.
5. **Transparency over abstraction.** The agent loop and labs are read by learners. Keep modules small, every step visible, nothing important hidden inside a framework or a clever helper. No agent framework (no LangGraph/LangChain).
6. **Legible failures.** Corrupted records and wrong-client briefings are shown via `rich` and must read clearly when screen-shared at 720p.

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

`fixtures/` holds placeholders only. Every placeholder file starts with `PLACEHOLDER — replace with real content` and is listed in the README under "Content to replace." Do not generate realistic financial documents or real recorded model outputs — size placeholders only so tests pass.

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
fixtures/     placeholder LLM responses, embeddings, client docs, traces
colab/        one notebook per hands-on lab + preflight
scripts/      generate_trace.py
preflight.py  environment self-check
```

When a requirement is ambiguous, build the simplest thing that satisfies the acceptance criteria in `CLAUDE-CODE-build-brief.md` and leave an `# AUTHOR TODO`, rather than inventing content.