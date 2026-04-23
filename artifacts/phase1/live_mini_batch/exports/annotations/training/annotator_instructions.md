# Phase 1 Annotator Instructions

## 目标
- 你需要把目标段落标成 `HIGH`、`LOW` 或 `BUFFER`，判断标准是它对回答当前问题的相对价值。
- `HIGH`：去掉后很可能显著伤害答案概率或多跳链路完整性。
- `LOW`：去掉后影响很小，主要是背景、重复或弱相关信息。
- `BUFFER`：价值接近 tertile 边界，或你认为证据不足以稳定判成 HIGH/LOW。

## 使用顺序
1. 先看 `5` 个 worked examples，熟悉标签边界。
2. 再做 `5` 个 calibration items。
3. calibration 完成后，再进入本轮正式 queue。

## 具体操作
- 每个 item 先读 `question_text` 和 `answer_text`，再看 `target_paragraph`，最后参考整题 `paragraphs[]`。
- 重点判断 target paragraph 是否承载关键 bridge fact、实体 disambiguation、或多跳链路中的必要中介。
- 如果你对 HIGH/LOW 犹豫，而且它又靠近边界，优先标 `BUFFER` 并在 expert 讨论环节解释原因。

## Expert 协作约定
- `expert_answer_key.csv` 当前是 draft scaffold，不是最终 gold。
- 正式 onboarding 前，expert 需要先确认 calibration gold label，再把反馈写入 `calibration_feedback.md`。