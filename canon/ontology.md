# M1 — Ontology

Core entities: TeachingState, IntendedState, ObservedState, InferredState, EvaluatedState, InstructionalEvent, Objective, Concept, Claim, Drift, Mismatch, WeakPoint, Intervention, Transition.

Core epistemic distinction:
- WHAT HAPPENED? → Observation
- WHAT IS HAPPENING? → Inference
- IS IT A PROBLEM? → Evaluation
- WHAT SHOULD WE DO? → Intervention

TeachingState = Context + Intent + Observation + Inference + Evaluation + TemporalPosition.
Events are immutable and ordered; corrections are new events. Claims carry verification state and context. Drift means meaningful trajectory deviation, not automatic failure. WeakPoint describes an instructional condition, never teacher worth. Intervention is an action authorized by M5, not a finding.
