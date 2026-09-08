from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional

from .m3 import InterventionLevel
from .m5 import InterventionDecision


class Availability(str, Enum):
    AVAILABLE = "AVAILABLE"
    LIMITED = "LIMITED"
    BUSY = "BUSY"
    UNAVAILABLE = "UNAVAILABLE"
    UNKNOWN = "UNKNOWN"


class SpeakingStatus(str, Enum):
    SPEAKING = "SPEAKING"
    LISTENING = "LISTENING"
    SILENT = "SILENT"
    UNKNOWN = "UNKNOWN"


class InstructionalPhase(str, Enum):
    OPENING = "OPENING"
    EXPLANATION = "EXPLANATION"
    QUESTIONING = "QUESTIONING"
    DISCUSSION = "DISCUSSION"
    ASSESSMENT = "ASSESSMENT"
    ACTIVITY = "ACTIVITY"
    TRANSITION = "TRANSITION"
    CLOSING = "CLOSING"
    UNKNOWN = "UNKNOWN"


class PresentationMode(str, Enum):
    PASSIVE = "PASSIVE"
    BADGE = "BADGE"
    CARD = "CARD"
    SIDEBAR = "SIDEBAR"
    INLINE = "INLINE"
    EMERGENCY = "EMERGENCY"


class AssistanceStatus(str, Enum):
    PENDING = "PENDING"
    PRESENTED = "PRESENTED"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    ACCEPTED = "ACCEPTED"
    DISMISSED = "DISMISSED"
    DEFERRED = "DEFERRED"
    MODIFIED = "MODIFIED"
    CORRECTED = "CORRECTED"
    FOLLOW_UP = "FOLLOW_UP"
    EXPIRED = "EXPIRED"
    RESOLVED = "RESOLVED"


class TeacherAction(str, Enum):
    ACKNOWLEDGE = "ACKNOWLEDGE"
    ACCEPT = "ACCEPT"
    DISMISS = "DISMISS"
    DEFER = "DEFER"
    MODIFY = "MODIFY"
    CORRECT = "CORRECT"
    ASK = "ASK"


@dataclass(frozen=True)
class AttentionState:
    availability: Availability = Availability.UNKNOWN
    cognitive_load_estimate: float = 0.5
    speaking_status: SpeakingStatus = SpeakingStatus.UNKNOWN
    instructional_phase: InstructionalPhase = InstructionalPhase.UNKNOWN
    intervention_density: float = 0.0
    interruption_cost: float = 0.5


@dataclass(frozen=True)
class Assistance:
    id: str
    intervention_id: str
    level: InterventionLevel
    priority: str
    presentation_mode: PresentationMode
    status: AssistanceStatus
    message: str
    confidence: float


@dataclass(frozen=True)
class TeacherCorrection:
    id: str
    assistance_id: str
    corrected_content: str
    correction_scope: str


@dataclass(frozen=True)
class TeacherActionRecord:
    id: str
    assistance_id: str
    action: TeacherAction
    modified_content: Optional[str] = None
    correction: Optional[TeacherCorrection] = None


SPEAKING_LOAD = {
    SpeakingStatus.SPEAKING: 1.00,
    SpeakingStatus.LISTENING: 0.35,
    SpeakingStatus.SILENT: 0.15,
    SpeakingStatus.UNKNOWN: 0.50,
}

PHASE_LOAD = {
    InstructionalPhase.OPENING: 0.35,
    InstructionalPhase.EXPLANATION: 0.70,
    InstructionalPhase.QUESTIONING: 0.65,
    InstructionalPhase.DISCUSSION: 0.70,
    InstructionalPhase.ASSESSMENT: 0.85,
    InstructionalPhase.ACTIVITY: 0.75,
    InstructionalPhase.TRANSITION: 0.80,
    InstructionalPhase.CLOSING: 0.45,
    InstructionalPhase.UNKNOWN: 0.50,
}

AVAILABILITY_LOAD = {
    Availability.AVAILABLE: 0.10,
    Availability.LIMITED: 0.45,
    Availability.BUSY: 0.75,
    Availability.UNAVAILABLE: 1.00,
    Availability.UNKNOWN: 0.60,
}

PRESENTATION_COST = {
    PresentationMode.PASSIVE: 0.05,
    PresentationMode.BADGE: 0.10,
    PresentationMode.SIDEBAR: 0.20,
    PresentationMode.CARD: 0.30,
    PresentationMode.INLINE: 0.35,
    PresentationMode.EMERGENCY: 1.00,
}


