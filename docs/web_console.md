# Local Web Evaluation Console

The project includes a local browser-based console for evaluating code models against the real engineering task set.

## Start

```bash
cd /Users/zhengkai/test/ModelBenchmarkTesting
python3 -m evaluator.web_app --host 127.0.0.1 --port 8765
```

Open:

```text
http://127.0.0.1:8765
```

## What you can configure on the page

- Model display name
- OpenAI-compatible model id
- Base URL, usually the full chat-completions endpoint
- API Key
- Thinking/reasoning level: `none`, `low`, `medium`, `high`
- Input/output token prices
- Repetitions
- Task selection
- Mock-mode smoke test

## What the Web run does

For selected tasks, the backend reuses the existing evaluator runner. It invokes the selected model, prepares the task workdir, runs configured task commands such as `mvn -q test`, checks constraints, and aggregates procurement metrics.

The page displays:

- Overall success rate
- Java success rate
- Constraint violation rate
- Critical constraint violation rate
- Total cost
- Cost per success
- Latency percentiles
- Stability score
- Per-task details

## Security

API keys entered on the page are kept in process memory for the active run only. They are not written to `configs/`, `results/web_runs/`, `results/raw/`, or report JSON files.

If historical multi-user tracking is needed later, MySQL can store run metadata only. Do not store raw API keys.

## Smoke test with mock model

1. Keep `Use mock model` checked.
2. Select one task.
3. Click `Start`.
4. Wait for the status to become `completed`.
5. Review metrics and details on the right panel.

Generated Web run snapshots are saved under:

```text
results/web_runs/<job_id>/
```
