# Reviewer Defense: Live-API Operational Paper

Status: POST-8 reviewer package
Claim ceiling: `operational_utility_only/no_claim_upgrade`

This document answers likely reviewer questions while preserving the
operational-only boundary. It does not run experiments, add evidence, or change
claim status.

## Why no fixed-target NLL bridge?

The deployed live API exposes generated-token chat logprobs, not fixed-target
teacher-forced NLL over a predetermined continuation under a fixed
materialization policy. We do not relabel generated-token chat logprobs as
teacher-forced NLL. Without the fixed-target scoring surface, the metric bridge
fails closed and cannot support calibrated proxy support, V-information proxy
support, measurement validation, Route 5 unlock, or Route 8 unlock.

## Why mention V-information?

V-information is the formal motivation for dispatch-time evidence selection.
It states the target that the theory would optimize under its assumptions. The
submission does not claim V-information verification. It separates the formal
objective from backend-constrained operational diagnostics and marks the
deployed evidence package as `operational_utility_only/no_claim_upgrade`.

## Why use LLM judges?

LLM judges are weak-source operational diagnostics. They can reveal
disagreement, order sensitivity, parse failures, sufficiency failures,
abstention behavior, and extraction risks at scale. They are not human labels,
external gold labels, human-human agreement, judge validation, or measurement
validation. Any judge-based result must stay candidate-only unless a later
approved route supplies stronger evidence and passes its own review.

## Why not claim selector superiority?

The available operational replay is scoped to particular datasets, candidate
pools, budgets, baselines, prompts, and model snapshots. That can support a
scoped operational comparison under matched budgets. It does not establish
selector superiority, global selector superiority, metric bridge support,
measurement validation, or V-information verification.

## Why is this not just another RAG compressor?

The contribution is not a generic compression benchmark. The paper frames
dispatch-time evidence selection as a claim-gated audit problem: what evidence
can be selected, replayed, traced, and bounded under backend constraints. The
submission emphasizes formal motivation, fail-closed bridge gates, replayable
artifact interfaces, sufficiency and abstention diagnostics, reprojection
witnesses, and explicit non-claims.

## What does live-API-only constraint contribute scientifically?

The live-API-only constraint makes the backend limitation observable. It shows
what a deployed system can actually expose, which artifacts can be replayed,
and where claims must stop when fixed-target scoring, human/external gold
labels, or bridge calibration are unavailable. The scientific contribution is
the fail-closed boundary and the reproducible operational audit surface, not a
claim that live API diagnostics validate the metric.

## Why are EPF-FINAL silver labels candidate-only?

EPF-FINAL silver labels are LLM-generated/model-adjudicated candidate evidence.
They are not human labels, external gold labels, human-human kappa, or
measurement validation. They can help organize reviewable candidate packages,
but they cannot unlock Route 5, unlock Route 8, establish paper evidence, or
turn generated-token chat logprobs into teacher-forced NLL.

## Why are Route 5 and Route 8 still locked?

Route 5 remains locked because the fixed-target continuation scoring and
accepted metric-bridge requirements are absent. Route 8 remains locked because
the integration package has no accepted evidence route that would justify a
paper-evidence or measurement-validation upgrade. Route 5 locked: yes. Route 8
locked: yes.

## Required Submission Stance

- We do not relabel generated-token chat logprobs as teacher-forced NLL.
- We do not claim V-information verification.
- We do not claim measurement validation.
- The contribution is a fail-closed, replayable, claim-gated operational audit
  framework for dispatch-time evidence selection.

## Denied Claims Checklist

- metric bridge support: denied
- calibrated proxy support: denied
- V-information proxy support: denied
- measurement validation: denied
- paper evidence: denied
- selector superiority: denied
- global selector superiority: denied
- Route 5 unlock: denied
- Route 8 unlock: denied
- raw API responses stored: no
