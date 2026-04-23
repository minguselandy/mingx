# Phase 1 Contamination Review Packet

- Purpose: support human-in-the-loop AI triage after a contamination gate failure.
- Review scope: `above_threshold_questions_only`
- Question count: `3`
- Gate decision: `fail`
- Threshold logp: `-0.6931471805599453`
- Threshold probability: `0.5`

## Regenerate

```bash
python scripts/export_contamination_review_packet.py --run-summary /home/mingxiaoyu/mingx/artifacts/phase1/live_mini_batch/exports/run_summary.json --snippet-chars 280 --json-out /home/mingxiaoyu/mingx/artifacts/phase1/live_mini_batch/exports/contamination_review_packet.json --markdown-out /home/mingxiaoyu/mingx/artifacts/phase1/live_mini_batch/exports/contamination_review_packet.md
```

## Full JSON Report

- `/home/mingxiaoyu/mingx/artifacts/phase1/live_mini_batch/exports/contamination_review_packet.json`

## Operator Rules

- AI output is advisory only. It does not clear the contamination gate.
- Do not auto-rerun the protocol from rewritten questions without recording lineage and human approval.
- Prefer minimal rewrites. If the answer remains too recoverable from the question alone, drop and replace the item.

## 2hop__86458_20273

- Hop depth: `2hop`
- Model: `qwen3.6-plus` (frontier)
- Baseline logp: `-0.0003786687871070171`
- Baseline probability: `0.9996214028988695`
- Question: In what year did the founder of the Presbyterian Church die?
- Gold answer: `1572`

### Heuristic Signals

- `answer_string_appears_in_question = False`
- `answer_alias_hits_in_question = []`
- `shared_question_answer_tokens = []`

### Supporting Paragraphs

- `paragraph_id=7` | `Presbyterianism` | Presbyterian history is part of the history of Christianity, but the beginning of Presbyterianism as a distinct movement occurred during the 16th - century Protestant Reformation. As the Catholic Church resisted the reformers, several different theological movements splintered fr...
- `paragraph_id=15` | `Presbyterianism` | John Knox (1505–1572), a Scot who had spent time studying under Calvin in Geneva, returned to Scotland and urged his countrymen to reform the Church in line with Calvinist doctrines. After a period of religious convulsion and political conflict culminating in a victory for the Pr...

### Stage 1 Prompt

```text
You are auditing a MuSiQue-style question for contamination risk.
Stage 1 is question-only: do not use any hidden answer, retrieval result, or external notes.
Decide whether a strong frontier LM could likely answer this question from prior knowledge alone.
Return strict JSON with keys:
  "question_id", "judgement", "confidence", "primary_mechanism", "secondary_mechanisms", "reasoning", "rewrite_worth_trying"
Allowed judgement values: "likely_contaminated", "uncertain", "likely_clean".
Allowed confidence values: "high", "medium", "low".
Allowed primary_mechanism values: "direct_leakage", "near_unique_entity_chain", "memorized_public_fact", "question_collapse", "dataset_artifact", "unclear".

question_id: 2hop__86458_20273
hop_depth: 2hop
question_text: In what year did the founder of the Presbyterian Church die?
```

### Stage 2 Prompt

```text
Stage 2 is rewrite planning.
You may now inspect the gold answer and supporting evidence.
Propose the smallest rewrite that reduces question-only answerability while preserving the same gold answer and hop structure.
Do not introduce facts not supported by the evidence. Do not change the intended answer.
Return strict JSON with keys:
  "question_id", "rewrite_status", "contamination_cause", "rewrite_strategy", "rewritten_question", "answer_preserved", "hop_structure_preserved", "residual_risk", "operator_note"
Allowed rewrite_status values: "rewrite_recommended", "drop_and_replace", "needs_human_only".
Allowed residual_risk values: "high", "medium", "low".

question_id: 2hop__86458_20273
hop_depth: 2hop
original_question: In what year did the founder of the Presbyterian Church die?
gold_answer: 1572
supporting_evidence:
- paragraph_id=7 | title=Presbyterianism | excerpt=Presbyterian history is part of the history of Christianity, but the beginning of Presbyterianism as a distinct movement occurred during the 16th - century Protestant Reformation. As the Catholic Church resisted the reformers, several different theological movements splintered fr...
- paragraph_id=15 | title=Presbyterianism | excerpt=John Knox (1505–1572), a Scot who had spent time studying under Calvin in Geneva, returned to Scotland and urged his countrymen to reform the Church in line with Calvinist doctrines. After a period of religious convulsion and political conflict culminating in a victory for the Pr...
```

