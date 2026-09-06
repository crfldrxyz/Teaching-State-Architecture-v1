# M7 — Evaluation & Continuous Improvement

M7 evaluates the system, not teacher worth. It separately evaluates observation accuracy, inference quality, finding validity, intervention proportionality, timing, delivery, outcome, privacy, and system regression.

Failure taxonomy: observation, inference, context, knowledge, severity, confidence, policy, timing, delivery, suppression, state, privacy, unknown outcome.

Continuous-learning path is strictly: evaluation → improvement proposal → human/controlled review → versioned policy/model → offline replay → regression gates → deployment → monitoring. M7 never automatically mutates production policy.

Outcome causality is not inferred from sequence alone. Say an intervention was followed by an outcome unless the evaluation design supports causal attribution.
