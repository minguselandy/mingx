# Teacher-Forced LogProbe Scoring Contract

Claim status: operational_utility_only/no_claim_upgrade

## Required Fields

- deterministic_settings
- fixed_target_text
- materialization_policy_hash
- per_token_logprobs
- prompt_template_hash
- prompt_text
- raw_response_stored=false
- scorer_model_id
- scoring_backend_id
- scoring_policy
- target_format_hash
- target_nll
- target_nll_normalized
- target_token_count
- target_token_ids
- tokenizer_id

Validation rejects empty fixed targets, generated-target mismatches, missing tokenization metadata, missing target logprobs, raw response payload fields, and secret-like fields.
