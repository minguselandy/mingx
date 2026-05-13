# P61R Public Benchmark Adapters

## P61R-A purpose

P61R-A adds the FEVER-first public benchmark adapter and the shared
candidate-pool schema for Route 2. The output is deterministic benchmark
instances and candidate pools that can be reviewed before P62R starts.

## FEVER-first adapter status

The adapter accepts local/offline FEVER-style JSONL files. It reads claim rows,
optional local candidate rows, positive evidence text when available, and
explicit distractors when provided locally. If required local files are absent
or no valid candidate pools can be produced, it emits a blocked-data report
instead of fake benchmark rows.

## CandidatePool schema summary

Each benchmark instance uses `benchmark_instance_v1` and contains a FEVER
classification target plus a candidate pool. Each evidence packet records a
stable `packet_id`, `source_doc_id`, sentence span, content, `token_cost`,
`gold_support_label`, provenance, and packet hash. Candidate pools record
candidate counts, total token cost, gold evidence reachability for budgets
`256`, `512`, and `1024`, and a stable `candidate_pool_hash`.

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
