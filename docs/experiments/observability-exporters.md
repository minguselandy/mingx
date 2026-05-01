# Observability Exporters

## Purpose

The P07 exporters map `ProjectionBundleV1` records into local observability payloads for later integration work. They are dry-run helpers for inspecting dispatch identity, bundle hashes, budget fields, selector diagnostics, and conservative metric claim metadata.

These exporters do not send telemetry, contact external services, or validate scientific claims.

## Dry-run default

All P07 exporters return deterministic Python dictionaries. They do not import OpenTelemetry, Langfuse, Phoenix, or any other observability package at module import time.

Implemented mappings:

- `cps.export.projection_bundle_to_otel_span(...)`
- `cps.export.projection_bundle_to_langfuse_payload(...)`
- `cps.export.export_projection_bundle_to_langfuse(..., dry_run=True)`
- `cps.export.projection_bundle_to_phoenix_payload(...)`

`export_projection_bundle_to_langfuse(..., dry_run=False, client=None)` fails closed with a clear `RuntimeError`. Network-capable clients are out of scope for P07.

## Field mapping

The common mapper includes stable, JSON-safe fields:

- bundle version
- run, dispatch, agent, and round identity
- source mode
- `ProjectionBundleV1` canonical hash
- candidate and selected counts
- selected IDs
- budget, estimated-token, realized-token, and within-budget fields
- materialized context hash
- metric class and diagnostic claim level
- selector regime label and selector action when diagnostics are present
- optional contamination, annotation, kappa, and bridge status fields when present

Full rendered context is excluded by default. `include_payload_preview=True` adds bounded deterministic previews only.

## Payload shapes

The OTel-style mapping returns a local span dictionary with `name`, `kind`, `trace_id`, `span_id`, `attributes`, and local event metadata.

The Langfuse-style mapping returns a dry-run trace and observation dictionary. It is suitable for comparing future integration shapes without creating traces or observations in any external service.

The Phoenix-style mapping returns `trace_id`, `span_id`, `span_name`, `attributes`, and evaluation-like local metadata. It does not import or call Phoenix.

## Optional dependency policy

Observability packages are not dependencies of mingx. Future integrations may add adapter layers or operator-installed optional packages, but P07 payload generation must remain dependency-free and local.

## Claim boundaries

Exporter payloads are operational observability artifacts only. They do not certify deployed V-information weak submodularity, do not validate bridge freshness, do not replace annotation or kappa evidence, and do not upgrade any run to `measurement_validated`.

P04 scientific closure remains deferred and operator-required. Contamination, annotation, kappa, and bridge gates are unchanged.

## Local references

`reference/langfuse-main` may exist as a ZIP-extracted read-only design reference. It must not be imported, copied, executed, vendored, committed, or treated as a required dependency.

## Future work

A future phase may add a dry-run JSONL conversion CLI, for example converting `projection_bundles.jsonl` into OTel-style or Langfuse-style payload JSONL. P07 intentionally does not add a CLI to keep this phase limited to pure mapping functions and tests.