## 3hop1__222979_40769_64047

- Hop depth: `3hop`
- Model: `qwen3.6-plus` (frontier)
- Baseline logp: `-0.00018333042157081536`
- Baseline probability: `0.999816686382424`
- Question: When did the RX 350 from the Scion owner's luxury division change body style?
- Gold answer: `Sales began worldwide in April 2012`

### Heuristic Signals

- `answer_string_appears_in_question = False`
- `answer_alias_hits_in_question = []`
- `shared_question_answer_tokens = []`

### Supporting Paragraphs

- `paragraph_id=1` | `Lexus RX` | A facelift was designed through late 2010 and patented on 7 January 2011 under design registration number 001845801 - 0004. The facelift was unveiled at the March 2012 Geneva Motor Show with new wheels, interior colors, new head and tail lamps and new grilles. New LED running lig...
- `paragraph_id=10` | `Scion (automobile)` | Scion is a discontinued marque of Toyota that started in 2003. It was designed as an extension of its efforts to appeal towards younger customers. The Scion brand primarily featured sports compact vehicles (primarily badge engineered from Toyota's international models), a simplif...
- `paragraph_id=14` | `1973 oil crisis` | Some buyers lamented the small size of the first Japanese compacts, and both Toyota and Nissan (then known as Datsun) introduced larger cars such as the Toyota Corona Mark II, the Toyota Cressida, the Mazda 616 and Datsun 810, which added passenger space and amenities such as air...

### Stage 1 Prompt

```text
You are auditing a MuSiQue-style question for contamination risk.
Stage 1 is question-only: do not use any hidden answer, retrieval result, or external notes.
Decide whether a strong frontier LM could likely answer this question from prior knowledge alone.
Return strict JSON with keys:
  "question_id", "judgement", "confidence", "primary_mechanism", "secondary_mechanisms", "reasoning", "rewrite_worth_trying"
Allowed judgement values: "likely_contaminated", "uncertain", "likely_clean".
Allowed confidence values: "high", "medium", "low".
Allowed primary_mechanism values: "direct_leakage", "near_unique_entity_chain", "memorized_public_fact", "question_collapse", "dataset_artifact", "unclear".

question_id: 3hop1__222979_40769_64047
hop_depth: 3hop
question_text: When did the RX 350 from the Scion owner's luxury division change body style?
```

### Stage 2 Prompt

```text
Stage 2 is rewrite planning.
You may now inspect the gold answer and supporting evidence.
Propose the smallest rewrite that reduces question-only answerability while preserving the same gold answer and hop structure.
Do not introduce facts not supported by the evidence. Do not change the intended answer.
Return strict JSON with keys:
  "question_id", "rewrite_status", "contamination_cause", "rewrite_strategy", "rewritten_question", "answer_preserved", "hop_structure_preserved", "residual_risk", "operator_note"
Allowed rewrite_status values: "rewrite_recommended", "drop_and_replace", "needs_human_only".
Allowed residual_risk values: "high", "medium", "low".

question_id: 3hop1__222979_40769_64047
hop_depth: 3hop
original_question: When did the RX 350 from the Scion owner's luxury division change body style?
gold_answer: Sales began worldwide in April 2012
supporting_evidence:
- paragraph_id=1 | title=Lexus RX | excerpt=A facelift was designed through late 2010 and patented on 7 January 2011 under design registration number 001845801 - 0004. The facelift was unveiled at the March 2012 Geneva Motor Show with new wheels, interior colors, new head and tail lamps and new grilles. New LED running lig...
- paragraph_id=10 | title=Scion (automobile) | excerpt=Scion is a discontinued marque of Toyota that started in 2003. It was designed as an extension of its efforts to appeal towards younger customers. The Scion brand primarily featured sports compact vehicles (primarily badge engineered from Toyota's international models), a simplif...
- paragraph_id=14 | title=1973 oil crisis | excerpt=Some buyers lamented the small size of the first Japanese compacts, and both Toyota and Nissan (then known as Datsun) introduced larger cars such as the Toyota Corona Mark II, the Toyota Cressida, the Mazda 616 and Datsun 810, which added passenger space and amenities such as air...
```

## 4hop1__76111_624859_355213_203322

- Hop depth: `4hop`
- Model: `qwen3.6-plus` (frontier)
- Baseline logp: `-6.44912724965252e-05`
- Baseline probability: `0.9999355108070209`
- Question: What county shares a border with the county where the singer of Hungry Eyes from the movie Dirty Dancing was born?
- Gold answer: `Cabarrus County`

### Heuristic Signals

- `answer_string_appears_in_question = False`
- `answer_alias_hits_in_question = []`
- `shared_question_answer_tokens = ['county']`

### Supporting Paragraphs

- `paragraph_id=0` | `Gold Hill, North Carolina` | Gold Hill is a small unincorporated community in southeastern Rowan County, North Carolina near the Cabarrus County line. It is situated near the Yadkin River and is served by U.S. Highway 52 and Old Beatty Ford Road. Gold was found in this small town outside Salisbury in the 19t...
- `paragraph_id=7` | `The Definitive Collection (Eric Carmen album)` | The Definitive Collection is a 1997 greatest hits compilation album of all the singles released by Cleveland, Ohio singer-songwriter Eric Carmen. It features five hits by the Raspberries, a power pop group which he led in the early 1970s. It also contains his versions of two majo...
- `paragraph_id=12` | `Hungry Eyes` | ``Hungry Eyes ''is a song performed by American artist Eric Carmen, a former member of the band Raspberries, and was featured in the film Dirty Dancing. The song was recorded at Beachwood Studios in Beachwood, Ohio in 1987.`` Hungry Eyes'' peaked at # 4 on the Billboard Hot 100 c...
- `paragraph_id=13` | `Cleveland, North Carolina` | Cleveland is a town in the Cleveland Township of Rowan County, North Carolina, United States. The population was 871 at the 2010 census.

### Stage 1 Prompt

```text
You are auditing a MuSiQue-style question for contamination risk.
Stage 1 is question-only: do not use any hidden answer, retrieval result, or external notes.
Decide whether a strong frontier LM could likely answer this question from prior knowledge alone.
Return strict JSON with keys:
  "question_id", "judgement", "confidence", "primary_mechanism", "secondary_mechanisms", "reasoning", "rewrite_worth_trying"
Allowed judgement values: "likely_contaminated", "uncertain", "likely_clean".
Allowed confidence values: "high", "medium", "low".
Allowed primary_mechanism values: "direct_leakage", "near_unique_entity_chain", "memorized_public_fact", "question_collapse", "dataset_artifact", "unclear".

question_id: 4hop1__76111_624859_355213_203322
hop_depth: 4hop
question_text: What county shares a border with the county where the singer of Hungry Eyes from the movie Dirty Dancing was born?
```

### Stage 2 Prompt

```text
Stage 2 is rewrite planning.
You may now inspect the gold answer and supporting evidence.
Propose the smallest rewrite that reduces question-only answerability while preserving the same gold answer and hop structure.
Do not introduce facts not supported by the evidence. Do not change the intended answer.
Return strict JSON with keys:
  "question_id", "rewrite_status", "contamination_cause", "rewrite_strategy", "rewritten_question", "answer_preserved", "hop_structure_preserved", "residual_risk", "operator_note"
Allowed rewrite_status values: "rewrite_recommended", "drop_and_replace", "needs_human_only".
Allowed residual_risk values: "high", "medium", "low".

question_id: 4hop1__76111_624859_355213_203322
hop_depth: 4hop
original_question: What county shares a border with the county where the singer of Hungry Eyes from the movie Dirty Dancing was born?
gold_answer: Cabarrus County
supporting_evidence:
- paragraph_id=0 | title=Gold Hill, North Carolina | excerpt=Gold Hill is a small unincorporated community in southeastern Rowan County, North Carolina near the Cabarrus County line. It is situated near the Yadkin River and is served by U.S. Highway 52 and Old Beatty Ford Road. Gold was found in this small town outside Salisbury in the 19t...
- paragraph_id=7 | title=The Definitive Collection (Eric Carmen album) | excerpt=The Definitive Collection is a 1997 greatest hits compilation album of all the singles released by Cleveland, Ohio singer-songwriter Eric Carmen. It features five hits by the Raspberries, a power pop group which he led in the early 1970s. It also contains his versions of two majo...
- paragraph_id=12 | title=Hungry Eyes | excerpt=``Hungry Eyes ''is a song performed by American artist Eric Carmen, a former member of the band Raspberries, and was featured in the film Dirty Dancing. The song was recorded at Beachwood Studios in Beachwood, Ohio in 1987.`` Hungry Eyes'' peaked at # 4 on the Billboard Hot 100 c...
- paragraph_id=13 | title=Cleveland, North Carolina | excerpt=Cleveland is a town in the Cleveland Township of Rowan County, North Carolina, United States. The population was 871 at the 2010 census.
```
