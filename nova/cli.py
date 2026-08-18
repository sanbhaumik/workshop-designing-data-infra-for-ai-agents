"""Presentation helpers shared by the lab runners.

Turns infrastructure errors into legible `rich` panels (never raw tracebacks on
a screen-shared terminal) and truncates long free-text so tables stay readable
at 720p. See the design review for why these matter in a live room.
"""
import sys
from typing import Callable

from rich.console import Console
from rich.panel import Panel


def _hint_for(exc: Exception) -> tuple[str, str]:
    """Map a known error to a (what happened, what to do) pair."""
    name = type(exc).__name__
    module = type(exc).__module__ or ""
    if name == "OllamaError":
        return (
            "The local model server (Ollama) is not reachable.",
            "Run `bash setup.sh` for the live model, or set NOVA_LLM=frozen to use "
            "the recorded outputs.",
        )
    if name == "FixtureMissing":
        return (
            "There is no recorded model response for this prompt.",
            "The prompt may have changed. Re-record the fixtures, or run with "
            "NOVA_LLM=ollama to use the live model.",
        )
    if module.startswith("psycopg") or "OperationalError" in name:
        return (
            "The Postgres database is not reachable.",
            "Re-run `bash setup.sh`, or unset DATABASE_URL to fall back to a local "
            "SQLite file.",
        )
    if isinstance(exc, FileNotFoundError):
        return (
            f"A required file is missing: {exc.filename or exc}.",
            "Make sure you cloned the repo and are running from its root.",
        )
    return (f"{name}: {exc}", "Unexpected error. Re-run `python preflight.py` to check the environment.")


def run_guarded(main_fn: Callable[[], None]) -> None:
    """Run `main_fn`, rendering known infra errors as a red panel instead of a traceback."""
    console = Console()
    try:
        main_fn()
    except (SystemExit, KeyboardInterrupt):
        raise
    except Exception as exc:  # noqa: BLE001 - deliberately legible catch-all for participants
        what, todo = _hint_for(exc)
        console.print(
            Panel(
                f"{what}\n\n[dim]{todo}[/dim]",
                title="[bold]Something needs attention[/bold]",
                border_style="red",
            )
        )
        sys.exit(1)


def truncate(text: object, limit: int = 64) -> str:
    """Shorten `text` to `limit` chars with an ellipsis, for readable tables at 720p."""
    s = str(text)
    return s if len(s) <= limit else s[: limit - 1] + "…"
