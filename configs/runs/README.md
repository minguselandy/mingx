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

- [smoke.json](./smoke.json)
- [cohort.json](./cohort.json)
- [live-pilot.json](./live-pilot.json)
- [live-mini-batch.json](./live-mini-batch.json)
- [live-calibration-p2.json](./live-calibration-p2.json)
- [live-calibration-p3.json](./live-calibration-p3.json)
