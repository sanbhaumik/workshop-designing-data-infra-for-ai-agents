# Module 03 — State, Memory & Recovery: participant instructions

## Prerequisites

- Environment ready: `python preflight.py` prints a green **GREEN**.
- Codespaces: open a terminal in your codespace.
- Colab: open `colab/03_state.ipynb` and run the first cell (clones the
  repo, installs dependencies), then follow along using the notebook's code
  cells in place of a terminal.

## What you'll learn

Two agent runs serve two different **tenants** while sharing one mutable memory
object. Tenant Beta's run overwrites the shared memory, and tenant Alpha's run
then drafts its briefing from Beta's data — a **cross-tenant data leak**, the
kind that shows up in a multi-tenant agent system when memory or retrieved
context isn't isolated. The fix is to namespace memory per run/tenant. The
second task adds **recovery**: a crashed run must resume from a checkpoint
instead of redoing (and duplicating) work it already completed.

## Steps

1. Run the naive path and watch the leak happen step by step:
   ```bash
   python modules/03_state/naive_state.py
   ```
2. Read the **interleaved steps** table. Each row is one agent action. Watch the
   `memory.tenant` column: at steps flagged in red, run-a (which serves Alpha)
   is acting while the shared memory already says `beta`. That's the leak — and
   Alpha's final briefing ends up containing Beta's obligation.
3. See the leaked row in the real database:
   ```bash
   psql "$DATABASE_URL" -c "SELECT client_id, content FROM briefings;"
   ```
3. Open `modules/03_state/your_fix.py`. There are two tasks in this file:
   - **Task 1:** fix `IsolatedState.get` / `IsolatedState.set` so state is
     namespaced by `run_id`.
   - **Task 2:** fix `run_recoverable` so a resumed run does not redo work
     that already completed before a simulated kill.
4. Edit only this file.
5. Run the test:
   ```bash
   pytest modules/03_state/test_state.py -v
   ```
6. There are two tests — `test_isolation_alpha_briefing_has_no_beta_data`
   (Task 1) and `test_recovery_no_duplicate_after_kill` (Task 2). Both must
   pass.
7. If either fails, go back to step 3/4 and adjust the corresponding class
   or function.
8. Done when the test output shows `2 passed`.
9. See both fixes land. Run the before/after reveal:
   ```bash
   python modules/03_state/compare.py
   ```
   Two tables. **Isolation** — Alpha's briefing goes from "contains Beta" to
   clean. **Recovery** — after a crash and resume, the obligation count goes
   from 2 (duplicated) to 1. If you've only fixed one task, the reveal tells you
   which one is still outstanding.

## Files

| File | Edit? |
|---|---|
| `modules/03_state/your_fix.py` | Yes — this is the whole lab |
| `modules/03_state/naive_state.py` | No (read it — it shows the interleaving) |
| `modules/03_state/compare.py` | No (the before/after reveal) |
| `modules/03_state/test_state.py` | No |
| `nova/*.py` | No |

## Troubleshooting

- `pytest` not found → re-run `python preflight.py`; if that's not GREEN,
  dependencies didn't install correctly.
- Only the isolation test fails → check `IsolatedState`, leave
  `run_recoverable` alone.
- Only the recovery test fails → check `run_recoverable`, leave
  `IsolatedState` alone.
