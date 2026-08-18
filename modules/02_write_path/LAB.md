# Module 02 — Write Problems

The agent charges a client's advisory fee through a payment gateway. Agents
retry, so the charge can fire twice. A unique key on your `charges` table makes
the record idempotent, but it does not un-charge the card. Idempotency has to be
enforced before the irreversible effect.

1. Run the agent (and its retry) and watch it double-charge the client:
   ```bash
   python modules/02_write_path/naive.py
   ```
2. Read the two tables: your `charges` table shows ONE charge, but the payment
   gateway charged the client TWICE ($5,000). The constraint protected your
   records, not the card.
3. See the single clean row in the real database:
   ```bash
   psql "$DATABASE_URL" -c "SELECT client_id, amount FROM charges;"
   ```
4. Open `modules/02_write_path/your_fix.py`. Edit `charge_client_fee`: before
   `gateway.charge(...)`, check `store.already_charged(key)` and return if the
   fee was already charged. The key is derived from intent (client + period),
   not the memo text. Edit only this file.
5. Run the test:
   ```bash
   pytest modules/02_write_path/test_write.py
   ```
6. Iterate until it's green (2 passed).
7. See the before/after:
   ```bash
   python modules/02_write_path/compare.py
   ```
   BEFORE: 2 charges ($5,000). AFTER: 1 charge ($2,500).
