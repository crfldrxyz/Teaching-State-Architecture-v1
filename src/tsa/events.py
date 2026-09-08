from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class TSAEvent:
    """Canonical cross-layer correlation envelope.

    Payloads remain owned by their originating layer; this envelope carries
    enough metadata to reconstruct a consequential execution trace.
    """

    event_id: str
    event_type: str
    session_id: str
    timestamp: float
    source_layer: str
    state_version: int
    correlation_id: str
    causation_id: Optional[str] = None
    payload_ref: Optional[str] = None

    def __post_init__(self) -> None:
        if not self.event_id or not self.session_id or not self.correlation_id:
            raise ValueError("event_id, session_id, and correlation_id are required")
        if self.state_version < 0:
            raise ValueError("state_version must be non-negative")
        if self.timestamp < 0:
            raise ValueError("timestamp must be non-negative")
