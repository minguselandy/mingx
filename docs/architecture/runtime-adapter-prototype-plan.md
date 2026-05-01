# Runtime Adapter Prototype Plan

## Purpose

This plan describes a future integration path for wiring CPS projection into external runtimes such as LangGraph or OpenClaw without making those runtimes core mingx dependencies.

The prototype boundary should let a runtime request context materialization, receive a CPS `ProjectionBundleV1` and materialized context, execute its worker, and preserve audit artifacts for later offline diagnostics. It is an engineering integration plan only.

## Non-goals

- No LangGraph or OpenClaw hard dependency.
- No external service startup.
- No live model call.
- No scheduler theory claim.
- No `measurement_validated` claim.
- No copying reference code.
- No import, execution, or vendoring of local ZIP reference projects.

## Current CPS boundary

Existing CPS pieces already provide the local projection boundary:

- `ProjectionBundleV1` records stable dispatch identity, candidate pool, projection plan, budget witness, materialized context, metric bridge witness, optional diagnostics, and canonical hash.
- `cps.runtime.projection_export` emits projection materialization events after completed cohort dispatches.
- `cps.export` maps `ProjectionBundleV1` into dry-run OTel-style, Langfuse-style, and Phoenix-style local payloads.
- `cps.providers` includes pure provider-output conversion helpers for Graphiti-style and LangExtract-style fake/local objects.
- Synthetic benchmark outputs can already produce `ProjectionBundleV1`-compatible artifacts for offline testing.

Missing pieces for a real runtime adapter are the runtime-facing interface dataclasses, fake runtime harness, runtime callback glue, external-runtime optional wrappers, operator-reviewed dependency policy, and end-to-end mock replay tests.

## Target abstraction

Future adapter code should define generic inputs and outputs without importing any external runtime package.

`RuntimeDispatchInput`:

- `run_id`
- `dispatch_id`
- `agent_id`
- `round_id`
- `task` or `query`
- `role`
- `budget_tokens`
- `candidate_provider_output`
- `materialization_policy`

`RuntimeProjectionOutput`:

- `ProjectionBundleV1`
- `materialized_context`
- `event_payloads`
- optional `observability_payloads`
- optional `selector_regime_label`
- `metric_claim_level`

## Adapter boundary

The external runtime owns:

- scheduling
- worker execution
- tool execution
- memory service lifecycle

CPS owns:

- candidate normalization
- budgeted projection selection
- `ProjectionBundleV1`
- `BudgetWitness`
- `MaterializedContext`
- `MetricBridgeWitness`
- diagnostics and export payloads

The adapter must not let runtime success modify scientific claim gates. Runtime execution status and CPS measurement validity are separate.

## Provider candidate normalization

Provider candidate normalization is an engineering compatibility layer between provider-style CPS candidates and older selector or materializer paths. It harmonizes field aliases for `candidate_id`/`item_id`, `content`/`text`, and `token_cost`/`token_estimate` so runtime candidates can enter downstream projection code without losing identity, content, or token budget fields.

Normalization does not validate measurement, certify V-information, certify submodularity, certify metric bridge freshness, certify deployment claims, change conservative claim gates, or unblock P04 or P09.

## Minimal adapter flow

1. Runtime emits a dispatch event.
2. Adapter converts runtime context or memory results into a CPS candidate pool.
3. CPS selector and materializer create `ProjectionBundleV1`.
4. Adapter returns materialized context to the runtime.
5. Runtime executes its worker.
6. CPS emits projection events and dry-run observability payloads.
7. Runtime or offline evaluator later performs diagnostics.

## LangGraph prototype sketch

Pseudocode only:

```python
def collect_candidates_node(state):
    runtime_records = state["memory_results"]
    candidates = convert_runtime_records_to_cps_candidates(runtime_records)
    return {"candidate_provider_output": candidates}


def cps_projection_node(state):
    dispatch_input = RuntimeDispatchInput(
        run_id=state["run_id"],
        dispatch_id=state["dispatch_id"],
        agent_id=state["agent_id"],
        round_id=state["round_id"],
        task=state["task"],
        role=state["role"],
        budget_tokens=state["budget_tokens"],
        candidate_provider_output=state["candidate_provider_output"],
        materialization_policy=state["materialization_policy"],
    )
    projection_output = cps_project(dispatch_input)
    return {
        "projection_bundle": projection_output.bundle,
        "materialized_context": projection_output.materialized_context,
    }


def worker_execution_node(state):
    context = state["materialized_context"]
    return run_runtime_worker_with_context(context)


def audit_export_node(state):
    return emit_local_projection_audit_payloads(state["projection_bundle"])
```

The future LangGraph-specific wrapper would map graph state to `RuntimeDispatchInput` and map `RuntimeProjectionOutput` back into graph state. It must remain optional.

## OpenClaw prototype sketch

Pseudocode only:

```python
def before_worker_dispatch(runtime_context):
    memory_results = runtime_context.context_engine_results
    candidates = convert_runtime_records_to_cps_candidates(memory_results)
    projection = cps_project(
        RuntimeDispatchInput(
            run_id=runtime_context.run_id,
            dispatch_id=runtime_context.dispatch_id,
            agent_id=runtime_context.agent_id,
            round_id=runtime_context.round_id,
            task=runtime_context.task,
            role=runtime_context.role,
            budget_tokens=runtime_context.budget_tokens,
            candidate_provider_output=candidates,
            materialization_policy=runtime_context.materialization_policy,
        )
    )
    runtime_context.inject_materialized_context(projection.materialized_context)
    runtime_context.attach_projection_audit(projection.event_payloads)
    return runtime_context
```

The future OpenClaw-specific wrapper should call CPS after memory retrieval and before materialized context injection. It must not own CPS scientific gates.

## Required artifacts

- `ProjectionBundleV1`
- `projection_bundle_materialized` event
- OTel/Langfuse/Phoenix dry-run payload
- candidate provenance
- budget witness
- metric bridge witness

## Safety and claim gates

- Runtime adapter success is engineering integration only.
- Runtime adapter success does not validate the deployed V-information regime.
- P04 scientific closure remains required before any scientific validation claim.
- No `measurement_validated` claim is allowed without contamination pass, complete human labels, acceptable kappa, and fresh/passing bridge evidence.
- External runtimes must remain optional until an operator approves dependencies, services, credentials, and live execution.

## Prototype implementation phases after P09

These phases are proposed for later planning only and are not active:

- P10 adapter interface dataclasses.
- P11 local fake runtime adapter.
- P12 LangGraph optional adapter skeleton.
- P13 OpenClaw optional adapter skeleton.
- P14 end-to-end mock runtime demo.
- P15 live integration, operator-required.
