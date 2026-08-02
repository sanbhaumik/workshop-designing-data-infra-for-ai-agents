"""Pydantic models shared across the engine."""
from typing import Optional

from pydantic import BaseModel, Field


class ClientDocument(BaseModel):
    """A single source document belonging to a client."""

    client_id: str
    doc_id: str
    path: str
    content: str = ""


class Obligation(BaseModel):
    """A single extracted obligation tied to a client and source document."""

    id: Optional[int] = None
    client_id: str
    text: str
    source_doc: str
    idempotency_key: Optional[str] = None


class Briefing(BaseModel):
    """The drafted output of an agent run for one client."""

    client_id: str
    content: str
    obligations: list[Obligation] = Field(default_factory=list)


class TraceEvent(BaseModel):
    """One provenance event: what a run did at a single step."""

    run_id: str
    step: str
    data: dict
