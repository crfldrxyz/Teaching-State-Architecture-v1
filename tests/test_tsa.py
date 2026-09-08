import pytest

from tsa.m3 import *
from tsa.m4 import *
from tsa.m5 import *
from tsa.m7 import *


def state():
    return TeachingState("s1")


def finding(conf=.95, severity=Severity.SIGNIFICANT, **kw):
    return Finding("f", FindingType.DRIFT, "test", conf, severity, **kw)


def test_low_confidence_never_high_intensity():
    d = PolicyEngine().decide(
        state(),
        finding(.79, Severity.CRITICAL, immediate_risk=True),
    )
    assert d.level.value < 3


def test_l4_requires_all_gates():
    p = PolicyEngine()
    critical = finding(
        .90,
        Severity.CRITICAL,
        immediate_risk=True,
        evidence_strength=.80,
        relevance=.70,
        disruption_cost=.30,
    )
    assert p.decide(state(), critical).level is InterventionLevel.L4
    assert p.decide(
        state(),
        finding(
            .90,
            Severity.CRITICAL,
            immediate_risk=True,
            evidence_strength=.80,
            relevance=.70,
            disruption_cost=.31,
        ),
    ).level.value < 4
    assert p.decide(
        state(),
        finding(
            .90,
            Severity.CRITICAL,
            immediate_risk=False,
            evidence_strength=.80,
            relevance=.70,
            disruption_cost=.20,
        ),
    ).level.value < 4
    assert p.decide(
        state(),
        finding(
            .89,
            Severity.CRITICAL,
            immediate_risk=True,
            evidence_strength=.90,
            relevance=.90,
            disruption_cost=.20,
        ),
    ).level.value < 4


def test_repetition_suppression():
    assert PolicyEngine().decide(state(), finding(.99, repetitions=3)).suppressed


def test_resolved_suppression():
    f = finding(.99, status=Status.RESOLVED)
    assert PolicyEngine().decide(state(), f).level is InterventionLevel.L0


def test_proportionality_evaluation():
    f = finding(.95, Severity.SIGNIFICANT)
    d = PolicyEngine().decide(state(), f)
    assert EvaluationEngine().evaluate_decision(f, d).result is Result.CONFIRMED


def test_teacher_dismissal_is_uncertain_not_incorrect():
    f = finding(.95)
    d = PolicyEngine().decide(state(), f)
    assert EvaluationEngine().evaluate_feedback(
        d,
        TeacherResponse.DISMISSED,
    ).result is Result.UNCERTAIN


def test_m3_idempotent_events():
    e = InstructionalEvent("1", 1, EventType.TOPIC, "fractions")
    eng = StateEngine(state())
    eng.apply(e)
    eng.apply(e)
    assert eng.state.version == 1 and eng.state.topic == "fractions"


def test_improvement_requires_failure_and_is_not_deployment():
    f = finding(.95)
    d = InterventionDecision(
        "d",
        "f",
        InterventionLevel.L4,
        "x",
        "confidence=.95; severity=significant; contextual factors",
    )
    ev = EvaluationEngine().evaluate_decision(f, d)
    proposal = EvaluationEngine().propose([ev])
    assert proposal and proposal[0].status == "proposed"
