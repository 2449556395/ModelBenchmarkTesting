from __future__ import annotations

from pathlib import Path
import json
import time
import uuid
import subprocess

from evaluator.model_clients.factory import create_client
from evaluator.prompting import build_prompt
from evaluator.sandbox import prepare_workdir
from evaluator.scoring.tests import run_task_commands, tests_pass
from evaluator.scoring.constraints import check_constraints
from evaluator.scoring.human_review import empty_review
from evaluator.reporting.json_report import write_json
from evaluator.patching import apply_model_changes


def load_json(path: str) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def init_git_repo(repo_dir: Path):
    subprocess.run(
        "git init -q",
        cwd=str(repo_dir),
        shell=True,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    subprocess.run(
        "git config user.email evaluator@example.local && git config user.name Evaluator",
        cwd=str(repo_dir),
        shell=True,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    subprocess.run(
        "git add . && git commit -q -m baseline",
        cwd=str(repo_dir),
        shell=True,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def has_major_or_critical(violations: list[dict]) -> bool:
    return any(v.get("severity") in {"major", "critical"} for v in violations)


def run_one(task: dict, model_name: str, models_config: dict, repetition: int = 1) -> dict:
    run_id = f"{task['id']}__{model_name}__r{repetition}__{uuid.uuid4().hex[:8]}"
    work_dir = prepare_workdir(task, run_id)
    repo_dir = work_dir / "repo"
    init_git_repo(repo_dir)

    prompt = build_prompt(task, work_dir)
    client = create_client(model_name, models_config)

    start = time.time()

    # Baseline is informational: it helps reviewers see whether the initial repo
    # already passed. Final success is always computed after applying model edits.
    baseline_test_results = run_task_commands(task, work_dir)

    # Baseline commands such as Maven/JUnit may update generated files or leave
    # build artifacts. Reset the git worktree before applying model edits so
    # final_diff only represents the model-produced change.
    subprocess.run(
        "git reset --hard HEAD && git clean -fd",
        cwd=str(repo_dir),
        shell=True,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    response = client.generate(prompt, task)
    (work_dir / "model_response.txt").write_text(response.text, encoding="utf-8")

    patch_result = apply_model_changes(response.text, repo_dir)
    (work_dir / "final_diff.patch").write_text(patch_result.get("final_diff", ""), encoding="utf-8")

    test_results = run_task_commands(task, work_dir)
    violations = check_constraints(task, work_dir, response.text)

    public_tests_pass = tests_pass(test_results)
    changed_files = patch_result.get("files_changed", [])
    patch_applied = bool(patch_result.get("patch_applied"))
    major_or_critical_violation = has_major_or_critical(violations)

    success = (
        patch_applied
        and bool(changed_files)
        and public_tests_pass
        and not major_or_critical_violation
    )

    failure_reasons = []
    if not patch_applied:
        failure_reasons.append("patch_not_applied")
    if not changed_files:
        failure_reasons.append("no_files_changed")
    if not public_tests_pass:
        failure_reasons.append("tests_failed")
    if major_or_critical_violation:
        failure_reasons.append("major_or_critical_constraint_violation")

    total_seconds = time.time() - start
    result = {
        "run_id": run_id,
        "task_id": task["id"],
        "language": task.get("language"),
        "category": task.get("category"),
        "difficulty": task.get("difficulty"),
        "model": model_name,
        "repetition": repetition,
        "success": success,
        "public_tests_pass": public_tests_pass,
        "hidden_tests_pass": None,
        "constraint_violations": violations,
        "cost_usd": response.cost_usd,
        "input_tokens": response.input_tokens,
        "output_tokens": response.output_tokens,
        "latency_seconds": response.latency_seconds,
        "total_seconds": total_seconds,
        "baseline_test_results": baseline_test_results,
        "test_results": test_results,
        "patch_method": patch_result.get("patch_method"),
        "patch_applied": patch_applied,
        "patch_error": patch_result.get("patch_error", ""),
        "files_changed": changed_files,
        "final_diff": patch_result.get("final_diff", ""),
        "failure_reasons": failure_reasons,
        "human_review": empty_review(),
        "work_dir": str(work_dir),
    }
    out = Path("results/raw") / f"{run_id}.json"
    write_json(out, result)
    return result