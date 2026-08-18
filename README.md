# nova-agent-infra

Python engine and lab harness for the 4-hour workshop *Designing Data
Infrastructure for AI Agents*.

## What this is

Every course on data for LLMs teaches retrieval: vector stores, chunking,
RAG. Almost none teach what happens when the agent **writes** — and that is
where production data silently corrupts.

This workshop owns the neglected, high-severity failures. An AI agent is a
**non-deterministic, concurrent, retrying, crash-prone producer of side
effects.** A data layer built for ordinary callers does not survive that. So
this workshop teaches the four invariants a data layer for agents actually
needs, through failures you watch happen against a real local model and a
real database:

- **Identity** — derive it from the agent's intent, not its variable output
  (Lab 1, Write Problems).
- **Isolation** — namespace state per run/tenant; no shared mutable context
  (Lab 2, State, Memory & Recovery).
- **Idempotency / durability** — safe retries, exactly-once effects,
  crash recovery (Labs 1 and 2).
- **Provenance** — reconstruct what an agent read and wrote, after the fact
  (Provenance demo).

Deliberately out of scope: retrieval/RAG (covered everywhere else) and
evaluation (a separate body of work). This is the write path and the state
layer — the parts that fail quietly and cost the most.

## Run it

**Use GitHub Codespaces if you have a GitHub account. Use Colab only if
something blocks Codespaces.**

### Codespaces (primary)

1. Click **Code → Codespaces → Create codespace on main** on this repo.
   *(AUTHOR TODO: add the "Open in Codespaces" badge once this repo has a
   GitHub remote.)*
2. Wait for the container to build — it installs `requirements.txt`
   automatically.
3. Run `python preflight.py` in the terminal. You should see a green
   **GREEN** banner.

### Colab (fallback)

Open in Colab:

- `colab/00_preflight.ipynb`
- `colab/02_write_path.ipynb`
- `colab/03_state.ipynb`

*(AUTHOR TODO: add Colab badges/links once this repo has a GitHub remote.
Until then, set `REPO_URL` in each notebook's first cell.)*

Each notebook clones this repo and installs dependencies in its first cell,
then runs the relevant script and test.

## Labs

Two hands-on labs:

| Module | Lab guide | Step-by-step instructions |
|---|---|---|
| 02 — Write Problems | `modules/02_write_path/LAB.md` | `instructions/02_write_path.md` |
| 03 — State, Memory & Recovery | `modules/03_state/LAB.md` | `instructions/03_state.md` |

Module 04 (Provenance) is a facilitator demo — see
`modules/04_provenance/LAB.md` and `instructions/04_provenance.md`. Modules
01 and 05 are authored content, stubbed here.

## Commands

```bash
python preflight.py                         # environment self-check
pytest                                       # engine + both lab tests
python modules/02_write_path/naive.py        # show the write-conflict corruption
python modules/03_state/naive_state.py       # show the wrong-client briefing
python scripts/generate_trace.py             # regenerate fixtures/traces/incident_047.json
python modules/04_provenance/walk_trace.py   # facilitator forensic viewer
```

## Real stack, two ways to run

The labs run a real agent against a **real Postgres database**. The model is a
**real local open-source model** (Ollama, `llama3.2:1b`).

- **Participants / default** (`NOVA_LLM=frozen`): the model's answers are
  replayed from real recordings captured once from that same model. Real agent,
  real code, real database, real fixes — 100% reproducible, no slow model
  install. See `SETUP.md`.
- **Facilitator / opt-in** (`NOVA_LLM=ollama`): the live model, generating fresh
  each run.

The test suite always uses the recordings (`NOVA_LLM=frozen`) + SQLite, so it is
deterministic and offline.

Fixtures under `fixtures/clients/` are synthetic sample documents, marked
`SAMPLE / FICTIONAL`. `fixtures/llm_responses/` holds real recorded model
outputs. Swap in your own client documents and re-record to customize.
