from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .m3 import Severity, TeachingState


class FindingType(str, Enum):
    DRIFT = "drift"
    MISMATCH = "mismatch"
    KNOWLEDGE = "knowledge_integrity"
    WEAK_POINT = "weak_point"


class Status(str, Enum):
    OPEN = "open"
    RESOLVED = "resolved"
    DISMISSED = "dismissed"


@dataclass(frozen=True)
class Evidence:
    id: str
    source: str
    excerpt: str = ""
    confidence: float = 1.0


@dataclass(frozen=True)
class Finding:
    id: str
    type: FindingType
    message: str
    confidence: float
    severity: Severity
    evidence: tuple[Evidence, ...] = ()
    status: Status = Status.OPEN
    repetitions: int = 1
    immediate_risk: bool = False
    knowledge_risk: bool = False
    evidence_strength: float = 1.0
    persistence: float = 0.0
    recoverability: float = 0.5
    relevance: float = 1.0
    disruption_cost: float = 0.5
    intervention_density: float = 0.0


class DetectionEngine:
    """Deterministic M4 finding orchestration.

    Detection creates findings; it never authorizes intervention levels.
    """

    def detect(self, state: TeachingState) -> tuple[Finding, ...]:
        if not state.unresolved:
            return ()
        return (
            Finding(
                id=f"weak-{state.version}",
                type=FindingType.WEAK_POINT,
                message="Unresolved instructional item remains active",
                confidence=0.88,
                severity=Severity.MODERATE,
                persistence=1.0,
                recoverability=0.7,
            ),
        )
