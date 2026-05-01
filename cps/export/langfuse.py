from __future__ import annotations

from typing import Any

from cps.export.common import projection_bundle_observability_fields
from cps.schema import ProjectionBundleV1


def projection_bundle_to_langfuse_payload(
    bundle: ProjectionBundleV1,
    *,
    include_payload_preview: bool = False,
) -> dict[str, Any]:
    fields = projection_bundle_observability_fields(
        bundle,
        include_payload_preview=include_payload_preview,
    )
    metadata = fields["attributes"]
    payload: dict[str, Any] = {
        "dry_run": True,
        "trace": {
            "id": fields["run_id"],
            "name": "cps.dispatch",
            "metadata": metadata,
        },
        "observation": {
            "id": fields["dispatch_id"],
            "type": "span",
            "name": "projection_bundle_materialized",
            "metadata": metadata,
        },
    }
    if include_payload_preview and "payload_preview" in fields:
        payload["observation"]["payload_preview"] = fields["payload_preview"]
    return payload


def export_projection_bundle_to_langfuse(
    bundle: ProjectionBundleV1,
    *,
    dry_run: bool = True,
    client: Any = None,
    include_payload_preview: bool = False,
) -> dict[str, Any]:
    if not dry_run and client is None:
        raise RuntimeError("dry_run=False requires an explicit client")
    if not dry_run:
        raise RuntimeError("non-dry-run Langfuse export is outside the P07 dry-run contract")
    return projection_bundle_to_langfuse_payload(
        bundle,
        include_payload_preview=include_payload_preview,
    )
