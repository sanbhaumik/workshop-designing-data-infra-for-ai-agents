# Module 03 — State, Memory & Recovery

Two agent runs serve two different tenants while sharing one mutable memory
object. Tenant Beta's run overwrites the shared memory, and tenant Alpha's run
then saves an account summary built from Beta's data — a cross-tenant leak,
written to a real database. Alpha's summary shows Beta's balance.

1. Run the naive path and watch the leak happen step by step:
   ```bash
   python modules/03_state/naive_state.py
   ```
2. Read the interleaved-steps table. Find the row where run-a (serves Alpha)
   saves while `memory.tenant` is already `beta`. That's the leak.
3. See the leaked row in the real database:
   ```bash
   psql "$DATABASE_URL" -c "SELECT client_id, content FROM summaries;"
   ```
4. Open `modules/03_state/your_fix.py`. Fix `IsolatedState` so `get`/`set`
   namespace memory by `run_id` (each run gets its own dict). Edit only this
   file.
5. Run the test:
   ```bash
   pytest modules/03_state/test_state.py
   ```
6. Iterate until it's green (1 passed).
7. See the before/after:
   ```bash
   python modules/03_state/compare.py
   ```
   Alpha's summary goes from "contains Beta" to clean.
