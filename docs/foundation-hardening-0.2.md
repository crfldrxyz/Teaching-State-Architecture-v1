# TSA Foundation Hardening v0.2

## Scope

This milestone hardens the deterministic boundary between M3, M4, M5, M6, and M7 before the end-to-end replay harness is built.

## Cross-layer contract

M3 represents state transitions. M4 creates findings. M5 authorizes intervention intensity. M6 determines delivery under attention constraints. M7 evaluates outcomes and proposes controlled improvements.

The authorization boundary is strict:

```text
M4 Finding
  -> M5 InterventionDecision
  -> M6 Assistance
  -> TeacherAction
  -> M7 Evaluation
```

M6 must never increase an M5 level or unsuppress an M5 decision.

## M5 hardening

The policy engine now records confidence, severity, evidence strength, persistence, recoverability, relevance, disruption cost, intervention density, repetition, and risk context in its rationale.

L4 requires all of:

- critical severity;
- confidence >= 0.90;
- evidence strength >= 0.80;
- relevance >= 0.70;
- immediate welfare or knowledge-integrity risk;
- disruption cost <= 0.30.

Confidence below 0.80 cannot produce L3 or L4.
Repeated findings at three or more occurrences are suppressed.
Resolved or dismissed findings are suppressed.

## M6 hardening

M6 now contains deterministic attention-budget and presentation resolution logic for PASSIVE, BADGE, SIDEBAR, CARD, INLINE, and EMERGENCY.

High speaking load removes INLINE delivery. L4 uses EMERGENCY only because M5 already authorized L4.

Teacher controls produce immutable action records. CORRECT additionally produces a structured TeacherCorrection for M7.

## M7 hardening

M7 evaluates proportionality against policy ceilings, attributes known evaluation failures, and creates proposals with an offline validation plan. M7 has no production-policy mutation operation.

## Event correlation

`TSAEvent` provides a common correlation envelope with session, state version, source layer, correlation ID, causation ID, and payload reference.

## Testing

The repository includes M5/M6 invariant tests and realistic classroom simulations covering:

1. minor topic drift during an active objective;
2. factual/conceptual error during high teacher speaking load;
3. critical knowledge-integrity risk;
4. teacher correction;
5. suppression and delivery boundaries;
6. immutable event identity.

The next milestone is the deterministic M0-M7 replay harness using these scenarios.
