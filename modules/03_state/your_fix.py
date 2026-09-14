"""Module 03 — State, Memory & Recovery: your fix.

Edit ONLY this file. You change one function: `state_key`.

The agent stores each run's working memory in a shared `MemoryStore`, under a key
YOU choose. Right now every run returns the same key (""), so two tenants' runs
collide in one slot and one tenant's data leaks into the other's summary.

There are two tests. One is the live leak. The second is a crash-and-resume — and
a fix that passes the first can still fail the second. That's the point.
"""


def state_key(run_id: str, tenant: str) -> str:
    """Return the key under which this run's working memory is stored.

    Args:
      run_id: the id of THIS run/attempt. It is ephemeral -- a resumed run may
              arrive with a reused id, and ids are not unique to a piece of work.
      tenant: the client this run is serving.
    """
    # TODO: give each run its own memory so two tenants never share a slot.
    return ""  # NAIVE: every run shares one slot -> cross-tenant leak
