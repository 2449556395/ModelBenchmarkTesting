from __future__ import annotations
from pathlib import Path
import json, time, uuid, subprocess
from evaluator.model_clients.factory import create_client
from evaluator.prompting import build_prompt
from evaluator.sandbox import prepare_workdir
from evaluator.scoring.tests import run_task_commands, tests_pass
from evaluator.scoring.constraints import check_constraints
from evaluator.scoring.human_review import empty_review
from evaluator.reporting.json_report import write_json


def load_json(path: str) -> dict:
    return json.loads(Path(path).read_text(encoding='utf-8'))


def init_git_repo(repo_dir: Path):
    subprocess.run('git init -q', cwd=str(repo_dir), shell=True, check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    subprocess.run('git add . && git commit -q -m baseline', cwd=str(repo_dir), shell=True, check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def run_one(task: dict, model_name: str, models_config: dict, repetition: int = 1) -> dict:
    run_id = f"{task['id']}__{model_name}__r{repetition}__{uuid.uuid4().hex[:8]}"
    work_dir = prepare_workdir(task, run_id)
    repo_dir = work_dir / 'repo'
    init_git_repo(repo_dir)

    prompt = build_prompt(task, work_dir)
    client = create_client(model_name, models_config)
    start = time.time()
    response = client.generate(prompt, task)

    # MVP intentionally records model output but does not auto-apply arbitrary edits.
    # Production adapters should convert model responses into safe patches here.
    (work_dir / 'model_response.txt').write_text(response.text, encoding='utf-8')

    test_results = run_task_commands(task, work_dir)
    violations = check_constraints(task, work_dir, response.text)
    success = tests_pass(test_results) and not any(v['severity'] == 'critical' for v in violations)
    total_seconds = time.time() - start
    result = {
        'run_id': run_id,
        'task_id': task['id'],
        'language': task.get('language'),
        'category': task.get('category'),
        'difficulty': task.get('difficulty'),
        'model': model_name,
        'repetition': repetition,
        'success': success,
        'public_tests_pass': tests_pass(test_results),
        'hidden_tests_pass': None,
        'constraint_violations': violations,
        'cost_usd': response.cost_usd,
        'input_tokens': response.input_tokens,
        'output_tokens': response.output_tokens,
        'latency_seconds': response.latency_seconds,
        'total_seconds': total_seconds,
        'test_results': test_results,
        'human_review': empty_review(),
        'work_dir': str(work_dir),
    }
    out = Path('results/raw') / f'{run_id}.json'
    write_json(out, result)
    return result
