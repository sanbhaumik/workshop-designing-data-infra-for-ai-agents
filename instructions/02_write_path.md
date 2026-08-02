# Module 02 — Write Problems: participant instructions

## Prerequisites

- Environment ready: `python preflight.py` prints a green **GREEN**.
- Codespaces: open a terminal in your codespace.
- Colab: open `colab/02_write_path.ipynb` and run the first cell (clones the
  repo, installs dependencies), then follow along using the notebook's code
  cells in place of a terminal.

## Steps

1. Run the naive path:
   ```bash
   python modules/02_write_path/naive.py
   ```
2. Read the printed output:
   - The obligations table — note how many rows exist for one true obligation.
   - The final briefing line and its version number.
3. Open `modules/02_write_path/your_fix.py`.
4. Edit the body of `guarded_write(store, ob)`. This is the only function,
   and the only file, you need to change.
5. Run the test:
   ```bash
   pytest modules/02_write_path/test_write.py -v
   ```
6. If it fails, go back to step 4 and adjust `guarded_write`.
7. Done when the test output shows `1 passed`.

## Files

| File | Edit? |
|---|---|
| `modules/02_write_path/your_fix.py` | Yes — this is the whole lab |
| `modules/02_write_path/naive.py` | No |
| `modules/02_write_path/test_write.py` | No |
| `nova/*.py` | No |

## Troubleshooting

- `pytest` not found → re-run `python preflight.py`; if that's not GREEN,
  dependencies didn't install correctly.
- Test still fails after editing → re-run `python modules/02_write_path/naive.py`
  to re-observe the corruption, then re-check `guarded_write`.
