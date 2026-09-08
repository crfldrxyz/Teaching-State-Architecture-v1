"""Realistic classroom simulations for the M5 → M6 boundary."""

from tsa.m3 import InterventionLevel, Severity, TeachingState
from tsa.m4 import Finding, FindingType
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


def test_minor_topic_drift_during_active_objective():
    """Teacher is speaking about photosynthesis and briefly drifts into history."""
    finding = Finding(
        "drift-001",
        FindingType.DRIFT,
        "Topic is drifting from the active photosynthesis objective.",
        0.86,
        Severity.MINOR,
        persistence=0.6,
        recoverability=0.8,
        relevance=0.9,
        disruption_cost=0.8,
    )
    state = TeachingState("lesson-01", version=12, topic="photosynthesis", objective="explain photosynthesis")
    decision = PolicyEngine().decide(state, finding)

    assert decision.level is InterventionLevel.L2
    assert not decision.suppressed

    assistance = CopilotEngine().create_assistance(
        decision,
        AttentionState(
            availability=Availability.AVAILABLE,
            cognitive_load_estimate=0.55,
            speaking_status=SpeakingStatus.SPEAKING,
            instructional_phase=InstructionalPhase.EXPLANATION,
            interruption_cost=0.70,
        ),
    )
    assert assistance is not None
    assert assistance.presentation_mode in {
        PresentationMode.PASSIVE,
        PresentationMode.BADGE,
        PresentationMode.SIDEBAR,
        PresentationMode.CARD,
    }
    assert assistance.presentation_mode is not PresentationMode.EMERGENCY


def test_factual_error_during_high_teacher_speaking_load():
    """Teacher speaks rapidly; a well-supported conceptual error needs a prompt, not an interrupt."""
    finding = Finding(
        "knowledge-002",
        FindingType.KNOWLEDGE,
        "The explanation appears to conflate two distinct concepts.",
        0.91,
        Severity.MODERATE,
        knowledge_risk=True,
        evidence_strength=0.90,
        relevance=0.95,
        disruption_cost=0.90,
    )
    decision = PolicyEngine().decide(TeachingState("lesson-02", version=20), finding)

    assert decision.level is InterventionLevel.L3
    assert decision.level is not InterventionLevel.L4

    assistance = CopilotEngine().create_assistance(
        decision,
        AttentionState(
            availability=Availability.BUSY,
            cognitive_load_estimate=0.82,
            speaking_status=SpeakingStatus.SPEAKING,
            instructional_phase=InstructionalPhase.EXPLANATION,
            intervention_density=0.10,
            interruption_cost=0.90,
        ),
    )
    assert assistance is not None
    assert assistance.level is decision.level
    assert assistance.presentation_mode is not PresentationMode.EMERGENCY
    assert assistance.presentation_mode is not PresentationMode.INLINE


def test_critical_knowledge_risk_reaches_emergency_surface():
    finding = Finding(
        "critical-003",
        FindingType.KNOWLEDGE,
        "Critical knowledge-integrity risk requires immediate review.",
        0.96,
        Severity.CRITICAL,
        immediate_risk=True,
        knowledge_risk=True,
        evidence_strength=0.95,
        relevance=0.95,
        disruption_cost=0.20,
    )
    decision = PolicyEngine().decide(TeachingState("lesson-03", version=30), finding)
    assert decision.level is InterventionLevel.L4

    assistance = CopilotEngine().create_assistance(
        decision,
        AttentionState(
            availability=Availability.BUSY,
            cognitive_load_estimate=0.98,
            speaking_status=SpeakingStatus.SPEAKING,
            instructional_phase=InstructionalPhase.EXPLANATION,
            intervention_density=0.80,
            interruption_cost=1.0,
        ),
    )
    assert assistance is not None
    assert assistance.presentation_mode is PresentationMode.EMERGENCY


def test_teacher_correction_survives_delivery_layer():
    finding = Finding(
        "knowledge-004",
        FindingType.KNOWLEDGE,
        "Check this factual claim.",
        0.90,
        Severity.MODERATE,
        knowledge_risk=True,
        evidence_strength=0.90,
        relevance=0.90,
        disruption_cost=0.30,
    )
    decision = PolicyEngine().decide(TeachingState("lesson-04"), finding)
    assistance = CopilotEngine().create_assistance(
        decision, AttentionState(availability=Availability.AVAILABLE)
    )
    assert assistance is not None

    updated, record = CopilotEngine().apply_action(
        assistance,
        TeacherAction.CORRECT,
        "action-004",
        modified_content="The teacher's correction is the authoritative feedback event.",
        correction_scope="FACTUAL_CLAIM",
    )
    assert updated.status is AssistanceStatus.CORRECTED
    assert record.correction is not None
    assert record.correction.assistance_id == assistance.id
    assert assistance.level == decision.level
