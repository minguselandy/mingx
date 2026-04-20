# Phase 1 Annotation Package

## 你现在需要做什么
- 本轮待标注实例总数：`28`
- tolerance-band flagged：`26`
- face-validity sample：`2`
- 你只需要填写 `labels/` 目录下的 3 个 CSV，然后重跑同一条 cohort 命令。

## 必须填写的文件
- `primary_a.csv`: `C:\Users\Mingx\Documents\mx-codex\phase0-config-starter\phase0-config-starter\artifacts\phase1\live_calibration_p3\exports\annotations\labels\primary_a.csv`
- `primary_b.csv`: `C:\Users\Mingx\Documents\mx-codex\phase0-config-starter\phase0-config-starter\artifacts\phase1\live_calibration_p3\exports\annotations\labels\primary_b.csv`
- `expert.csv`: `C:\Users\Mingx\Documents\mx-codex\phase0-config-starter\phase0-config-starter\artifacts\phase1\live_calibration_p3\exports\annotations\labels\expert.csv`

## 字段规则
- 只能填写 `HIGH`、`LOW`、`BUFFER` 这三个标签。
- `annotation_item_id`、`question_id`、`paragraph_id`、`hop_depth`、`source`、`automated_label` 不要改。
- `primary_a.csv` 和 `primary_b.csv`：`label` 必填，`justification` 可留空。
- `expert.csv`：`label` 和 `justification` 都必填。
- 不要把 `justification` 填成保留字 `[synthetic_passthrough]`；这是测试专用标记。

## 参考文件
- `annotation_queue.csv`：本次需要处理的实例清单。
- `annotation_items.jsonl`：每个实例的完整上下文。
- `target_paragraph` 是目标段落，`paragraphs[]` 是该题的完整段落池。
- `source = tolerance_flagged` 表示这是容忍带仲裁样本。
- `source = face_validity_sample` 表示这是非 flagged 的抽样核验样本。

## 完成后怎么继续
- 填完 3 个 CSV 后，重跑生成这个目录的同一条 cohort 命令。
- 当前仓库的 canonical mock 命令是：
  `uv run python -m cps.runtime.cohort --plan configs/runs/live-calibration-p3.json --backend mock --env .env`
- 如果你要完成 live run 的最终闭环，把上面命令里的 `--backend mock` 改成 `--backend live`。

## 完成判定
- 3 个 CSV 全部逐行填完后，runner 会自动 ingest labels、计算 `kappa_summary.json`。
- reduced-scope 或 synthetic 标注路径仍然只会得到 pilot 级 measurement 状态，不会被当成正式 Phase 1 完成。