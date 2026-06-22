from __future__ import annotations
from pathlib import Path
from evaluator.sandbox import run_command


def run_task_commands(task: dict, work_dir: Path) -> list[dict]:
    repo_dir = work_dir / 'repo'
    results = []
    for cmd in task.get('commands', {}).get('test', []):
        results.append(run_command(cmd, repo_dir, task.get('limits', {}).get('timeout_seconds', 900)))
    return results


def tests_pass(results: list[dict]) -> bool:
    return bool(results) and all(r['exit_code'] == 0 for r in results)
