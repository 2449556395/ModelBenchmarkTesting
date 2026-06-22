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

## Real AI edit flow

The Web console now evaluates whether the model actually edits code. A run is not considered successful just because the original repository already passes tests.

For every selected task, the backend now performs this flow:

1. Copy the task repository into an isolated `.work/<run_id>/` directory.
2. Initialize a git baseline.
3. Run baseline tests for reviewer context.
4. Ask the model to return machine-applicable code changes.
5. Apply the model output as either a unified diff or JSON file edits.
6. Compute `git diff`, `files_changed`, and patch application status.
7. Run the configured tests, for example `mvn -q test`.
8. Check constraints.
9. Mark success only if all are true:
   - patch was applied,
   - at least one file changed,
   - tests passed after the change,
   - there is no major or critical constraint violation.

Supported model output formats:

```diff
diff --git a/src/main/java/example/Foo.java b/src/main/java/example/Foo.java
--- a/src/main/java/example/Foo.java
+++ b/src/main/java/example/Foo.java
@@ -1 +1 @@
-old
+new
```

Or:

```json
{
  "edits": [
    {"path": "src/main/java/example/Foo.java", "content": "full replacement file content"}
  ]
}
```

The page displays patch status, changed files, failure reasons, and a diff/error preview for each run. No-op model responses now fail instead of producing a misleading 100% success rate.

