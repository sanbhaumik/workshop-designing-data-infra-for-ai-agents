# Module 01 — Opening & Readiness Review

<!--
AUTHOR TODO: the opening talk track (0:00-0:20) is authored by a human and
does not live in this repo. This file is a scaffold of the beats the
repositioned workshop needs the opening to hit. Write the narration elsewhere.

Positioning (from the strategy review): own the neglected failures. Do NOT
frame this as a survey of all data infrastructure.

Beats to cover:

1. THE THESIS (say it once, plainly):
   An AI agent is a non-deterministic, concurrent, retrying, crash-prone
   producer of side effects. A data layer built for ordinary callers does not
   survive that. It needs four invariants:
     - Identity      (from intent, not output)
     - Isolation     (per run / per tenant)
     - Idempotency / durability (safe retries, exactly-once effects, recovery)
     - Provenance    (reconstruct what was read and written)

2. THE LANDSCAPE MAP (one slide; show WHERE the labs sit):
     ingestion -> retrieval -> memory -> reasoning -> WRITE-BACK -> provenance -> eval
                                   ^^^^^^                ^^^^^^^^^^   ^^^^^^^^^
                                  Lab 2                 Lab 1        Demo
   Highlight that Lab 1 (write-back) and Lab 2 (memory/state) are the two
   boxes nobody teaches, and the provenance demo is the "how do you see it"
   box.

3. WHY NOT RAG / EVAL (name the omission out loud — the audience expects it):
   "Everyone teaches retrieval. Nobody teaches what happens when the agent
   writes. That is where your data corrupts, and that is today. Evaluation is
   a separate body of work we are not covering here."

4. THE FROZEN/REAL DISCLOSURE:
   The labs run a real local model (Ollama) against a real database
   (Postgres). The test suite uses frozen fixtures so failures reproduce
   deterministically. Disclose this so nobody wonders whether it's "real."

5. READINESS GATE:
   Everyone runs preflight and sees GREEN before Lab 1. (Mechanical; the
   command is `python preflight.py`.)
-->