class CopilotEngine:
    """Deterministic M6 delivery engine; cannot change M5 authorization."""

    @staticmethod
    def _clamp(value: float) -> float:
        return max(0.0, min(1.0, value))

    def attention_budget(self, state: AttentionState) -> float:
        cognitive_load = self._clamp(
            0.30 * SPEAKING_LOAD[state.speaking_status]
            + 0.20 * PHASE_LOAD[state.instructional_phase]
            + 0.20 * AVAILABILITY_LOAD[state.availability]
            + 0.15 * self._clamp(state.intervention_density)
            + 0.15 * self._clamp(state.interruption_cost)
        )
        return self._clamp(
            (1.0 - cognitive_load) * (1.0 - self._clamp(state.intervention_density))
        )

    def resolve_presentation(
        self,
        decision: InterventionDecision,
        state: AttentionState,
        context_confidence: float = 1.0,
    ) -> Optional[PresentationMode]:
        if decision.suppressed:
            return None
        if decision.level is InterventionLevel.L4:
            return PresentationMode.EMERGENCY

        budget = self.attention_budget(state)
        candidates = [
            PresentationMode.PASSIVE,
            PresentationMode.BADGE,
            PresentationMode.SIDEBAR,
            PresentationMode.CARD,
            PresentationMode.INLINE,
        ]
        if state.speaking_status is SpeakingStatus.SPEAKING:
            candidates.remove(PresentationMode.INLINE)
        if context_confidence < 0.80:
            candidates.remove(PresentationMode.INLINE)

        for mode in candidates:
            cost = PRESENTATION_COST[mode] * (1.0 + self._clamp(state.cognitive_load_estimate))
            if cost <= budget:
                return mode
        return None

    def create_assistance(
        self,
        decision: InterventionDecision,
        state: AttentionState,
        context_confidence: float = 1.0,
    ) -> Optional[Assistance]:
        mode = self.resolve_presentation(decision, state, context_confidence)
        if mode is None:
            return None
        return Assistance(
            id=f"assistance-{decision.id}",
            intervention_id=decision.id,
            level=decision.level,
            priority=self._priority(decision.level),
            presentation_mode=mode,
            status=AssistanceStatus.PRESENTED,
            message=decision.message,
            confidence=self._decision_confidence(decision),
        )

    @staticmethod
    def _priority(level: InterventionLevel) -> str:
        return {
            InterventionLevel.L0: "BACKGROUND",
            InterventionLevel.L1: "LOW",
            InterventionLevel.L2: "NORMAL",
            InterventionLevel.L3: "HIGH",
            InterventionLevel.L4: "CRITICAL",
        }[level]

    @staticmethod
    def _decision_confidence(decision: InterventionDecision) -> float:
        marker = "confidence="
        start = decision.rationale.find(marker)
        if start < 0:
            return 0.0
        try:
            return float(decision.rationale[start + len(marker):].split(";", 1)[0])
        except ValueError:
            return 0.0

    def apply_action(
        self,
        assistance: Assistance,
        action: TeacherAction,
        action_id: str,
        modified_content: Optional[str] = None,
        correction_scope: str = "OTHER",
    ) -> tuple[Assistance, TeacherActionRecord]:
        if assistance.status in {
            AssistanceStatus.DISMISSED,
            AssistanceStatus.CORRECTED,
            AssistanceStatus.EXPIRED,
            AssistanceStatus.RESOLVED,
        }:
            raise ValueError("Cannot transition a terminal assistance state")

        target = {
            TeacherAction.ACKNOWLEDGE: AssistanceStatus.ACKNOWLEDGED,
            TeacherAction.ACCEPT: AssistanceStatus.ACCEPTED,
            TeacherAction.DISMISS: AssistanceStatus.DISMISSED,
            TeacherAction.DEFER: AssistanceStatus.DEFERRED,
            TeacherAction.MODIFY: AssistanceStatus.MODIFIED,
            TeacherAction.CORRECT: AssistanceStatus.CORRECTED,
            TeacherAction.ASK: AssistanceStatus.FOLLOW_UP,
        }[action]

        if action is TeacherAction.MODIFY and not modified_content:
            raise ValueError("MODIFY requires modified_content")
        if action is TeacherAction.CORRECT and not modified_content:
            raise ValueError("CORRECT requires corrected content")

        correction = None
        if action is TeacherAction.CORRECT:
            correction = TeacherCorrection(
                id=f"correction-{action_id}",
                assistance_id=assistance.id,
                corrected_content=modified_content or "",
                correction_scope=correction_scope,
            )

        updated = Assistance(
            id=assistance.id,
            intervention_id=assistance.intervention_id,
            level=assistance.level,
            priority=assistance.priority,
            presentation_mode=assistance.presentation_mode,
            status=target,
            message=modified_content if action is TeacherAction.MODIFY else assistance.message,
            confidence=assistance.confidence,
        )
        return updated, TeacherActionRecord(
            id=action_id,
            assistance_id=assistance.id,
            action=action,
            modified_content=modified_content,
            correction=correction,
        )
