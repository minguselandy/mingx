from __future__ import annotations

from typing import Any

from cps.export.common import projection_bundle_observability_fields
from cps.schema import ProjectionBundleV1


def projection_bundle_to_otel_span(
    bundle: ProjectionBundleV1,
    *,
    include_payload_preview: bool = False,
) -> dict[str, Any]:
    fields = projection_bundle_observability_fields(
        bundle,
        include_payload_preview=include_payload_preview,
    )
    payload: dict[str, Any] = {
        "name": "cps.projection_bundle",
        "kind": "INTERNAL",
        "trace_id": fields["run_id"],
        "span_id": fields["dispatch_id"],
        "attributes": fields["attributes"],
        "events": [
            {
                "name": "projection_bundle_materialized",
                "attributes": {
                    "cps.canonical_hash": fields["canonical_hash"],
                    "cps.dispatch_id": fields["dispatch_id"],
                },
            }
        ],
    }
    if include_payload_preview and "payload_preview" in fields:
        payload["payload_preview"] = fields["payload_preview"]
    return payload
