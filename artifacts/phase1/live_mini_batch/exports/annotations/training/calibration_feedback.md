# Calibration Feedback Template

- Calibration item count: `5`
- Expert answer key path: `/home/mingxiaoyu/mingx/artifacts/phase1/live_mini_batch/exports/annotations/training/expert_answer_key.csv`

## 使用方式
1. Primary annotators 先独立填写 `calibration_set.csv`。
2. Expert 在 `expert_answer_key.csv` 中确认 draft label，补全 `expert_label` 与 `feedback_notes`。
3. 对系统性分歧做简短复盘，记录到下面的模板里。

## 需要记录的分歧模式
- 哪些案例被误判成 HIGH，但其实只是 supporting-adjacent context。
- 哪些案例应判 LOW，却因实体共现或 lexical overlap 被高估。
- 哪些案例合理落在 BUFFER，以及它们共享的边界信号。

## 复盘记录
- 主要误差模式：
- Expert 修正规则：
- 是否需要追加 worked example：