# Module 04 — Provenance: facilitator instructions

This block is a facilitator-driven demo. There is no `your_fix.py` and no
test — nothing for participants to edit or run on their own machines.

## Prerequisites

- Environment ready: `python preflight.py` prints a green **GREEN**.

## Steps

1. Regenerate the trace:
   ```bash
   python scripts/generate_trace.py
   ```
   This writes `fixtures/traces/incident_047.json`.
2. Walk the trace:
   ```bash
   python modules/04_provenance/walk_trace.py
   ```
3. Walk the printed table row by row with participants, then the "draft
   events" section, then the final contrast statement.

## Files

| File | Edit? |
|---|---|
| `scripts/generate_trace.py` | No |
| `modules/04_provenance/walk_trace.py` | No |

## Troubleshooting

- `walk_trace.py` reports the trace file is missing → run
  `python scripts/generate_trace.py` first (step 1).
