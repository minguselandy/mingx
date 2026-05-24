# Reviewer Defense: Live-API Operational Paper

Status: SUB-3 reviewer defense package
Claim ceiling: `operational_utility_only/no_claim_upgrade`

This document answers likely reviewer questions while preserving the operational-only boundary. It does not run experiments, add evidence, or change claim status.

## Core One-Paragraph Defense

This paper is V-information anchored, live-API-only, claim-gated, and operational audit / diagnostic in scope. It studies dispatch-time evidence projection in a live-agent setting and uses formal V-information to define the target object, while refusing to overstate what the supported live API can measure. The evidence package reports weak model-adjudicated diagnostics, sufficiency / abstention behavior, reprojection witness records, scoped replay, extraction-risk candidate evidence, and replayable artifacts under fail-closed claim gates. It is not a compression paper, router paper, validation paper, calibrated proxy paper, or selector superiority paper.

## Why no NLL bridge?

The deployed live API exposes generated-token chat logprobs, not fixed-target teacher-forced NLL over a predetermined continuation under a fixed materialization policy. We do not relabel generated-token chat logprobs as teacher-forced NLL. Without the fixed-target scoring surface, the metric bridge fails closed and cannot support calibrated proxy support, V-information proxy validation, measurement validation, Route 5 unlock, or Route 8 unlock.

## Why mention V-information?

V-information is the formal motivation for dispatch-time evidence projection. It states the target that the theory would optimize under its assumptions. The submission does not claim deployed V-information verification or V-information proxy validation. It separates the formal objective from backend-constrained operational diagnostics and marks the deployed evidence package as `operational_utility_only/no_claim_upgrade`.

## Why use LLM judges?

LLM judges are weak-source operational diagnostics. They can reveal disagreement, order sensitivity, parse failures, sufficiency failures, abstention behavior, omitted-evidence behavior, and extraction risks at scale. They are not human labels, external gold labels, human-human agreement, judge validation, or measurement validation. Any judge-based result must stay candidate-only unless a later approved route supplies stronger evidence and passes its own review.

## Why not claim selector superiority?

The available operational replay is scoped to particular datasets, candidate pools, budgets, baselines, prompts, and model snapshots. That can support a scoped operational comparison under matched budgets. It does not establish selector superiority, global selector superiority, metric bridge support, measurement validation, or V-information verification.

## Why is this not just another compressor/router?

Compression and routing papers usually optimize token efficiency, answer accuracy, or routing decisions directly. This paper studies dispatch-time evidence projection as a claim-gated audit problem: what evidence can be selected, replayed, traced, bounded, and safely interpreted under backend constraints. The submission emphasizes formal motivation, fail-closed bridge gates, replayable artifact interfaces, sufficiency and abstention diagnostics, reprojection witnesses, extraction-risk accounting, and explicit non-claims.

## What does the live-API-only constraint contribute scientifically?

The live-API-only constraint makes the backend limitation observable. It shows what a deployed system can actually expose, which artifacts can be replayed, and where claims must stop when fixed-target scoring, human/external gold labels, or bridge calibration are unavailable. The scientific contribution is the fail-closed boundary and the reproducible operational audit surface, not a claim that live API diagnostics validate the metric.

## Why are artifacts a contribution rather than just logs?

The artifacts are structured audit witnesses: they bind normalized rows, prompt and schema hashes where applicable, model/evaluator identifiers, candidate-pool or materialization context, checksums, denied-claim fields, route-lock fields, and storage-policy fields. That structure lets reviewers reproduce the audit trail, inspect why a claim gate passed or failed, and confirm that raw API responses are not stored. The artifacts remain replay/audit evidence, not validation evidence.

## Why is extraction quality separate from selector quality?

The selector operates over an extracted pool, but end-to-end task performance also depends on what the extraction gate omitted, distorted, or failed to preserve. POST-7 therefore treats extraction as a separate M-star to extracted-pool risk surface. Its value-weighted loss proxy and stratum counts are model-adjudicated extraction-risk candidate evidence only. They do not prove selector validity, measurement validation, or theorem transfer to runtime extraction behavior.

## Required Submission Stance

- The paper is V-information anchored, live-API-only, claim-gated, and operational audit / diagnostic in scope.
- We do not relabel generated-token chat logprobs as teacher-forced NLL.
- We do not claim V-information proxy validation.
- We do not claim measurement validation.
- We do not claim metric bridge support.
- We do not claim selector superiority.
- The contribution is a fail-closed, replayable, claim-gated operational audit framework for dispatch-time evidence projection.

## Denied Claims Checklist

- fixed-target teacher-forced NLL: denied
- teacher-forced scoring support: denied
- fixed-target continuation scoring support: denied
- metric bridge support: denied
- calibrated proxy support: denied
- V-information proxy validation: denied
- `vinfo_proxy_supported`: denied
- measurement validation: denied
- human/external gold validation: denied
- paper-grade evidence: denied
- selector superiority: denied
- global selector superiority: denied
- Route 5 unlock: denied
- Route 8 unlock: denied
- raw API responses stored: no
