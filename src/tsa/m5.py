from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .m3 import InterventionLevel, Severity, TeachingState
from .m4 import Finding, Status


POLICY_VERSION = "0.2.0"


class TeacherResponse(str, Enum):
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    DISMISSED = "dismissed"
    DEFERRED = "deferred"
    MODIFIED = "modified"
    CORRECTED = "corrected_by_teacher"
    NONE = "no_response"


@dataclass(frozen=True)
class InterventionDecision:
    id: str
    finding_id: str
    level: InterventionLevel
    message: str
    rationale: str
    suppressed: bool = False
    policy_version: str = POLICY_VERSION


@dataclass(frozen=True)
class DecisionAudit:
    decision_id: str
    finding_id: str
    state_id: str
    state_version: int
    policy_version: str
    confidence: float
    severity: Severity
    selected_level: InterventionLevel
    suppressed: bool
    rationale: str


class PolicyEngine:
    """Deterministic M5 authorization engine.

    M5 authorizes intervention intensity. It does not decide presentation.
    """

    @staticmethod
    def _clamp(value: float) -> float:
        return max(0.0, min(1.0, value))

    def decide(self, state: TeachingState, f: Finding) -> InterventionDecision:
        c = self._clamp(f.confidence)
        evidence = self._clamp(f.evidence_strength)
        relevance = self._clamp(f.relevance)
        disruption = self._clamp(f.disruption_cost)
        density = self._clamp(f.intervention_density)
        ctx = (
            f"confidence={c:.2f}; severity={f.severity.value}; "
            f"evidence_strength={evidence:.2f}; persistence={f.persistence:.2f}; "
            f"recoverability={f.recoverability:.2f}; relevance={relevance:.2f}; "
            f"disruption_cost={disruption:.2f}; intervention_density={density:.2f}; "
            f"repetitions={f.repetitions}; immediate_risk={f.immediate_risk}; "
            f"knowledge_risk={f.knowledge_risk}; state_version={state.version}"
        )

        if f.status is not Status.OPEN:
            level, suppressed, reason = (
                InterventionLevel.L0,
                True,
                "Finding is resolved/dismissed; no active intervention.",
            )
        elif f.repetitions >= 3:
            level, suppressed, reason = (
                InterventionLevel.L0,
                True,
                "Repeated finding suppressed for anti-fatigue.",
            )
        elif c < 0.50:
            level, suppressed, reason = (
                InterventionLevel.L0,
                False,
                "Confidence is too low for an active intervention.",
            )
        elif c < 0.80:
            level, suppressed, reason = (
                InterventionLevel.L2,
                False,
                "Confidence below high-intensity threshold; signal only.",
            )
        elif (
            f.severity is Severity.CRITICAL
            and c >= 0.90
            and evidence >= 0.80
            and relevance >= 0.70
            and (f.immediate_risk or f.knowledge_risk)
            and disruption <= 0.30
        ):
            level, suppressed, reason = (
                InterventionLevel.L4,
                False,
                "Critical immediate welfare/knowledge-integrity risk meets the L4 gate.",
            )
        elif f.severity in (Severity.MODERATE, Severity.SIGNIFICANT):
            if relevance < 0.50 or density >= 0.75:
                level, suppressed, reason = (
                    InterventionLevel.L2,
                    False,
                    "Contextual relevance or intervention density makes a lower-disruption signal more appropriate.",
                )
            else:
                level, suppressed, reason = (
                    InterventionLevel.L3,
                    False,
                    "Proportional prompt selected as the lowest effective level for a meaningful finding.",
                )
        else:
            level, suppressed, reason = (
                InterventionLevel.L2,
                False,
                "Low-disruption signal selected as the minimum effective intervention.",
            )

        rationale = f"{reason} {ctx}"
        return InterventionDecision(
            id=f"decision-{f.id}",
            finding_id=f.id,
            level=level,
            message=f.message,
            rationale=rationale,
            suppressed=suppressed,
        )

    def audit(self, state: TeachingState, finding: Finding) -> DecisionAudit:
        decision = self.decide(state, finding)
        return DecisionAudit(
            decision_id=decision.id,
            finding_id=finding.id,
            state_id=state.session_id,
            state_version=state.version,
            policy_version=decision.policy_version,
            confidence=max(0.0, min(1.0, finding.confidence)),
            severity=finding.severity,
            selected_level=decision.level,
            suppressed=decision.suppressed,
            rationale=decision.rationale,
        )
