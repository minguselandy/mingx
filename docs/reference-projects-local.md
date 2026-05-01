# Local Reference Projects

## Purpose

`reference/` contains local ZIP-extracted external repositories used only for architecture study, adapter design, and baseline inspiration. These references are local research material for future phases and are not part of the mingx source tree or dependency set.

## Policy

- `reference/` is read-only research material.
- `reference/` must not be committed.
- No external source code should be copied into mingx without license review.
- Scripts under `reference/` must not be executed.
- Dependencies from reference projects must not be installed automatically.
- Commit SHA may be unavailable because these are ZIP archive extractions.

## Project index

| Project | Local folder | Original URL | Source type | Commit SHA | Role for mingx | Inspect first | Do not copy |
| --- | --- | --- | --- | --- | --- | --- | --- |
| LangGraph | `reference/langgraph-main/langgraph-main/` | `https://github.com/langchain-ai/langgraph` | zip archive extraction | unavailable | Runtime dispatch boundary, stateful graph execution, checkpoint/replay reference. | `README.md`, `docs/`, `examples/`, `libs/` | Runtime source, graph engine code, checkpoint implementation, package metadata, scripts. |
| Graphiti | `reference/graphiti-main/graphiti-main/` | `https://github.com/getzep/graphiti` | zip archive extraction | unavailable | Provenance-rich temporal context graph and candidate provider reference. | `README.md`, `examples/`, `graphiti_core/`, `mcp_server/`, `OTEL_TRACING.md` | Graph implementation, MCP server code, Docker files, tests, generated assets. |
| LangExtract | `reference/langextract-main/langextract-main/` | `https://github.com/google/langextract` | zip archive extraction | unavailable | Source-grounded structured extraction and `M* -> M` extraction-gate reference. | `README.md`, `docs/`, `examples/`, `langextract/` | Extraction engine code, provider integrations, scripts, prompts, tests. |
| submodlib | `reference/submodlib-master/submodlib-master/` | `https://github.com/decile-team/submodlib` | zip archive extraction | unavailable | Submodular greedy selector baseline reference. | `README.md`, `docs/`, `tutorials/`, `submodlib/` | Optimizer source, C++ extension code, setup files, requirements, tutorials as code. |
| OR-Tools | `reference/or-tools-stable/or-tools-stable/` | `https://github.com/google/or-tools` | zip archive extraction | unavailable | Exact/near-exact small-instance oracle reference. | `README.md`, `examples/`, `ortools/`, `Dependencies.txt` | Solver source, generated bindings, Bazel/CMake files, examples as implementation. |
| Langfuse | `reference/langfuse-main/langfuse-main/` | `https://github.com/langfuse/langfuse` | zip archive extraction | unavailable | Observability, traces, datasets, evals, and `MetricBridgeWitness` sink reference. | `README.md`, `packages/`, `web/`, `worker/`, `specs/` | Product source, SDK internals, service code, Docker/config files, package manifests. |

`reference/files/` contains auxiliary local reference material and is not one of the six external project indexes.

## How Codex should use these references

Codex may inspect README, docs, and examples to understand architecture patterns, adapter boundaries, and test strategies. Codex must not import code, vendor files, execute scripts, install dependencies, or make these projects required dependencies of mingx.
