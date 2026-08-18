# Module 03 — State, Memory & Recovery

Two agent runs serve two different tenants while sharing one mutable memory
object. Tenant Beta's run overwrites the shared memory, and tenant Alpha's run
then drafts its briefing from Beta's data: a cross-tenant leak, written to a
real database.

1. Run the naive path and watch the leak happen step by step:
   ```bash
   python modules/03_state/naive_state.py
   ```
2. Read the interleaved-steps table. Find the rows where run-a (serves Alpha)
   acts while `memory.tenant` is already `beta`. That is the leak. Alpha's
   final briefing contains Beta's obligation.
3. See the leaked row in the real database:
   ```bash
   psql "$DATABASE_URL" -c "SELECT client_id, content FROM briefings;"
   ```
4. Open `modules/03_state/your_fix.py`. Two tasks:
   - Fix `IsolatedState` so memory is namespaced by `run_id` (per run/tenant).
   - Fix `run_recoverable` so a resumed run doesn't redo (and duplicate) work
     that already completed before a simulated kill.
   Edit only this file.
5. Run the test:
   ```bash
   pytest modules/03_state/test_state.py
   ```
6. Iterate until it's green (2 passed).
7. See both fixes land — run the before/after reveal:
   ```bash
   python modules/03_state/compare.py
   ```
   Isolation goes from "contains Beta" to clean; recovery goes from 2 to 1.
