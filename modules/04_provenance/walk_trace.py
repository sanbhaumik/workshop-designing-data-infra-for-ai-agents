"""Module 04 — Provenance: facilitator forensic viewer.

Walks fixtures/traces/incident_047.json and reconstructs why Alpha's
briefing ended up containing Beta's data, then contrasts that with what's
answerable from the database alone (nothing).

Run this directly: `python modules/04_provenance/walk_trace.py`
"""
import json
from pathlib import Path

from rich.console import Console
from rich.table import Table

ROOT = Path(__file__).resolve().parents[2]
TRACE_PATH = ROOT / "fixtures" / "traces" / "incident_047.json"


def load_trace() -> list[dict]:
    """Load the trace, or raise a clear error telling the facilitator what to run first."""
    if not TRACE_PATH.exists():
        raise FileNotFoundError(
            f"{TRACE_PATH} not found -- run `python scripts/generate_trace.py` first."
        )
    return json.loads(TRACE_PATH.read_text())


def main() -> None:
    console = Console()
    events = load_trace()

    table = Table(title="incident_047 — full trace")
    table.add_column("#")
    table.add_column("run_id")
    table.add_column("step")
    table.add_column("state_snapshot")
    for i, evt in enumerate(events):
        snapshot = evt["data"].get("state_snapshot", {})
        table.add_row(str(i), evt["run_id"], evt["step"], str(snapshot))
    console.print(table)

    draft_events = [e for e in events if e["step"] == "draft"]
    console.print("\n[bold]Forensic walk — draft events:[/bold]")
    for evt in draft_events:
        console.print(f"  run_id={evt['run_id']}: content = {evt['data'].get('content')!r}")
        console.print(f"    state at draft time = {evt['data'].get('state_snapshot')}")

    contaminated = [
        e for e in draft_events
        if e["run_id"].endswith("-a") and "beta" in str(e["data"].get("content", "")).lower()
    ]
    if contaminated:
        console.print(
            "\n[bold red]With the trace, the answer is clear:[/bold red] run-047-a's "
            "draft step read a state snapshot already carrying client 'beta' -- written "
            "by run-047-b earlier, into the same shared state object. The trace shows "
            "the exact read/write ordering that caused it."
        )

    console.print(
        "\n[bold]Contrast — without a trace:[/bold] all we'd have is the final corrupted "
        "briefing in the database. There would be no record of which run wrote what, "
        "when, or what state it read at the moment of the mistake -- the question "
        "'why does Alpha's briefing mention Beta?' would be unanswerable."
    )


if __name__ == "__main__":
    main()
