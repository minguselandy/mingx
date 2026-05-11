# P45 API-Generated Bridge Calibration Data

This optional scaffold prepares API-assisted calibration rows for the P45
one-stratum bridge calibration lane. It is dry-run by default and does not run a
live API unless the operator enables both required environment flags and
supplies an approved live config.

The scaffold may use a strong model to generate task packets, utility scores,
and adjudication. It must not use a judge or reviewer to invent log-loss.
`delta_logloss` is accepted only when it comes from measured fixed-model
logprobs.

## Default Dry Run

Canonical dry-run config:

```text
configs/runs/bridge-data-generation-bio-attribute.json
```

Dry-run command:

```bash
uv run python -m cps.experiments.bridge_data_generation \
  --config configs/runs/bridge-data-generation-bio-attribute.json \
  --output-dir artifacts/experiments/bridge_data_generation_bio_attribute
```

Dry-run mode writes planned task/prompt/schema artifacts and an empty accepted
P45 input file. It does not call provider functions, does not open sockets, and
does not create calibration evidence.

## Live Gates

Live generation is opt-in only. The run must use:

```text
mode = live_operator_approved
CPS_ALLOW_LIVE_API=1
P45_ALLOW_API_DATA_GENERATION=1
operator_approval = true
```

The operator config must also provide non-empty identifiers for:

- `provider_profile`
- `fixed_model_id`
- `strong_review_model_id`

Provider secrets and concrete live endpoints do not belong in the run config.

The provider-profile runner constructs the three live callables required by the
scaffold:

- fixed-model log-loss scorer
- strong utility reviewer
- adjudicator

The fixed-model scorer requests `logprobs=true`, requires non-empty finite
token logprobs, rejects all-zero degenerate logprobs, and recomputes:

```text
loss_without = -sum token_logprobs(target_answer | question, L)
loss_with = -sum token_logprobs(target_answer | question, L union A)
delta_logloss = loss_without - loss_with
```

The scorer also requires the provider response to replay the target answer
exactly. If the provider does not provide usable measured logprobs, the row is
marked unusable and is excluded from the accepted P45 JSONL.

## Secure Local Config

Use the checked-in example only as a template:

```text
configs/local/bridge-data-generation-live-template.example.json
```

For a future live smoke, copy it to an operator-local config such as:

```text
configs/local/bridge-data-generation-live.local.json
```

The local copy must remain untracked. It may contain provider profile names and
model identifiers, but it must not contain API key values. Credential CSV files,
`.env` files, and local live configs must stay outside tracked Git content.

Set live gates in the operator shell before running any live generation:

```powershell
$env:CPS_ALLOW_LIVE_API = "1"
$env:P45_ALLOW_API_DATA_GENERATION = "1"
```

Set provider credentials separately through the provider wrapper's local
environment variables or local secret loader. Never paste credential values into
the run config, docs, generated artifacts, test fixtures, or issue comments.

If the operator has a local provider credential CSV, generate an ignored
`.env.local` from it rather than pasting the key into tracked files. The P45
provider preflight reads `.env.local` and `.env` locally, but it reports only
env-var names and pass/fail status. It must not print API key values.

## Live Preflight Checklist

Before a live smoke, verify all of the following without printing secret values:

- Credential file exists on the operator machine.
- Credential file is not tracked by Git.
- Credential file is ignored by `.gitignore` or `.git/info/exclude`.
- `CPS_ALLOW_LIVE_API=1` is set in the current shell.
- `P45_ALLOW_API_DATA_GENERATION=1` is set in the current shell.
- Local config uses `mode = live_operator_approved`.
- Local config uses `operator_approval = true`.
- `provider_profile` is set to the intended provider wrapper.
- `fixed_model_id` names a fixed model with actual logprob/log-loss support.
- `strong_review_model_id` names the reviewer/adjudicator model.
- Output directory is unique for this smoke run.
- The operator accepts that generated rows are pilot engineering data unless a
  later claim gate explicitly promotes them.

The preflight command validates these gates and provider capability metadata
without calling the provider:

```bash
uv run python -m cps.experiments.bridge_data_generation \
  --config configs/local/bridge-data-generation-live.local.json \
  --preflight-only
```

The preflight output is redacted: it reports env-var names and pass/fail status,
not secret values.

## Task Packet Shape

Each task packet contains:

```json
{
  "task_id": "OPERATOR_OR_API_FILL_TASK_ID",
  "question": "OPERATOR_OR_API_FILL_QUESTION",
  "target_answer": "OPERATOR_OR_API_FILL_TARGET_ANSWER",
  "gold_facts": ["OPERATOR_OR_API_FILL_GOLD_FACT"],
  "candidate_findings": ["OPERATOR_OR_API_FILL_CANDIDATE_FINDING"],
  "evidence_strength_band": "partial_constraint",
  "baseline_context": "OPERATOR_OR_API_FILL_BASELINE_CONTEXT_L",
  "added_block": "OPERATOR_OR_API_FILL_ADDED_BLOCK_A"
}
```

The baseline context is `L`. The added block is `A`.

## P45b Bridge-Canary Redesign

The first authorized API live smoke proved that measured logprobs could be
collected, but the bridge failed its thresholds. The accepted rows had saturated
utility deltas, tiny `delta_logloss` values, and one positive-utility row with
negative `delta_logloss`. That failure remains `operational_utility_only`; it
is not upgraded by this redesign.

