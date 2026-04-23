# Rewrite Candidates For `3hop1__222979_40769_64047`

- Original question:
  `When did the RX 350 from the Scion owner's luxury division change body style?`
- Gold answer:
  `Sales began worldwide in April 2012`
- Current recommendation:
  `drop_and_replace`

## Rewrite Goal

Reduce question-only answerability without changing:

- the gold answer
- the Toyota -> Lexus linkage
- the intended evidence path

The main leakage problem in the original wording is the direct clue bundle:

- `RX 350`
- `Scion owner`
- `luxury division`

Together, these clues narrow the answer path too aggressively.

## Candidate A

`When did worldwide sales begin for the facelifted 350 variant of the crossover sold by the luxury division of the company that owned Scion?`

- Strengths:
  Keeps the 350-variant target while removing the direct `RX 350` string.
- Weaknesses:
  Still may be easy for a strong model to map to Lexus RX 350.
- Residual risk:
  `medium`

## Candidate B

`When did worldwide sales begin for the facelifted crossover sold by the luxury division of Scion's parent company?`

- Strengths:
  Removes the most direct leakage handle and keeps the Toyota -> Lexus bridge.
- Weaknesses:
  Broadens the target from the exact RX 350 variant toward the broader RX line.
- Residual risk:
  `medium-high`

## Candidate C

`When did worldwide sales begin for the facelifted crossover from the luxury marque of the company behind Scion?`

- Strengths:
  Most natural phrasing among the indirect versions.
- Weaknesses:
  Weakest control over target specificity; may drift too far from the exact original item.
- Residual risk:
  `high`

## Recommended Candidate

Use **Candidate A** only as the historical candidate that was selected for reprobe.

Why Candidate A is the best current compromise:

- It avoids the literal `RX 350` string.
- It still preserves the `350` clue, which helps keep the target closer to the original item.
- It retains the intended Toyota -> Lexus reasoning bridge.

## Live Reprobe Result

The selected rewrite candidate was reprobed live:

- backend: `live`
- model role: `frontier`
- model id: `qwen3.6-plus`
- response status: `200`
- baseline_logp: `-0.00028821608191265113`
- threshold_logp: `-0.6931471805599453`
- passes contamination threshold: `false`

Interpretation:

- The rewrite still leaves the answer highly recoverable from the question alone.
- This item should no longer be treated as an active rewrite candidate.

## Reprobe Rule

Do not reuse this rewrite in a future run unless it passes a fresh
question-only contamination reprobe first.

Minimum reprobe question:

- Does the rewritten question still produce `baseline_logp > log(0.5)` under the current frontier model?

If yes:

- reject the rewrite
- mark the item `drop_and_replace`

If no:

- keep the rewrite candidate in a human-approved lineage log
- only then consider it for a future run

For the current batch, this branch did not happen.

## Human Approval Fields

- Approved candidate: `[pending]`
- Approver: `[pending]`
- Approval date: `[pending]`
- Fresh reprobe result: `[pending]`
- Final disposition: `drop_and_replace`
