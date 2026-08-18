# Module 03 — State, Memory & Recovery: participant instructions

## What you'll learn

Two agent runs serve two different **tenants** while sharing one mutable memory
object. Tenant Beta's run overwrites the shared memory, and tenant Alpha's run
then saves an account summary built from Beta's data — so **Alpha's summary
shows Beta's balance**. This is the cross-tenant leak that bites real
multi-tenant agent systems: it happens inside the agent's shared memory, before
any per-request check runs. The fix is to namespace working memory per run.

The Colab notebook (`colab/03_state.ipynb`) walks this inline: you run the two
tenants yourself, watch the shared memory get overwritten, and watch Alpha save
Beta's data — then isolate memory and watch the leak disappear.

## Steps (terminal)

1. Run the naive path and watch the leak happen step by step:
   ```bash
   python modules/03_state/naive_state.py
   ```
2. Read the **interleaved steps** table. Watch the `memory.tenant` column: at the
   red row, run-a (which serves Alpha) saves while the shared memory already
   says `beta`. Alpha's summary ends up containing Beta's balance.
3. See the leaked row in the real database:
   ```bash
   psql "$DATABASE_URL" -c "SELECT client_id, content FROM summaries;"
   ```
4. Open `modules/03_state/your_fix.py` and fix `IsolatedState` so `get`/`set`
   give each `run_id` its own dict.
5. Run the test:
   ```bash
   pytest modules/03_state/test_state.py -v
   ```
6. Done when it shows `1 passed`. Then run the before/after:
   ```bash
   python modules/03_state/compare.py
   ```

## Files

| File | Edit? |
|---|---|
| `modules/03_state/your_fix.py` | Yes — fix `IsolatedState` |
| `modules/03_state/naive_state.py` | No (read it — it shows the interleaving) |
| `modules/03_state/compare.py` | No (the before/after reveal) |
| `modules/03_state/test_state.py` | No |
| `nova/*.py` | No |

## Think about it

- The leak happens inside the agent's memory, before any auth or tenant check on
  the request. Where else does shared state hide in an agent system (a module
  global, a cached client, a shared vector store), and how would you isolate it?

## Troubleshooting

- `pytest` not found → re-run `python preflight.py`; if it's not GREEN,
  dependencies didn't install correctly.
