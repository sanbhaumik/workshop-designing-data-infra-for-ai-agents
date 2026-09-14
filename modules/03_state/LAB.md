# Module 03 — State, Memory & Recovery

The agent keeps working memory in a shared `MemoryStore`, addressed by whatever
key `state_key(run_id, tenant)` returns. The shipped version returns the same key
for every run, so two tenants' runs share one slot and one leaks into the other.
You change only `state_key` in `your_fix.py`.

There are **two** tests. The first is a live leak; the second is a crash-and-resume.
A fix that passes the first can still fail the second — that gap is the lesson.

1. Watch the live leak happen step by step:
   ```bash
   python modules/03_state/naive_state.py
   ```
2. See the leaked row in the real database:
   ```bash
   psql "$DATABASE_URL" -c "SELECT client_id, content FROM summaries;"
   ```
3. Open `modules/03_state/your_fix.py`. Try the obvious fix first: give each run
   its own slot by returning `run_id`.
4. Run the tests:
   ```bash
   pytest modules/03_state/test_state.py
   ```
   The live-isolation test passes — but the recovery test **fails**. A run crashed,
   another tenant reused its attempt id, and the resumed run loaded the wrong
   tenant's checkpoint. `run_id` is an ephemeral attempt id, not identity.
5. Fix `state_key` to key on the **unit of work** (the tenant), which survives a
   crash and resume. Run the tests again until both are green (2 passed).
6. See the full before/after — live and recovery, side by side:
   ```bash
   python modules/03_state/compare.py
   ```
