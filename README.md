# nova-agent-infra

Python engine and lab harness for the 4-hour workshop *Designing Data
Infrastructure for AI Agents*.

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

## Content to replace

Everything under `fixtures/` is a placeholder, not real content. Each file
starts with `PLACEHOLDER — replace with real content`.

- `fixtures/clients/alpha/*.md`, `fixtures/clients/beta/*.md` — placeholder
  client documents.
- `fixtures/llm_responses/*.json` — placeholder frozen LLM responses.
- `fixtures/embeddings/*.npy` — placeholder frozen embedding vectors.

## No network at runtime

The workshop never calls a real LLM or embeddings API. `nova/frozen_llm.py`
and `nova/embeddings.py` serve pre-recorded fixtures looked up by content
hash. An optional live-recording path exists to regenerate fixtures but is
gated behind `NOVA_LIVE_LLM=1` and is never used during the workshop.
