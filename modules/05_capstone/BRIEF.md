# Module 05 — Capstone Architecture Review

<!--
AUTHOR TODO: the capstone brief (2:55-3:40) is authored by a human and does
not live in this repo. This file is a scaffold of the shape the repositioned
capstone should take. Write the actual candidate architecture and narration
elsewhere.

This block carries the workshop's architect-level "designing" promise. It is
the highest-leverage authored asset. Design it around the four invariants the
labs installed.

Shape:

1. Present a candidate data architecture for an agent system (a diagram: an
   agent that retrieves client docs, writes obligations/briefings to a store,
   serves multiple tenants, retries on failure). Seed it with realistic flaws.

2. Participants SCORE it against the four invariants (this is the exercise):

   | Invariant                | Question to ask the architecture              |
   |--------------------------|-----------------------------------------------|
   | Identity                 | Are writes keyed on intent, or on model output? |
   | Isolation                | Is state/memory namespaced per run and tenant?  |
   | Idempotency / durability | Are retries safe? Are effects exactly-once?     |
   |                          | Does a crashed run recover without redoing work?|
   | Provenance               | Can you reconstruct what each run read and wrote?|

3. The seeded flaws should map back to the labs: an output-derived
   idempotency key (Lab 1), a shared memory store across tenants (Lab 2), a
   fire-and-forget side effect with no recovery, and no trace.

4. Deliverable: participants leave with the four-invariant scorecard as a
   reusable review tool for their own architectures.
-->
