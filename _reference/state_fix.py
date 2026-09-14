"""Reference solution for Module 03 — never shipped to participants.

The obvious fix is `return run_id`: give each run its own slot. It passes the
live-isolation test. But run ids are ephemeral and get reused across a crash and
resume -- so a resumed run keyed on run_id can load another tenant's checkpoint.

The durable fix keys memory on the UNIT OF WORK -- the tenant -- so the right
checkpoint is found whether the run is live, retried, or resumed.
"""


def state_key(run_id: str, tenant: str) -> str:
    """Key working memory by the tenant (the unit of work), not the run id."""
    return tenant
