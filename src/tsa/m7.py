from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from .m3 import InterventionLevel, Severity
from .m4 import Finding
from .m5 import InterventionDecision, TeacherResponse
class Result(str,Enum): CONFIRMED="confirmed"; PARTIAL="partially_confirmed"; UNCERTAIN="uncertain"; INCORRECT="incorrect"; NA="not_applicable"
class Dimension(str,Enum): ACCURACY="accuracy"; TIMING="timing"; PROPORTIONALITY="intervention_proportionality"; USEFULNESS="teacher_usefulness"; CONFIDENCE="confidence"; PRIVACY="privacy"; OUTCOME="instructional_impact"
class ErrorType(str,Enum): OBSERVATION="observation_error"; INFERENCE="inference_error"; CONTEXT="context_error"; KNOWLEDGE="knowledge_error"; SEVERITY="severity_error"; CONFIDENCE="confidence_error"; POLICY="policy_error"; TIMING="timing_error"; DELIVERY="delivery_error"; SUPPRESSION="suppression_error"; STATE="state_error"; PRIVACY="privacy_error"; UNKNOWN="outcome_unknown"
@dataclass(frozen=True)
class EvaluationEvidence: id:str; source_type:str; observation:str; confidence:float=1.0
@dataclass(frozen=True)
class Evaluation: id:str; target_id:str; dimension:Dimension; result:Result; confidence:float; evidence:tuple[EvaluationEvidence,...]; rationale:str
@dataclass(frozen=True)
class Outcome: id:str; intervention_id:str; resolution:str; instructional_effect:str; confidence:float=.0
@dataclass(frozen=True)
class ImprovementProposal: id:str; problem:str; proposed_change:str; affected_component:str; validation_plan:str; status:str="proposed"
class EvaluationEngine:
    def evaluate_decision(self,f:Finding,d:InterventionDecision)->Evaluation:
        c=f.confidence; max_allowed=InterventionLevel.L4 if f.severity is Severity.CRITICAL and c>=.90 and (f.immediate_risk or f.knowledge_risk) else (InterventionLevel.L3 if f.severity in (Severity.MODERATE,Severity.SIGNIFICANT) and c>=.80 else InterventionLevel.L2 if c>=.50 else InterventionLevel.L0)
        result=Result.CONFIRMED if d.level.value<=max_allowed.value else Result.INCORRECT
        gap=d.level.value-max_allowed.value
        rationale=f"confidence={c:.2f}; severity={f.severity.value}; selected_level={d.level.name}; maximum_policy_level={max_allowed.name}; proportionality_gap={gap}"
        return Evaluation("eval-"+d.id,d.id,Dimension.PROPORTIONALITY,result,c,(),rationale)
    def evaluate_feedback(self,d:InterventionDecision,response:TeacherResponse)->Evaluation:
        # Rejection/dismissal is not evidence that the finding was wrong.
        result=Result.UNCERTAIN if response in (TeacherResponse.REJECTED,TeacherResponse.DISMISSED) else Result.CONFIRMED
        return Evaluation("feedback-"+d.id,d.id,Dimension.USEFULNESS,result,d.level.value/4,(),f"Teacher response={response.value}; response is evaluation evidence, not automatic proof of system error.")
    def propose(self,evaluations:list[Evaluation])->tuple[ImprovementProposal,...]:
        bad=[e for e in evaluations if e.result is Result.INCORRECT]
        if not bad:return ()
        return (ImprovementProposal("proposal-1","Observed evaluation failures require review","Investigate failing cases; change only after controlled validation","policy/model/context representation","Offline replay, regression corpus, human review, then versioned deployment"),)
