# Route 3 Artifact Storage Policy

Status: Package A storage policy
Claim status: `operational_utility_only; no_claim_upgrade`

Route 3 should keep Git focused on deterministic review artifacts, not raw or
large generated data.

## Commit to Git

- Protocol plans and pre-registration documents.
- Small deterministic JSON summaries and validation reports.
- Schema versions, generation configs, row counts, content hashes, and claim
  boundary reports.
- Short markdown review packages and artifact manifests.

## Do Not Commit by Default

- Large JSONL delta-record files.
- Large operator-input JSONL files.
- Raw dispatch traces beyond explicitly accepted package scope.
- Raw benchmark mirrors.
- Raw live API responses, response dumps, or secrets.

## Storage Options for Large Artifacts

Use one of these before generating new large Route 3 artifacts:

- GitHub release assets for immutable reviewed packages.
- Git LFS for versioned large artifacts when repository policy allows it.
- DVC or another external artifact store for reproducible data pipelines.
- Operator-managed external storage for raw live API logs or sensitive material.

## Required Manifest Fields

For any large artifact stored outside normal Git, commit a small manifest with:

- relative artifact path or external storage locator;
- schema version;
- row count;
- unique instance count;
- content hash;
- generator version or commit;
- evaluator ID and non-secret evaluator settings;
- validation status;
- claim status.

## Claim Boundary

Artifact storage decisions do not create metric evidence. Route 3 remains
`no_claim_upgrade` until future pre-registered rows pass gates and independent
review accepts the result.
