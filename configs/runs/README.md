# Run Plans

This directory stores canonical project-level run plans.

These files define:

- input manifest and hash sources
- backend role and scoring scope
- calibration scope
- output storage roots

They are not run outputs themselves. Real outputs still land under
`artifacts/`.

Canonical runtime package:

- `python -m cps.runtime.phase1_smoke`
- `python -m cps.runtime.cohort`

Current recommended run plans:

- Protocol-full targets:
  [cohort.json](./cohort.json),
  [protocol-full-mock.json](./protocol-full-mock.json),
  [protocol-full-live.json](./protocol-full-live.json)
- Reduced-scope pilot configs:
  [smoke.json](./smoke.json),
  [live-pilot.json](./live-pilot.json),
  [live-mini-batch.json](./live-mini-batch.json),
  [live-calibration-p2.json](./live-calibration-p2.json),
  [live-calibration-p3.json](./live-calibration-p3.json)

Interpretation rules:

- `scope_mode = protocol_full` means the config is intended to satisfy the scientific Phase 1 scope.
- `scope_mode = pilot_reduced_scope` means the config is engineering/pilot only and must not be used as a Phase 2 statistical input.
- Current `live-*` configs use reduced scope, including `question_paragraph_limit = 5` and calibration `per_hop_count` values of `1`, `2`, or `3`.
