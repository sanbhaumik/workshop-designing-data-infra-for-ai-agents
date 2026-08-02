# Module 03 — State, Memory & Recovery: participant instructions

## Prerequisites

- Environment ready: `python preflight.py` prints a green **GREEN**.
- Codespaces: open a terminal in your codespace.
- Colab: open `colab/03_state.ipynb` and run the first cell (clones the
  repo, installs dependencies), then follow along using the notebook's code
  cells in place of a terminal.

## Steps

1. Run the naive path:
   ```bash
   python modules/03_state/naive_state.py
   ```
2. Read the printed output: Alpha's briefing and Beta's briefing. Note what
   Alpha's briefing contains.
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

## Files

| File | Edit? |
|---|---|
| `modules/03_state/your_fix.py` | Yes — this is the whole lab |
| `modules/03_state/naive_state.py` | No |
| `modules/03_state/test_state.py` | No |
| `nova/*.py` | No |

## Troubleshooting

- `pytest` not found → re-run `python preflight.py`; if that's not GREEN,
  dependencies didn't install correctly.
- Only the isolation test fails → check `IsolatedState`, leave
  `run_recoverable` alone.
- Only the recovery test fails → check `run_recoverable`, leave
  `IsolatedState` alone.
