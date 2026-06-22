# ModelBenchmarkTesting

供应商无关的代码模型 API 评测框架 MVP，面向真实软件工程任务，而不是只依赖公开 benchmark 或简单聊天示例。

## 设计目标

- **真实工程场景**：在 git 工作区内让模型修改已有代码、运行测试、生成 diff。
- **Java 优先**：MVP 内置 20 个任务定义，其中 **16 个 Java 任务（80%）**，4 个非 Java 任务（20%）。
- **供应商无关**：统一 `ModelClient` 接口，可接 OpenAI-compatible、本地 HTTP、Anthropic 等 API。
- **采购指标**：成功率、约束违规率、成本、延迟、稳定性、人工审查结果。
- **可复现**：每次运行保留 prompt、模型输出、diff、测试日志、结果 JSON/CSV。

## 当前环境建议

本机已确认：Python 3.9、Java 8、Maven、Git、Docker、npm 可用；Gradle 未安装。因此首版示例任务以 Maven/JUnit/Spring 风格约束为主，Gradle 任务作为模板保留。

## 快速开始

```bash
cd /Users/zhengkai/test/ModelBenchmarkTesting
python3 -m evaluator.cli validate-tasks
python3 -m evaluator.cli run --model mock --limit 1
python3 -m evaluator.cli summarize --results-dir results/raw
```

## 配置真实模型

编辑 `configs/models.json`：

```json
{
  "models": {
    "my-model": {
      "type": "openai_compatible",
      "base_url": "https://api.example.com/v1/chat/completions",
      "api_key_env": "MY_MODEL_API_KEY",
      "model": "vendor/model-name",
      "input_cost_per_1k": 0.001,
      "output_cost_per_1k": 0.003
    }
  }
}
```

然后：

```bash
export MY_MODEL_API_KEY=...
python3 -m evaluator.cli run --model my-model --repetitions 3
```

## 任务结构

```text
tasks/java/<task-id>/
  task.json          # 任务元数据、prompt、命令、约束、成本/时间限制
  repo/              # 被评测代码仓库初始状态，可替换为真实项目快照
  hidden_tests/      # 隐藏测试或隐藏检查脚本（模型不可见）
  evaluator/         # 任务级自定义检查脚本
tasks/non_java/<task-id>/...
```

## 核心指标

- `success_rate = successful_tasks / total_tasks`
- `java_success_rate = successful_java_tasks / java_tasks`
- `constraint_violation_rate = tasks_with_violation / total_tasks`
- `cost_per_success = total_cost_usd / successful_tasks`
- `latency`: p50 / p90 / p95 / timeout rate
- `stability`: 同一任务多次运行结果一致性
- `human_review`: 可读性、最小改动、设计、测试质量、安全性、风格一致性

## 推荐采购门槛

| 阶段 | Java 成功率 | Critical 违规率 | 总违规率 | 稳定性 | 人审均分 |
|---|---:|---:|---:|---:|---:|
| 小规模试用 | >= 60% | <= 5% | <= 15% | >= 65% | >= 3.5/5 |
| 正式采购 | >= 75% | <= 2% | <= 8% | >= 80% | >= 4.0/5 |

## 说明

`mock` 模型只用于验证评测框架链路，不代表真实模型能力。真实采购评估应接入候选 API，并至少对每个任务重复运行 3 次。

## Real Java repository upgrade

The 16 Java tasks under `tasks/java/*/repo` now contain Java 8 compatible Maven projects with production classes and JUnit 5 tests. They are intentionally dependency-light while modeling realistic engineering concerns: Spring-like layering, validation, Maven/build policy, concurrency, security, SQL safety, date/time correctness, repository batching, and refactoring. Validate them with:

```bash
for d in tasks/java/*/repo; do (cd "$d" && mvn -q test); done
```

# Web console uses Python standard library:
# python3 -m evaluator.web_app --host 127.0.0.1 --port 8765

## Local Web Evaluation Console

Start the local Web UI:

```bash
cd /Users/zhengkai/test/ModelBenchmarkTesting
python3 -m evaluator.web_app --host 127.0.0.1 --port 8765
```

Then open `http://127.0.0.1:8765`. The page lets you enter model name, API key, base URL, thinking level, prices, repetitions, and selected tasks. It runs real engineering tasks and shows success rate, Java success rate, constraint violations, cost, latency, stability, and per-task details.

Security: API keys are used in memory for the active run and are not written to result files. See `docs/web_console.md` for details.

### Real AI edit scoring

The evaluator now requires models to return machine-applicable code changes. The runner applies unified diffs or JSON file edits, records `patch_applied`, `files_changed`, `final_diff`, and `failure_reasons`, then runs the configured tests.

A task is successful only when the model actually changes files, the modified code passes tests, and there are no major or critical constraint violations. Plain explanations or no-op responses fail.

