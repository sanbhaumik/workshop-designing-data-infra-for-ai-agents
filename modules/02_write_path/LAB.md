# Module 02 — Write Problems

The agent charges a client's advisory fee through a payment gateway. Agents retry,
so the charge can fire twice, and it must reach the card exactly once. You edit
only `your_fix.py` (`charge_client_fee` and `charge_key`), and meet two traps.

There are **two** tests: a replayed retry (same memo) and a regenerated retry
(the model rewrote the memo). A fix that passes the first can still fail the
second — that gap is the lesson.

1. Watch the "obvious" table-key fix double-charge the client: the `charges` table
   dedupes to ONE row, but the gateway charged the card TWICE ($5,000).
   ```bash
   python modules/02_write_path/naive.py
   ```
2. See the single clean row in the real database:
   ```bash
   psql "$DATABASE_URL" -c "SELECT client_id, amount FROM charges;"
   ```
   The constraint protected your records, not the card. **Aha #1:** guard the
   effect *before* it fires, not the row after.
3. Open `your_fix.py`. Move the guard ahead of the charge: check
   `store.already_charged(key)` before `gateway.charge(...)`. Run the tests:
   ```bash
   pytest modules/02_write_path/test_write.py
   ```
   If `charge_key` is keyed on the memo, the replayed retry passes but the
   regenerated retry **fails** — the model rewrote the memo, so the "same" fee
   got two keys. **Aha #2:** key on the fee's intent (client + period), not the
   agent's output.
4. Fix `charge_key` to key on intent, and run the tests again until both are
   green (2 passed, plus the sanity test).
5. See the full before/after — both retry kinds, side by side:
   ```bash
   python modules/02_write_path/compare.py
   ```
