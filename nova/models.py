"""Pydantic models shared across the engine."""
from pydantic import BaseModel


class ClientDocument(BaseModel):
    """A single source document belonging to a client."""

    client_id: str
    doc_id: str
    path: str
    content: str = ""


class Summary(BaseModel):
    """The account summary produced by an agent run for one client."""

    client_id: str
    content: str


class TraceEvent(BaseModel):
    """One provenance event: what a run did at a single step."""

    run_id: str
    step: str
    data: dict
