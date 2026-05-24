# Codex command snippets

## Enable goal mode

```bash
codex features enable goals
```

## Start Codex in repo

```bash
codex -C /path/to/mingx
```

## Run configuration goals

```text
/goal Read codex-goals/post-lapi/codex-goals/configure/00-post-merge-baseline-verification.goal.md and execute exactly. Stop at the Done condition and report.
/goal Read codex-goals/post-lapi/codex-goals/configure/01-artifact-replay-integrity-config.goal.md and execute exactly. Stop at the Done condition and report.
/goal Read codex-goals/post-lapi/codex-goals/configure/02-paper-table-readiness-config.goal.md and execute exactly. Stop at the Done condition and report.
/goal Read codex-goals/post-lapi/codex-goals/configure/03-judge-stability-config.goal.md and execute exactly. Stop at the Done condition and report.
/goal Read codex-goals/post-lapi/codex-goals/configure/04-sufficiency-abstention-config.goal.md and execute exactly. Stop at the Done condition and report.
/goal Read codex-goals/post-lapi/codex-goals/configure/05-reprojection-witness-config.goal.md and execute exactly. Stop at the Done condition and report.
/goal Read codex-goals/post-lapi/codex-goals/configure/06-operational-replay-config.goal.md and execute exactly. Stop at the Done condition and report.
/goal Read codex-goals/post-lapi/codex-goals/configure/07-extraction-quality-audit-config.goal.md and execute exactly. Stop at the Done condition and report.
/goal Read codex-goals/post-lapi/codex-goals/configure/08-submission-reviewer-package-config.goal.md and execute exactly. Stop at the Done condition and report.
```

## Approval strings for later live API pilots

Only use these after POST-0 to POST-2 pass and you explicitly want live API calls.

```text
APPROVE_LIVE_API_POST_3_JUDGE_STABILITY=true
APPROVE_LIVE_API_POST_4_SUFFICIENCY_ABSTENTION=true
APPROVE_LIVE_API_POST_5_REPROJECTION_WITNESS=true
APPROVE_POST_6_OPERATIONAL_REPLAY_EXPANSION=true
APPROVE_LIVE_API_POST_7_EXTRACTION_AUDIT=true
```
