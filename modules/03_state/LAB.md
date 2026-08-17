# Module 03 — State, Memory & Recovery

1. Run the naive path and watch the contamination happen step by step:
   ```bash
   python modules/03_state/naive_state.py
   ```
2. Read the interleaved-steps table. Find the rows where run-a (owns Alpha)
   acts while `state.client_id` is already `beta` — that's the leak. Alpha's
   final briefing contains Beta's data.
3. Open `modules/03_state/your_fix.py`. There are two tasks in that file:
   - Fix `IsolatedState` so state is namespaced by `run_id`.
   - Fix `run_recoverable` so a resumed run doesn't redo (and duplicate)
     work that already completed before a simulated kill.
   Edit only this file.
4. Run the test:
   ```bash
   pytest modules/03_state/test_state.py
   ```
5. Iterate until it's green (2 passed).
6. See both fixes land — run the before/after reveal:
   ```bash
   python modules/03_state/compare.py
   ```
   The isolation table shows Alpha's briefing going from "contains Beta" to
   clean; the recovery table shows the obligation count going from 2 to 1.
