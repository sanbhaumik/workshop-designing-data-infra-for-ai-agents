# Module 02 — Write Problems: participant instructions

## What you'll learn

An AI agent is a **non-deterministic producer of irreversible side effects**.
It charges a client's advisory fee; agents retry, so the charge can fire twice.
The instinctive fix — a `UNIQUE` constraint on your table — makes the *record*
idempotent but does **not** un-charge the card: the payment gateway is the
outside world, and the money already moved. Idempotency has to be enforced
**before** the effect, keyed on the agent's stable intent (client + period), not
on the model's output, which changes every run.

The Colab notebook (`colab/02_write_path.ipynb`) walks this inline: you call the
agent yourself, watch it double-charge, see your DB stay clean while the gateway
charges twice, then guard the effect and watch the retry skip.

## Steps (terminal)

1. Run the agent and its retry:
   ```bash
   python modules/02_write_path/naive.py
   ```
2. Read the two tables: your `charges` table has **one** row, the payment
   gateway charged the client **twice** ($5,000). Your constraint protected your
   records, not the card.
3. Confirm the single clean row in the real database:
   ```bash
   psql "$DATABASE_URL" -c "SELECT client_id, amount FROM charges;"
   ```
4. Open `modules/02_write_path/your_fix.py` and edit `charge_client_fee`: before
   `gateway.charge(...)`, check `store.already_charged(key)` and `return` if the
   fee was already charged.
5. Run the test:
   ```bash
   pytest modules/02_write_path/test_write.py -v
   ```
6. Done when both tests show `2 passed`. Then run the before/after:
   ```bash
   python modules/02_write_path/compare.py
   ```

## Files

| File | Edit? |
|---|---|
| `modules/02_write_path/your_fix.py` | Yes — the one function `charge_client_fee` |
| `modules/02_write_path/naive.py` | No (read it — it shows how the agent runs) |
| `modules/02_write_path/compare.py` | No (the before/after reveal) |
| `modules/02_write_path/test_write.py` | No |
| `nova/*.py` | No |

## Think about it

- Why does a `UNIQUE` constraint on the `charges` table not prevent the double
  charge?
- The guard is keyed on `(client, period)`. Where does that key come from in a
  real system, and what would you do if the same fee could legitimately be
  charged twice (e.g. a genuine re-bill)?

## Troubleshooting

- `pytest` not found → re-run `python preflight.py`; if it's not GREEN,
  dependencies didn't install correctly.
- Test still fails → make sure you `return` **before** `gateway.charge(...)`,
  not after.
