# Module 03 — State, Memory & Recovery

1. Run the naive path and observe the contamination:
   ```bash
   python modules/03_state/naive_state.py
   ```
2. Read the printed briefings. Alpha's briefing contains Beta's data.
3. Open `modules/03_state/your_fix.py`. There are two tasks in that file:
   - Fix `IsolatedState` so state is namespaced by `run_id`.
   - Fix `run_recoverable` so a resumed run doesn't redo (and duplicate)
     work that already completed before a simulated kill.
   Edit only this file.
4. Run the test:
   ```bash
   pytest modules/03_state/test_state.py
   ```
5. Iterate until it's green.