P45b adds a deterministic bridge-canary task-packet mode:

```json
{
  "task_packet_mode": "bridge_canary_v2",
  "sample_limit": 8
}
```

The redesigned packets follow these rules:

- `baseline_context` is clearly insufficient to infer `target_answer`.
- `added_block` is the controlled intervention.
- `target_answer` uses low-prior operator-coded bio-attribute strings rather
  than common city, person, date, or generic attribute answers.
- The question avoids leaking the exact target string.
- `materialization_policy` remains `fixed_order_v1`.
- `block_size` remains `1`.

Each packet carries one of these evidence-strength bands:

- `irrelevant`
- `weak_hint`
- `partial_constraint`
- `strong_clue`
- `explicit_answer`

The 8-row canary intentionally varies those bands to reduce utility saturation.
The bands are design metadata; they are not measured utility or log-loss.

## Fixed-Model Log-Loss Boundary

For each task packet, measure the fixed model twice:

```text
loss_without = -log P(target_answer | question, L)
loss_with = -log P(target_answer | question, L union A)
delta_logloss = loss_without - loss_with
```

Accepted log-loss rows must have:

```text
logprob_available = true
logloss_source = measured_logprob
```

Rows are unusable for bridge calibration when logprobs are missing, empty,
degenerate all-zero, non-finite, unavailable, or marked as anything other than
`measured_logprob`. The scaffold recomputes `delta_logloss` from measured
`loss_without` and `loss_with`; it never accepts judge-estimated log-loss.

## Strong Review And Adjudication

The strong reviewer may provide:

- `utility_without`
- `utility_with`
- `delta_utility`
- `utility_rationale`
- `sufficiency_rationale`
- `evidence_strength_band`

The reviewer prompt requires a `0.00` to `1.00` evidence-sufficiency rubric:

- `0.00`: no support
- `0.25`: weak clue only
- `0.50`: partial constraint
- `0.75`: strong but ambiguous
- `1.00`: exact target entailed

The reviewer must ignore world knowledge and score only the supplied baseline
context and added block. The scaffold recomputes `delta_utility` as
`utility_with - utility_without` and rejects reviewer outputs that try to
provide `delta_logloss`, `loss_without`, `loss_with`, or any log-loss source.

Review artifacts preserve:

- `utility_without`
- `utility_with`
- `delta_utility`
- `utility_rationale`
- `evidence_strength_band`

Adjudication must return:

- `review_status`: `accepted`, `rejected`, or `ambiguous`
- `target_clear`
- `intervention_valid`
- `no_leakage`
- `no_duplicate_trivial_case`
- `utility_score_consistent`

Only `accepted` rows with every adjudication boolean set to true are exported to
the P45 input JSONL. `rejected` and `ambiguous` rows remain in review artifacts
and are excluded from bridge calibration.

## P45 Export

Accepted rows are exported as P45 calibration rows with:

```text
source = operator_provided
data_origin = api_generated
delta_utility_source = strong_model_adjudicated
delta_logloss_source = measured_logprob
review_status = accepted
```

The exported file is:

```text
accepted_bridge_calibration_pairs.jsonl
```

The row is still operator-provided data in the P45 sense because an approved
operator config and explicit live gates are required before live API generation.

## Handoff To P45 Calibration

Before artifact generation, validate accepted rows:

```bash
uv run python -m cps.experiments.bridge_calibration \
  --config configs/runs/bridge-calibration-one-stratum.json \
  --input artifacts/experiments/bridge_data_generation_bio_attribute/accepted_bridge_calibration_pairs.jsonl \
  --dry-validate
```

Only after dry validation passes should the operator generate bridge artifacts:

```bash
uv run python -m cps.experiments.bridge_calibration \
  --config configs/runs/bridge-calibration-one-stratum.json \
  --input artifacts/experiments/bridge_data_generation_bio_attribute/accepted_bridge_calibration_pairs.jsonl \
  --output-dir artifacts/experiments/bridge_calibration_one_stratum_operator
```

For a future authorized live smoke, pass the local live config and explicit task
packet file to the provider-profile runner:

```bash
uv run python -m cps.experiments.bridge_data_generation \
  --config configs/local/bridge-data-generation-live.local.json \
  --task-packets path/to/operator_task_packets.jsonl \
  --use-live-provider-profile
```

Live provider mode refuses placeholder task packets. Use at most `10` task
packets for the initial smoke. Run P45 `--dry-validate` on
`accepted_bridge_calibration_pairs.jsonl` before generating bridge artifacts.

## Low-Signal Rows

P45b does not relax bridge thresholds. It adds a stricter configured signal
screen:

```json
{
  "minimum_abs_delta_logloss_for_bridge_evidence": 0.001
}
```

Rows with `abs(delta_logloss)` below that threshold are marked
`bridge_uninformative` with reason code
`delta_logloss_below_informative_threshold`. Rows with `delta_logloss < 0` are
reported with reason code `negative_delta_logloss` in data-generation review
artifacts. These rows are not silently treated as strong bridge evidence.

## Claim Boundary

This scaffold does not create human labels, kappa, contamination closure,
scientific validation, deployed V-information verification, or
`measurement_validated`.

Successful downstream bridge calibration can support only
`calibrated_proxy_supported` for the active stratum. Weak, invalid, or failed
bridge evidence must downgrade to `operational_utility_only` or
`ambiguous_metric`.
