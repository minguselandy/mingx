# Goal ID: POST-0 / Post-merge baseline verification

## Objective

Verify the current repository baseline after EPF-FINAL, PAPER-RS, and LAPI-1 through LAPI-8. Do not implement new functionality and do not run live API calls.

## Read first

- `codex-goals/post-lapi/GLOBAL_CONSTRAINTS.md` if available
- `docs/api/live-api-capability-contract.md`
- `docs/paper/live-api-experiment-boundaries.md`
- `docs/roadmaps/live-api-only-development-plan.md`
- `docs/reviews/` latest POST-LAPI or LAPI reviews

## Hard constraints

- No live API calls.
- No new experiments.
- No silver-label scaling.
- No Route 5 or Route 8 unlock.
- No `git add -A`.
- Do not stage, delete, move, or clean historical untracked leftovers.
- Do not modify raw API response policy.
- Do not introduce any claim upgrade.

## Steps

1. Inspect baseline:
   ```bash
   git status --short --untracked-files=all
   git branch --show-current
   git rev-parse --short HEAD
   git rev-parse --short origin/codex/integrated-validation-workbench
   ```

2. Fetch remote refs only:
   ```bash
   git fetch origin
   ```

3. Check whether the reported HEAD `f38d3aa` is contained in `origin/main`:
   ```bash
   git merge-base --is-ancestor f38d3aa origin/main && echo "HEAD_CONTAINED_IN_ORIGIN_MAIN=yes" || echo "HEAD_CONTAINED_IN_ORIGIN_MAIN=no"
   ```

4. Do not switch branches unless necessary. If main verification requires switching:
   ```bash
   git switch main
   git pull --ff-only
   git merge-base --is-ancestor f38d3aa HEAD && echo "MERGED_TO_MAIN=yes" || echo "MERGED_TO_MAIN=no"
   ```

5. Run lightweight checks:
   ```bash
   git diff --check
   uv run pytest tests/test_revised_framing_guardrails.py tests/test_live_api_claim_contract.py tests/test_no_teacher_forced_claims_live_api_only.py -q
   python -m compileall cps tests
   ```

6. Run claim-boundary grep over active docs and tests:
   ```bash
   grep -RIn --exclude-dir=.git --exclude-dir=.codex --exclude-dir=artifacts/operator_inputs \
     -E "teacher-forced NLL support|fixed-target continuation scoring support|metric bridge support|calibrated_proxy_supported|vinfo_proxy_supported|measurement validation|human/external gold validation|paper-grade evidence|selector superiority|global selector superiority|Route 5 unlock|Route 8 unlock" \
     docs tests cps || true
   ```

## Allowed changes

- `docs/reviews/POST-LAPI-baseline-verification.md` only.

## Baseline report requirements

Create `docs/reviews/POST-LAPI-baseline-verification.md` with:
- current branch
- current HEAD
- whether `origin/main` contains `f38d3aa`
- whether index is clean
- untracked leftovers summary without staging them
- checks run and results
- claim status
- confirmation that no live API calls were run
- confirmation that no new experiments were run
- confirmation that Route 5 and Route 8 remain locked
- confirmation that raw API responses are not stored
- next recommended goal

## Done condition

- Baseline report is created.
- Checks complete or failures are documented.
- No unrelated leftovers are staged.
- No claim upgrade is introduced.
- Do not commit automatically unless explicitly instructed after review.


Report format:
- Goal ID:
- Branch:
- HEAD:
- Changed files:
- Staged files:
- Checks run:
- Check results:
- Live API calls run: yes/no
- Raw API responses stored: yes/no
- Claim level:
- Claim upgrade introduced: yes/no
- Route 5 locked: yes/no
- Route 8 locked: yes/no
- Unrelated leftovers staged: yes/no
- Next recommended goal:
