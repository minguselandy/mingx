from __future__ import annotations

from typing import Any

from cps.export.common import projection_bundle_observability_fields
from cps.schema import ProjectionBundleV1


def projection_bundle_to_phoenix_payload(
    bundle: ProjectionBundleV1,
    *,
    include_payload_preview: bool = False,
) -> dict[str, Any]:
    fields = projection_bundle_observability_fields(
        bundle,
        include_payload_preview=include_payload_preview,
    )
    attributes = fields["attributes"]
    evaluations: list[dict[str, Any]] = []
    metric_claim_level = attributes.get("cps.metric_claim_level")
    if metric_claim_level is not None:
        evaluations.append(
            {
                "name": "metric_claim_level",
                "value": metric_claim_level,
                "source": "cps.diagnostics",
            }
        )

    payload: dict[str, Any] = {
        "trace_id": fields["run_id"],
        "span_id": fields["dispatch_id"],
        "span_name": "cps.projection_bundle",
        "attributes": attributes,
        "evaluations": evaluations,
    }
    if include_payload_preview and "payload_preview" in fields:
        payload["payload_preview"] = fields["payload_preview"]
    return payload
