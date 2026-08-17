# Module 02 — Write Problems: participant instructions

## What you'll learn

An AI agent is a **non-deterministic producer**: run it twice on the same input
and it produces differently-worded output. When each run triggers an
**irreversible side effect** — here, filing an obligation with a regulator —
naive deduplication fails, because the two outputs don't match byte-for-byte. A
database `UNIQUE` constraint on the text can't save you. The fix is to derive
your idempotency identity from the agent's **intent** (its inputs), not its
output, and enforce it at the side-effect boundary.

## Prerequisites

- Environment ready: `python preflight.py` prints a green **GREEN**.
- Codespaces: open a terminal in your codespace.
- Colab: open `colab/02_write_path.ipynb`, run the first cell, then follow along
  with the notebook's code cells in place of a terminal.

## Steps

1. Run the agent twice:
   ```bash
   python modules/02_write_path/naive.py
   ```
2. Read the output carefully:
   - Each **run** shows four steps: RETRIEVE → REASON → IDENTITY → FILE.
   - The **REASON** step produces *different text* on run #1 vs run #2 — the
     same obligation, worded two ways.
   - The regulator table at the bottom shows **two filings** for one obligation.
3. Open `modules/02_write_path/your_fix.py`. Edit the one function,
   `obligation_identity`. It currently keys on `obligation_text` (which changes
   every run). Change it to key on the agent's stable intent — the inputs
   `client_id` and `source_doc`.
4. Run the test:
   ```bash
   pytest modules/02_write_path/test_write.py -v
   ```
5. There are two tests:
   - `test_two_runs_really_produce_different_text` — passes from the start; it
     proves the two runs genuinely diverge (otherwise the lab would be trivial).
   - `test_retry_files_obligation_only_once` — this is the one you're fixing.
6. Done when both show `2 passed`.
7. See it land. Run the before/after reveal:
   ```bash
   python modules/02_write_path/compare.py
   ```
   You'll see two tables. **BEFORE** (naive identity) — two different keys, both
   `FILED`. **AFTER** (your fix) — the *same* key on both runs, so the second is
   `SKIPPED`. Same non-deterministic model; deterministic identity.

## Files

| File | Edit? |
|---|---|
| `modules/02_write_path/your_fix.py` | Yes — the one function `obligation_identity` |
| `modules/02_write_path/naive.py` | No (read it — it shows how the agent runs) |
| `modules/02_write_path/compare.py` | No (the before/after reveal) |
| `modules/02_write_path/test_write.py` | No |
| `nova/*.py` | No |

## Think about it

- Why would a `UNIQUE` constraint on the obligation text *not* have prevented
  the double filing?
- Your fix keys on `(client_id, source_doc)`. In a real system where one
  document yields several obligations, what would you add to the key to keep
  each obligation distinct — and why is that harder than it sounds?

## Troubleshooting

- `pytest` not found → re-run `python preflight.py`; if it's not GREEN,
  dependencies didn't install correctly.
- Test still fails → make sure your key does **not** depend on `obligation_text`
  in any way.
