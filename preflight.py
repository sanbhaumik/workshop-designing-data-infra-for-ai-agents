"""Environment self-check. Run first in any new environment.

`python preflight.py` -- prints a large GREEN pass or a RED fail naming the
problem.
"""
import sys
import tempfile
from pathlib import Path

from rich.console import Console

ROOT = Path(__file__).resolve().parent
console = Console()

REQUIRED_PYTHON = (3, 11)


def check_python_version() -> None:
    if sys.version_info[:2] != REQUIRED_PYTHON:
        raise RuntimeError(
            f"Python {REQUIRED_PYTHON[0]}.{REQUIRED_PYTHON[1]}.x required, "
            f"found {sys.version.split()[0]}"
        )


def check_dependencies() -> None:
    import importlib

    for module_name in ("pydantic", "numpy", "rich", "pytest", "yaml"):
        try:
            importlib.import_module(module_name)
        except ImportError as exc:
            raise RuntimeError(f"missing dependency: {module_name} ({exc})") from exc


def check_smoke_test() -> None:
    from nova.agent import Agent, SharedState
    from nova.frozen_llm import FrozenLLM
    from nova.store import RecordStore
    from nova.trace import Tracer

    fixtures = ROOT / "fixtures"
    with tempfile.TemporaryDirectory() as tmp:
        store = RecordStore(Path(tmp) / "preflight.db")
        store.init_schema()
        tracer = Tracer(Path(tmp) / "preflight_trace.jsonl")
        llm = FrozenLLM(fixtures / "llm_responses")
        agent = Agent(store, llm, fixtures / "embeddings", tracer, SharedState())

        briefing = agent.run("alpha", "preflight-run")

    expected_prefix = "Briefing for alpha:"
    if not briefing.content.startswith(expected_prefix):
        raise RuntimeError(f"smoke test produced unexpected output: {briefing.content!r}")


def main() -> None:
    checks = [
        ("Python 3.11.x", check_python_version),
        ("dependencies importable", check_dependencies),
        ("engine smoke test (FrozenLLM + Agent + store)", check_smoke_test),
    ]
    failures = []
    for name, check in checks:
        try:
            check()
            console.print(f"[green]PASS[/green] {name}")
        except Exception as exc:
            failures.append((name, exc))
            console.print(f"[red]FAIL[/red] {name}: {exc}")

    console.print()
    if failures:
        console.print("[bold white on red] RED [/bold white on red] preflight failed -- see failures above.")
        sys.exit(1)
    else:
        console.print("[bold white on green] GREEN [/bold white on green] environment ready.")


if __name__ == "__main__":
    main()
