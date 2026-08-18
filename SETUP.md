# Setup — three ways to run the workshop

The workshop runs a real agent against a local open-source model (Ollama) and a
real Postgres database. One codebase, one `setup.sh`. Pick the client that fits
you. All three end in the same place: `python preflight.py` prints **GREEN**.

The environment is configured entirely by env vars:

| Variable | Default | Meaning |
|---|---|---|
| `NOVA_LLM` | `ollama` | `ollama` (real local model) or `frozen` (fixtures, for tests) |
| `DATABASE_URL` | local SQLite | `postgresql://postgres@localhost:5432/nova` for the labs |
| `OLLAMA_MODEL` | `llama3.2:1b` | any pulled Ollama model |
| `OLLAMA_TEMPERATURE` | `0.8` | higher = more divergent runs in the Write lab |

---

## 1. Google Colab (primary, nothing to install)

Open a notebook and run it top to bottom:

- Setup + preflight: `colab/00_preflight.ipynb`
- Lab 1: `colab/02_write_path.ipynb`
- Lab 2: `colab/03_state.ipynb`

Each notebook clones the repo, runs `setup.sh`, sets the env vars, and runs the
lab. The first setup cell takes a few minutes (installs Postgres + Ollama, pulls
the model). If your session disconnects, re-run the cells — setup is idempotent.
Optional: **Runtime → Change runtime type → T4 GPU** for a faster model.

## 2. GitHub Codespaces

Create a codespace on this repo. The devcontainer runs `setup.sh` on create and
sets the env vars. When it finishes, run `python preflight.py`. If a background
service (Postgres or Ollama) isn't up after a restart, re-run `bash setup.sh`.

## 3. Your own laptop (Linux/macOS)

```bash
git clone https://github.com/sanbhaumik/workshop-designing-data-infra-for-ai-agents.git
cd workshop-designing-data-infra-for-ai-agents
python3.11 -m venv .venv && source .venv/bin/activate
bash setup.sh                 # Debian/Ubuntu; on macOS install postgres + ollama via brew
export NOVA_LLM=ollama
export DATABASE_URL="postgresql://postgres@localhost:5432/nova"
python preflight.py
```

On macOS, `setup.sh`'s apt path won't apply — install Postgres and Ollama with
Homebrew (`brew install postgresql@16 ollama`), start them, `ollama pull
llama3.2:1b`, then `pip install -r requirements.txt` and set the same env vars.

---

## Running the deterministic tests (no model, no Postgres)

```bash
python -m pytest -q
```

The test suite forces `NOVA_LLM=frozen` behavior and SQLite, so it needs neither
Ollama nor Postgres. Expect `3 failed, 15 passed` on a fresh checkout — the 3
failures are the two labs' fix-me tests, broken on purpose.
