from __future__ import annotations
from dataclasses import dataclass, field, replace
from enum import Enum
from typing import Optional

class Severity(str, Enum):
    INFORMATIONAL="informational"; MINOR="minor"; MODERATE="moderate"; SIGNIFICANT="significant"; CRITICAL="critical"
class InterventionLevel(int, Enum): L0=0; L1=1; L2=2; L3=3; L4=4
class EventType(str, Enum): STATEMENT="teacher_statement"; QUESTION="teacher_question"; RESPONSE="student_response"; TOPIC="topic_transition"; OBJECTIVE="objective_transition"; CONCEPT="concept_introduction"; CLAIM="claim"; CORRECTION="correction"; ASSESSMENT="assessment"
@dataclass(frozen=True)
class InstructionalEvent:
    id:str; timestamp:float; type:EventType; content:str=""; confidence:float=1.0
@dataclass(frozen=True)
class TeachingState:
    session_id:str; version:int=0; topic:Optional[str]=None; objective:Optional[str]=None; concepts:tuple[str,...]=(); claims:tuple[str,...]=(); unresolved:tuple[str,...]=(); last_timestamp:float=0.0
class StateEngine:
    def __init__(self, initial:TeachingState): self._state=initial; self._events:dict[str,InstructionalEvent]={}
    @property
    def state(self)->TeachingState: return self._state
    def apply(self,event:InstructionalEvent)->TeachingState:
        if event.id in self._events:return self._state
        s=self._state
        kw={"version":s.version+1,"last_timestamp":max(s.last_timestamp,event.timestamp)}
        if event.type is EventType.TOPIC: kw["topic"]=event.content
        elif event.type is EventType.OBJECTIVE: kw["objective"]=event.content
        elif event.type is EventType.CONCEPT and event.content not in s.concepts: kw["concepts"]=s.concepts+(event.content,)
        elif event.type is EventType.CLAIM and event.content not in s.claims: kw["claims"]=s.claims+(event.content,)
        elif event.type is EventType.CORRECTION and event.content in s.unresolved: kw["unresolved"]=tuple(x for x in s.unresolved if x!=event.content)
        self._events[event.id]=event; self._state=replace(s,**kw); return self._state
    def replay(self,events:list[InstructionalEvent])->TeachingState:
        for e in sorted(events,key=lambda x:(x.timestamp,x.id)):self.apply(e)
        return self._state
