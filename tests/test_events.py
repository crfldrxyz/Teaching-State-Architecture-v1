import pytest

from tsa.events import TSAEvent


def test_event_envelope_is_immutable_and_valid():
    event = TSAEvent(
        event_id="e1",
        event_type="intervention_decision",
        session_id="s1",
        timestamp=1.0,
        source_layer="M5",
        state_version=4,
        correlation_id="corr-1",
        causation_id="finding-1",
        payload_ref="decision-1",
    )
    assert event.state_version == 4
    with pytest.raises((AttributeError, TypeError)):
        event.state_version = 5


def test_event_requires_correlation_identity():
    with pytest.raises(ValueError):
        TSAEvent("", "x", "s1", 1.0, "M3", 0, "c1")
    with pytest.raises(ValueError):
        TSAEvent("e1", "x", "s1", 1.0, "M3", 0, "")


def test_event_rejects_negative_version_and_timestamp():
    with pytest.raises(ValueError):
        TSAEvent("e1", "x", "s1", 1.0, "M3", -1, "c1")
    with pytest.raises(ValueError):
        TSAEvent("e1", "x", "s1", -1.0, "M3", 0, "c1")
