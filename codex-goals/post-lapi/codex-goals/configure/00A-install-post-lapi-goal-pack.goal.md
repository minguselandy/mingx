# Goal ID: POST-LAPI-GOALPACK-INSTALL / Install goal and config files into repo

## Objective

Install this POST-LAPI goal pack into the repository so future Codex `/goal` runs can reference goal files by path.

## Hard constraints

- No live API calls.
- No experiments.
- No claim upgrade.
- Do not stage unrelated leftovers.
- Do not use `git add -A`.

## Steps

1. Confirm current repository root:
   ```bash
   pwd
   git rev-parse --show-toplevel
   ```

2. Create directories if missing:
   ```bash
   mkdir -p codex-goals/post-lapi configs/post_lapi
   ```

3. Copy the goal pack files into:
   - `codex-goals/post-lapi/`
   - `configs/post_lapi/`

4. Do not commit automatically.

## Done condition

- Goal files and config files are available in the repository.
- No unrelated files were staged.
- No claim upgrade was introduced.


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
