# Module 04 — Provenance (facilitator demo)

This is a facilitator-driven demo, not a participant lab. There is no
`your_fix.py` and no test to run.

1. `python scripts/generate_trace.py` — regenerates `fixtures/traces/incident_047.json`
   from the same state-contamination scenario as Module 03.
2. `python modules/04_provenance/walk_trace.py` — walks the trace and
   reconstructs the exact read/write ordering that caused Alpha's briefing
   to contain Beta's data.
3. Point out the contrast printed at the end: without the trace, the
   database alone can't answer "why."
