from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from .m4 import Finding, FindingType, Status
from .m3 import InterventionLevel, Severity, TeachingState
class TeacherResponse(str,Enum): ACCEPTED="accepted"; REJECTED="rejected"; DISMISSED="dismissed"; DEFERRED="deferred"; MODIFIED="modified"; CORRECTED="corrected_by_teacher"; NONE="no_response"
@dataclass(frozen=True)
class InterventionDecision:
    id:str; finding_id:str; level:InterventionLevel; message:str; rationale:str; suppressed:bool=False
class PolicyEngine:
    def decide(self,state:TeachingState,f:Finding)->InterventionDecision:
        c=max(0.0,min(1.0,f.confidence)); ctx=f"confidence={c:.2f}; severity={f.severity.value}; repetitions={f.repetitions}; immediate_risk={f.immediate_risk}; knowledge_risk={f.knowledge_risk}; state_version={state.version}"
        if f.status is not Status.OPEN: level=InterventionLevel.L0; sup=True; reason="Finding is resolved/dismissed; no active intervention. "+ctx
        elif f.repetitions>=3: level=InterventionLevel.L0; sup=True; reason="Repeated finding suppressed for anti-fatigue. "+ctx
        elif c<.80: level=InterventionLevel.L0 if c<.50 else InterventionLevel.L2; sup=False; reason="Confidence below high-intensity threshold. "+ctx
        elif f.severity is Severity.CRITICAL and c>=.90 and (f.immediate_risk or f.knowledge_risk): level=InterventionLevel.L4; sup=False; reason="Critical immediate welfare/knowledge-integrity risk meets L4 gate. "+ctx
        elif f.severity in (Severity.MODERATE,Severity.SIGNIFICANT): level=InterventionLevel.L3; sup=False; reason="Proportional prompt selected as lowest effective level for meaningful finding. "+ctx
        else: level=InterventionLevel.L2; sup=False; reason="Low-disruption signal selected. "+ctx
        return InterventionDecision("decision-"+f.id,f.id,level,f.message,reason,sup)
