"""Environment self-check. Run first in any new environment.

`python preflight.py` -- prints a large GREEN pass or a RED fail naming the
problem. Adapts to configuration:
    NOVA_LLM=ollama (default) checks a live model; NOVA_LLM=frozen checks fixtures.
    DATABASE_URL=postgres://... checks Postgres; otherwise a local SQLite file.
"""
import os
import sys
from pathlib import Path

from rich.console import Console

ROOT = Path(__file__).resolve().parent
console = Console()

MIN_PYTHON = (3, 11)


def check_python_version() -> None:
    if sys.version_info[:2] < MIN_PYTHON:
        raise RuntimeError(
            f"Python {MIN_PYTHON[0]}.{MIN_PYTHON[1]}+ required, "
            f"found {sys.version.split()[0]}"
        )


def check_dependencies() -> None:
    import importlib

    modules = ["pydantic", "numpy", "rich", "pytest", "yaml"]
    if os.environ.get("DATABASE_URL", "").startswith("postgres"):
        modules.append("psycopg")
    for module_name in modules:
        importlib.import_module(module_name)


def check_llm() -> None:
    from nova.llm import get_llm

    backend = os.environ.get("NOVA_LLM", "ollama")
    llm = get_llm()
    if backend == "ollama":
        out = llm.complete("Reply with the single word: ready")
        if not out:
            raise RuntimeError("Ollama returned an empty response")
    else:  # frozen — confirm a known fixture loads
        from nova.agent import load_document, payment_memo_prompt

        doc = load_document("alpha", "billing_instruction.md")
        llm.complete(payment_memo_prompt("alpha", "Q1-2026", doc, 1))


def check_database() -> None:
    from nova.store import get_store

    store = get_store()
    store.init_schema()
    store.get_charges()  # a real query against the configured backend
    store.close()


def check_smoke_test() -> None:
    from nova.agent import load_document, payment_memo_prompt
    from nova.effects import PaymentGateway
    from nova.llm import get_llm
    from nova.store import get_store

    store = get_store()
    store.init_schema()
    store.reset_demo()
    llm = get_llm()
    gateway = PaymentGateway()

    doc = load_document("alpha", "billing_instruction.md")
    memo = llm.complete(payment_memo_prompt("alpha", "Q1-2026", doc, 1))
    gateway.charge("alpha", 2500, memo)
    store.record_charge("preflight-key", "alpha", 2500)
    if len(gateway.charges_for("alpha")) != 1 or not store.already_charged("preflight-key"):
        raise RuntimeError("smoke test did not complete a single charge")
    store.reset_demo()
    store.close()


def main() -> None:
    backend = os.environ.get("NOVA_LLM", "ollama")
    db = "Postgres" if os.environ.get("DATABASE_URL", "").startswith("postgres") else "SQLite"
    console.print(f"[dim]LLM backend: {backend}   •   Database: {db}[/dim]\n")

    checks = [
        ("Python 3.11.x", check_python_version),
        ("dependencies importable", check_dependencies),
        (f"LLM reachable ({backend})", check_llm),
        (f"database reachable ({db})", check_database),
        ("agent smoke test (retrieve → reason → charge)", check_smoke_test),
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
    console.print("[bold white on green] GREEN [/bold white on green] environment ready.")


if __name__ == "__main__":
    main()
