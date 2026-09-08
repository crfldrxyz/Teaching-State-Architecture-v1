from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .m3 import InterventionLevel, Severity
from .m4 import Finding
from .m5 import InterventionDecision, TeacherResponse


M7_VERSION = "0.2.0"


class Result(str, Enum):
    CONFIRMED = "confirmed"
    PARTIAL = "partially_confirmed"
    UNCERTAIN = "uncertain"
    INCORRECT = "incorrect"
    NA = "not_applicable"


class Dimension(str, Enum):
    ACCURACY = "accuracy"
    TIMING = "timing"
    PROPORTIONALITY = "intervention_proportionality"
    USEFULNESS = "teacher_usefulness"
    CONFIDENCE = "confidence"
    PRIVACY = "privacy"
    OUTCOME = "instructional_impact"


class ErrorType(str, Enum):
    OBSERVATION = "observation_error"
    INFERENCE = "inference_error"
    CONTEXT = "context_error"
    KNOWLEDGE = "knowledge_error"
    SEVERITY = "severity_error"
    CONFIDENCE = "confidence_error"
    POLICY = "policy_error"
    TIMING = "timing_error"
    DELIVERY = "delivery_error"
    SUPPRESSION = "suppression_error"
    STATE = "state_error"
    PRIVACY = "privacy_error"
    UNKNOWN = "outcome_unknown"


@dataclass(frozen=True)
class EvaluationEvidence:
    id: str
    source_type: str
    observation: str
    confidence: float = 1.0


@dataclass(frozen=True)
class Evaluation:
    id: str
    target_id: str
    dimension: Dimension
    result: Result
    confidence: float
    evidence: tuple[EvaluationEvidence, ...]
    rationale: str
    evaluator_version: str = M7_VERSION


@dataclass(frozen=True)
class Outcome:
    id: str
    intervention_id: str
    resolution: str
    instructional_effect: str
    confidence: float = 0.0


@dataclass(frozen=True)
class ImprovementProposal:
    id: str
    problem: str
    proposed_change: str
    affected_component: str
    validation_plan: str
    status: str = "proposed"


class EvaluationEngine:
    """Offline evaluation and improvement proposal engine.

    M7 can propose changes but cannot mutate production policy.
    """

    def evaluate_decision(self, f: Finding, d: InterventionDecision) -> Evaluation:
        c = max(0.0, min(1.0, f.confidence))
        evidence = max(0.0, min(1.0, f.evidence_strength))
        relevance = max(0.0, min(1.0, f.relevance))
        disruption = max(0.0, min(1.0, f.disruption_cost))
        l4_allowed = (
            f.severity is Severity.CRITICAL
            and c >= 0.90
            and evidence >= 0.80
            and relevance >= 0.70
            and (f.immediate_risk or f.knowledge_risk)
            and disruption <= 0.30
        )
        if l4_allowed:
            max_allowed = InterventionLevel.L4
        elif f.severity in (Severity.MODERATE, Severity.SIGNIFICANT) and c >= 0.80:
            max_allowed = InterventionLevel.L3
        elif c >= 0.50:
            max_allowed = InterventionLevel.L2
        else:
            max_allowed = InterventionLevel.L0

        result = (
            Result.CONFIRMED
            if d.level.value <= max_allowed.value
            else Result.INCORRECT
        )
        gap = d.level.value - max_allowed.value
        rationale = (
            f"confidence={c:.2f}; severity={f.severity.value}; "
            f"evidence_strength={evidence:.2f}; relevance={relevance:.2f}; "
            f"disruption_cost={disruption:.2f}; selected_level={d.level.name}; "
            f"maximum_policy_level={max_allowed.name}; proportionality_gap={gap}"
        )
        return Evaluation(
            f"eval-{d.id}", d.id, Dimension.PROPORTIONALITY, result, c, (), rationale
        )

    def evaluate_feedback(
        self,
        d: InterventionDecision,
        response: TeacherResponse,
    ) -> Evaluation:
        result = (
            Result.UNCERTAIN
            if response in (TeacherResponse.REJECTED, TeacherResponse.DISMISSED)
            else Result.CONFIRMED
        )
        rationale = (
            f"Teacher response={response.value}; response is evaluation evidence, "
            "not automatic proof of system error."
        )
        return Evaluation(
            f"feedback-{d.id}",
            d.id,
            Dimension.USEFULNESS,
            result,
            0.5,
            (),
            rationale,
        )

    def attribute_error(self, evaluation: Evaluation) -> ErrorType:
        if evaluation.result is not Result.INCORRECT:
            return ErrorType.UNKNOWN
        if evaluation.dimension is Dimension.PROPORTIONALITY:
            return ErrorType.POLICY
        if evaluation.dimension is Dimension.TIMING:
            return ErrorType.TIMING
        if evaluation.dimension is Dimension.PRIVACY:
            return ErrorType.PRIVACY
        if evaluation.dimension is Dimension.CONFIDENCE:
            return ErrorType.CONFIDENCE
        return ErrorType.UNKNOWN

    def propose(self, evaluations: list[Evaluation]) -> tuple[ImprovementProposal, ...]:
        bad = [e for e in evaluations if e.result is Result.INCORRECT]
        if not bad:
            return ()
        return (
            ImprovementProposal(
                id=f"proposal-{bad[0].id}",
                problem="Observed evaluation failures require controlled review.",
                proposed_change="Investigate failing cases; change only after offline validation.",
                affected_component=self.attribute_error(bad[0]).value,
                validation_plan=(
                    "Offline replay, regression corpus, constitutional invariant tests, "
                    "human review, then versioned deployment."
                ),
                status="proposed",
            ),
        )
