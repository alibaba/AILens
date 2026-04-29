"""Standard Trace data models - Pydantic version for compatibility."""

from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class SpanStatus(str, Enum):
    """Span status enumeration."""

    OK = "ok"
    ERROR = "error"
    UNSET = "unset"


class SpanAttribute(BaseModel):
    """Span attribute key-value pair."""

    key: str
    value: str


class SpanEvent(BaseModel):
    """Span event."""

    name: str
    timestamp: int  # millisecond timestamp
    attributes: Dict[str, str] = Field(default_factory=dict)


class Span(BaseModel):
    """Standard Span data model."""

    span_id: str
    trace_id: str
    operation_name: str  # Operation name (e.g., RPC method name)
    service_name: str  # Service name
    start_time: int  # Start time (millisecond timestamp)
    duration_ms: int  # Duration (milliseconds)

    parent_span_id: Optional[str] = None

    # Status
    status: SpanStatus = SpanStatus.UNSET
    status_message: Optional[str] = None

    # Attributes and events
    attributes: List[SpanAttribute] = Field(default_factory=list)
    events: List[SpanEvent] = Field(default_factory=list)

    # Classification
    span_kind: str = "internal"  # internal, client, server, producer, consumer

    # Raw data (preserve backend-specific fields)
    raw: Dict = Field(default_factory=dict)


class Trace(BaseModel):
    """Standard Trace data model."""

    trace_id: str
    spans: List[Span]

    # Aggregated information
    duration_ms: int = 0
    span_count: int = 0
    has_error: bool = False
    root_operation: Optional[str] = None
    root_service: Optional[str] = None

    # Raw data
    raw: Dict = Field(default_factory=dict)


class TraceSearchResult(BaseModel):
    """Trace search result."""

    trace_id: str
    start_time: int
    duration_ms: int
    span_count: int
    status: SpanStatus

    # Optional fields
    root_operation: Optional[str] = None
    root_service: Optional[str] = None
    experiment_id: Optional[str] = None
    trajectory_id: Optional[str] = None
    raw: Dict = Field(default_factory=dict)
