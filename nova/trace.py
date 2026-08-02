"""Structured provenance logging. Every agent step emits an event; events are
kept in memory and appended to disk as JSON lines as they happen.
"""
from pathlib import Path

from nova.models import TraceEvent


class Tracer:
    """Records TraceEvents in memory and streams them to `out_path` as JSON lines."""

    def __init__(self, out_path: Path) -> None:
        self.out_path = Path(out_path)
        self.out_path.parent.mkdir(parents=True, exist_ok=True)
        self.out_path.write_text("")
        self._events: list[TraceEvent] = []

    def event(self, run_id: str, step: str, data: dict) -> None:
        """Record one event for `run_id` at `step`, with arbitrary `data`."""
        evt = TraceEvent(run_id=run_id, step=step, data=data)
        self._events.append(evt)
        with self.out_path.open("a") as f:
            f.write(evt.model_dump_json() + "\n")

    def dump(self) -> list[TraceEvent]:
        """Return all recorded events, in the order they occurred."""
        return list(self._events)
