from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from .m3 import TeachingState, Severity

class FindingType(str,Enum): DRIFT="drift"; MISMATCH="mismatch"; KNOWLEDGE="knowledge_integrity"; WEAK_POINT="weak_point"
class Status(str,Enum): OPEN="open"; RESOLVED="resolved"; DISMISSED="dismissed"
@dataclass(frozen=True)
class Evidence: id:str; source:str; excerpt:str=""; confidence:float=1.0
@dataclass(frozen=True)
class Finding:
    id:str; type:FindingType; message:str; confidence:float; severity:Severity; evidence:tuple[Evidence,...]=(); status:Status=Status.OPEN; repetitions:int=1; immediate_risk:bool=False; knowledge_risk:bool=False
class DetectionEngine:
    def detect(self,state:TeachingState)->tuple[Finding,...]:
        out=[]
        if state.unresolved:
            out.append(Finding("weak-"+str(state.version),FindingType.WEAK_POINT,"Unresolved instructional item remains active",.88,Severity.MODERATE,()))
        return tuple(out)
