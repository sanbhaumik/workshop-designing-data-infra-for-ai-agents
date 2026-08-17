# Module 02 — Write Problems

The agent files a regulatory obligation with an external regulator — an
irreversible side effect. Two runs of a non-deterministic agent produce
differently-worded obligations for the same commitment, and the naive identity
guard files both.

1. Run the agent twice and watch it file the same obligation twice:
   ```bash
   python modules/02_write_path/naive.py
   ```
2. Read the two agent runs. Note that the REASON step produces different text
   each run, and the regulator receives two filings.
3. Open `modules/02_write_path/your_fix.py`. Edit `obligation_identity` — and
   only this file. Derive the key from the agent's stable intent
   (`client_id`, `source_doc`), not from the variable `obligation_text`.
4. Run the test:
   ```bash
   pytest modules/02_write_path/test_write.py
   ```
5. Iterate until it's green (2 passed).
6. See your fix land — run the before/after reveal:
   ```bash
   python modules/02_write_path/compare.py
   ```
   The BEFORE table (naive identity) shows two filings; the AFTER table (your
   fix) shows the second run SKIPPED, with the same idempotency key on both.
