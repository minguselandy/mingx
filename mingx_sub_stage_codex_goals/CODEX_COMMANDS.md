# Codex Commands

Use these from the repository root after unpacking this package.

```text
/goal Read mingx_sub_stage_codex_goals/codex-goals/SUB-0-evidence-freeze-and-paper-synthesis-baseline.goal.md and execute exactly. Stop at the Done condition and report.
```

```text
/goal Read mingx_sub_stage_codex_goals/codex-goals/SUB-1-manuscript-integration-post-lapi-evidence.goal.md and execute exactly. Stop at the Done condition and report.
```

```text
/goal Read mingx_sub_stage_codex_goals/codex-goals/SUB-2-independent-claim-boundary-review.goal.md and execute exactly. Stop at the Done condition and report.
```

```text
/goal Read mingx_sub_stage_codex_goals/codex-goals/SUB-3-submission-reviewer-package.goal.md and execute exactly. Stop at the Done condition and report.
```

```text
/goal Read mingx_sub_stage_codex_goals/codex-goals/SUB-4-gap-filling-decision-gate.optional.goal.md and execute exactly. Stop at the Done condition and report.
```

```text
/goal Read mingx_sub_stage_codex_goals/codex-goals/SUB-5-final-pr-or-submission-readiness-summary.goal.md and execute exactly. Stop at the Done condition and report.
```

## Staging rule

Never use:

```bash
git add -A
```

Stage explicit files only, and only after reviewing `git status --short --untracked-files=all`.
