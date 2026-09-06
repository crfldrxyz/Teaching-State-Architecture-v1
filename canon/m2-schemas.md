# M2 — Machine Schemas

M2 is the exact serialization/validation contract for M1. Production schemas use JSON Schema Draft 2020-12, stable IDs, explicit versions, controlled vocabularies, immutable state snapshots, event envelopes, evidence references, and cross-entity IDs.

Required envelope fields: `schema_version`, `entity_type`, `id`, `created_at`.

Validation rules: confidence is 0..1; intervention levels are L0..L4; severity is controlled; timestamps are monotonic within an event stream; evidence references must resolve; state versions are monotonic; immutable historical events are never overwritten; corrections reference the item they correct.

Serialization boundary: M1 defines meaning; M2 defines machine representation and exchange.
