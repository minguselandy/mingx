# Provider Adapters

## Purpose

P08 adds pure conversion helpers that normalize external-style memory and extraction records into native CPS candidate payloads. These adapters are offline utilities for candidate preparation and replay experiments.

They do not call providers, create network clients, require credentials, or alter live cohort defaults.

## Native candidate payload

Adapter outputs include:

- `candidate_id`
- `source_id`
- `source_type`
- `content`
- `token_cost`
- `provenance`
- `metadata`
- `content_hash`

Optional fields include `source_offsets`, `temporal_validity`, `confidence`, `extraction_type`, `synthetic_source`, and `provider`.

`content_hash` and fallback `candidate_id` values are deterministic. If a caller does not provide `token_cost`, the adapters use a deterministic stdlib token-like split. No external tokenizer is required.

## Provider candidate normalization

`cps.providers.normalizer` provides a deterministic compatibility layer for downstream selector and materializer paths that still expect legacy item fields. It harmonizes aliases between `candidate_id` and `item_id`, `content` and `text`, and `token_cost` and `token_estimate` without mutating the input payload or changing provider provenance.

This layer is engineering compatibility only. It does not validate measurement, certify V-information, certify submodularity, certify metric bridge freshness, certify deployment claims, change conservative claim gates, or unblock P04 or P09.

## Graphiti-style adapter

`cps.providers.graphiti_provider` converts fake or local Graphiti-style dicts, dataclasses, and attribute objects into CPS candidates:

- facts become `source_type: graphiti_fact`
- episodes become `source_type: graphiti_episode`
- generic records become `source_type: graphiti_record`

The adapter defensively reads common fields such as `uuid`, `id`, `name`, `content`, `summary`, `source`, `episode_id`, temporal validity fields, and `confidence`.

## LangExtract-style adapter

`cps.providers.langextract_provider` converts fake or local LangExtract-style dicts, dataclasses, and attribute objects into CPS candidates:

- spans become `source_type: langextract_span`
- extractions become `source_type: langextract_extraction`
- generic records become `source_type: langextract_record`

The adapter preserves document IDs, character offsets, labels or extraction types, confidence, attributes, and metadata when present.

## Dependency policy

Graphiti and LangExtract are not required dependencies. P08 adapter modules do not import either package, even lazily. Tests use fake/local objects only.

Local ZIP references under `reference/` are read-only design material. They must not be imported, copied, executed, vendored, committed, or treated as required dependencies.

## Scientific boundary

Provider adapter output is a candidate-conversion artifact only. It does not certify deployed V-information weak submodularity, validate measurement, replace human labels, compute kappa, validate bridge freshness, or upgrade any result to `measurement_validated`.

P04 scientific closure remains deferred and operator-required. Contamination, annotation, kappa, and bridge gates are unchanged.
