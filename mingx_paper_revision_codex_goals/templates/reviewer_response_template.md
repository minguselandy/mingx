# Reviewer Response Template

## Why no NLL bridge?

The supported live-API route exposes generated output-token diagnostics, not documented fixed-target continuation scoring. We therefore fail closed rather than relabel sampled chat logprobs as teacher-forced NLL.

## Why mention V-information?

V-information defines the formal ideal of usable information for bounded predictors. The present experiments use it as an organizing lens, not as an estimated deployment metric.

## Why use LLM judges?

LLM judges are used as weak supervisory signals with order-swap, duplicate, and rubric-paraphrase controls. They are not gold validation.

## Why not claim selector superiority?

The operational replay is scoped to named datasets, budgets, baselines, and materialization conditions. It supports scoped operational improvement under matched budgets, not global selector superiority.
