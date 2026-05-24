# Mingx POST-LAPI Codex Goal Pack

This pack contains file-driven Codex CLI `/goal` documents for the POST-LAPI phase.

## How to install into the repo

From the repository root:

```bash
mkdir -p codex-goals configs
cp -R /path/to/mingx_post_lapi_codex_goals/codex-goals ./codex-goals/post-lapi
cp -R /path/to/mingx_post_lapi_codex_goals/configs ./configs/post-lapi
cp /path/to/mingx_post_lapi_codex_goals/GLOBAL_CONSTRAINTS.md ./codex-goals/post-lapi/GLOBAL_CONSTRAINTS.md
```

Or unzip this pack directly at the repo root and keep the folder names.

## Enable Codex goal mode

If `/goal` does not appear in Codex CLI:

```bash
codex features enable goals
```

Then open the repo:

```bash
codex -C /path/to/mingx
```

## Recommended execution order

Run the configuration goals first. They do not permit live API calls.

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

The `run-pilots` goals are deliberately separate. Do not run them until POST-0 through POST-2 pass and the project owner explicitly approves live API calls.

## Goal design

Each goal has:
- one objective
- hard constraints
- files to read first
- allowed changes
- steps
- validation checks
- done condition
- report format

All goals preserve `operational_utility_only/no_claim_upgrade` unless a later accepted evidence package explicitly changes the project state.
