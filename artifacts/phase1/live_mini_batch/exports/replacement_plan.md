# Replacement Plan

- Run: `phase1-cohort-20260423033750`
- Scope: `pilot_reduced_scope`
- Basis: `same_hop_next_rank_on_resume_v1`
- Selection algorithm: `calibration_by_hop_questionid_sha256_v1`
- Replacement manifest: `../replacement_manifest.json`

## Purpose

This note records the next same-hop replacement candidates after the final
operator decision moved all three contaminated questions to
`drop_and_replace`.

These are **selection candidates**, not scientific approvals.

They still need ordinary runtime handling and any contamination-related checks
required by the current workflow before being consumed in a future run.

## Dropped Questions

- `2hop__86458_20273`
- `3hop1__222979_40769_64047`
- `4hop1__76111_624859_355213_203322`

## Selected Replacements

| dropped question | replacement question | hop depth | selection score |
| --- | --- | --- | --- |
| `2hop__86458_20273` | `2hop__132929_684936` | `2hop` | `16004b50469c16631c5905ff48369fad99c515c96bf6264a515f3e8b150f4ff0` |
| `3hop1__222979_40769_64047` | `3hop1__409517_547811_80702` | `3hop` | `1067cd9da2197f8d54cd76900819d5dbc3a75a49ba94c0d75685bffe6b154aa8` |
| `4hop1__76111_624859_355213_203322` | `4hop3__373866_5189_38229_86687` | `4hop` | `1110c27860549edadd3def3ba6894cae80001ab79ef9357c4f7fa86c0751ebdd` |

## Replacement Question Summaries

### 1. `2hop__132929_684936`

- Question:
  `What company eventually became the company that made the Skyflash missle?`
- Gold answer:
  `BAC`
- Supporting titles:
  - `Skyflash`
  - `Sea Wolf (missile)`

### 2. `3hop1__409517_547811_80702`

- Question:
  `What is the name of the famous bridge in the birth city of the composer of Scanderbeg?`
- Gold answer:
  `Rialto Bridge`
- Supporting titles:
  - `Scanderbeg (opera)`
  - `Rialto Bridge`
  - `Orlando furioso (Vivaldi, 1714)`

### 3. `4hop3__373866_5189_38229_86687`

- Question:
  `A group of nations of which the People's Socialist Republic of Albania was a member was controlled by one country. When did that country agree to a unified Germany inside of the organization Eisenhower would not discuss during the campaign?`
- Gold answer:
  `May 1990`
- Supporting titles:
  - `German reunification`
  - `Dwight D. Eisenhower`
  - `Hero of Socialist Labour (Albania)`
  - `Warsaw Pact`

## Recommended Operator Use

1. Treat these as the default next-in-line replacements for a future reduced-scope follow-up batch.
2. Keep the current failed run unchanged; do not mutate its scientific status.
3. If a future batch is prepared, carry forward the dropped-question lineage and the replacement manifest together.
4. If the team wants to stay conservative, run question-only contamination checks on the replacements before scheduling a new live batch.

## Reminder

This file records replacement selection only.

It does not:

- approve a rerun by itself
- clear contamination for the current failed run
- imply that the replacements are already contamination-safe
