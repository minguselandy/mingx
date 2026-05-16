# P61R Public Benchmark Adapters

## P61R-A purpose

P61R-A adds the FEVER-first public benchmark adapter and the shared
candidate-pool schema for Route 2. The output is deterministic benchmark
instances and candidate pools that can be reviewed before P62R starts.

## Adapter status

The adapter accepts local/offline FEVER-style JSONL files. It reads claim rows,
optional local candidate rows, positive evidence text when available, and
explicit distractors when provided locally. If required local files are absent
or no valid candidate pools can be produced, it emits a blocked-data report
instead of fake benchmark rows.

Route-control revision after P61R-A pauses FEVER as bridge-primary because the
complete wiki/evidence source is not available locally. FEVER code remains
available as an adapter, but the controlled bridge-primary target is now
HotpotQA with `task_family = hotpotqa_answer_support_selection`.

The HotpotQA adapter accepts local/offline official-style rows with `_id`,
`question`, `answer`, `supporting_facts`, and `context`. It builds
sentence-level packets from provided context, marks supporting facts as
`gold_supporting`, marks non-supporting context sentences as
`same_context_distractor`, and fails closed when real local HotpotQA input is
absent or invalid.

## CandidatePool schema summary

Each benchmark instance uses `benchmark_instance_v1` and contains a target plus
a candidate pool. FEVER uses a classification label target. HotpotQA uses an
answer-string target. Each evidence packet records a stable `packet_id`,
`source_doc_id`, sentence span, content, `token_cost`, `gold_support_label`,
provenance, and packet hash. Candidate pools record candidate counts, total
token cost, gold evidence reachability for budgets `256`, `512`, and `1024`,
and a stable `candidate_pool_hash`.

## Determinism and hash policy

Canonical JSON uses sorted keys, compact separators, and UTF-8 SHA-256 hashes.
Packet hashes exclude the packet `hash` field. Candidate-pool hashes are
computed from sorted packet payloads and derived pool metadata while excluding
the `candidate_pool_hash` self-reference. No timestamps, UUIDs, absolute local
paths, or nondeterministic ordering are introduced.

## Data availability status

No real FEVER local mirror is committed with this phase. The committed artifact
`artifacts/benchmarks/p61r_blocked_data_report.json` records the default
blocked-data behavior for missing local input. Small fixtures exist only in
focused tests and are not paper evidence.

No real HotpotQA local mirror is committed with this revision. Missing local
HotpotQA input must produce a blocked report rather than benchmark artifacts
from fixtures.

## Claim boundary

P61R-A does not generate P55 rows. P61R-A does not repair P55 blocked state.
P61R-A does not generate P56 traces. P61R-A does not repair P56 no-trace state.
no metric bridge support, measurement validation, or paper evidence claim is introduced.
`calibrated_proxy_supported` and `vinfo_proxy_supported` remain denied for this
adapter-only phase unless a later reviewed bridge package establishes them for a
matching active stratum.

Forbidden claim upgrades remain denied here:

- Denied: `measurement_validated`.
- Denied: human-label validation.
- Denied: human-human kappa.
- Denied: deployed V-information verification.
- Denied: global calibrated proxy support.
- Denied: global V-information proxy support.
- Denied: P55 unblocked.
- Denied: P56 unblocked.

Next phase: P62R FEVER bridge row generator.
Current bridge-primary next step: P62R HotpotQA row generation only after real
HotpotQA candidate pools and evaluator/log-loss delta records exist.
