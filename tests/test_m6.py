import pytest

from tsa.m3 import InterventionLevel, Severity, TeachingState
from tsa.m4 import Finding, FindingType, Status
from tsa.m5 import PolicyEngine
from tsa.m6 import (
    AssistanceStatus,
    AttentionState,
    Availability,
    CopilotEngine,
    InstructionalPhase,
    PresentationMode,
    SpeakingStatus,
    TeacherAction,
)


def make_finding(confidence=0.90, severity=Severity.MODERATE, **kwargs):
    return Finding(
        "f1",
        FindingType.KNOWLEDGE,
        "Check this claim.",
        confidence,
        severity,
        **kwargs,
    )


def test_m6_cannot_escalate_m5_level():
    finding = make_finding()
    decision = PolicyEngine().decide(TeachingState("s1"), finding)
    assistance = CopilotEngine().create_assistance(
        decision,
        AttentionState(availability=Availability.AVAILABLE),
    )
    assert assistance is not None
    assert assistance.level.value <= decision.level.value


def test_suppressed_decision_creates_no_assistance():
    finding = make_finding(repetitions=3)
    decision = PolicyEngine().decide(TeachingState("s1"), finding)
    assert decision.suppressed
    assert CopilotEngine().create_assistance(
        decision, AttentionState(availability=Availability.AVAILABLE)
    ) is None


def test_l4_is_emergency_and_bypasses_attention_budget():
    finding = make_finding(
        confidence=0.96,
        severity=Severity.CRITICAL,
        immediate_risk=True,
        knowledge_risk=True,
        evidence_strength=0.95,
        relevance=0.95,
        disruption_cost=0.10,
    )
    decision = PolicyEngine().decide(TeachingState("s1"), finding)
    assert decision.level is InterventionLevel.L4

    state = AttentionState(
        availability=Availability.BUSY,
        cognitive_load_estimate=0.99,
        speaking_status=SpeakingStatus.SPEAKING,
        instructional_phase=InstructionalPhase.ASSESSMENT,
        intervention_density=0.90,
        interruption_cost=1.0,
    )
    assert CopilotEngine().resolve_presentation(decision, state) is PresentationMode.EMERGENCY


def test_high_speaking_load_avoids_inline():
    finding = make_finding()
    decision = PolicyEngine().decide(TeachingState("s1"), finding)
    state = AttentionState(
        availability=Availability.AVAILABLE,
        cognitive_load_estimate=0.40,
        speaking_status=SpeakingStatus.SPEAKING,
        instructional_phase=InstructionalPhase.EXPLANATION,
        intervention_density=0.0,
        interruption_cost=0.30,
    )
    mode = CopilotEngine().resolve_presentation(decision, state)
    assert mode is not PresentationMode.INLINE


def test_modify_requires_content():
    finding = make_finding()
    decision = PolicyEngine().decide(TeachingState("s1"), finding)
    assistance = CopilotEngine().create_assistance(
        decision, AttentionState(availability=Availability.AVAILABLE)
    )
    assert assistance is not None
    with pytest.raises(ValueError):
        CopilotEngine().apply_action(
            assistance, TeacherAction.MODIFY, "a1"
        )


def test_correct_produces_structured_teacher_correction():
    finding = make_finding()
    decision = PolicyEngine().decide(TeachingState("s1"), finding)
    assistance = CopilotEngine().create_assistance(
        decision, AttentionState(availability=Availability.AVAILABLE)
    )
    assert assistance is not None
    updated, record = CopilotEngine().apply_action(
        assistance,
        TeacherAction.CORRECT,
        "a1",
        modified_content="Teacher-provided correction",
        correction_scope="FACTUAL_CLAIM",
    )
    assert updated.status is AssistanceStatus.CORRECTED
    assert record.correction is not None
    assert record.correction.correction_scope == "FACTUAL_CLAIM"


def test_attention_budget_is_deterministic():
    state = AttentionState(
        availability=Availability.BUSY,
        cognitive_load_estimate=0.75,
        speaking_status=SpeakingStatus.SPEAKING,
        instructional_phase=InstructionalPhase.EXPLANATION,
        intervention_density=0.20,
        interruption_cost=0.80,
    )
    engine = CopilotEngine()
    assert engine.attention_budget(state) == engine.attention_budget(state)
