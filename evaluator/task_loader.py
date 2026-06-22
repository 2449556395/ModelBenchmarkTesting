from __future__ import annotations
from pathlib import Path
import json


def load_task(path: Path) -> dict:
    task_file = path / 'task.json'
    if not task_file.exists():
        raise FileNotFoundError(f'missing task.json: {task_file}')
    data = json.loads(task_file.read_text(encoding='utf-8'))
    data['_task_dir'] = str(path)
    return data


def discover_tasks(task_root: str = 'tasks') -> list[dict]:
    root = Path(task_root)
    tasks = []
    for task_file in sorted(root.glob('*/*/task.json')):
        tasks.append(load_task(task_file.parent))
    return tasks


def validate_task_mix(tasks: list[dict], required_java_ratio: float = 0.8) -> dict:
    total = len(tasks)
    java = sum(1 for t in tasks if t.get('language') == 'java')
    non_java = total - java
    ratio = java / total if total else 0.0
    return {
        'total': total,
        'java': java,
        'non_java': non_java,
        'java_ratio': ratio,
        'required_java_ratio': required_java_ratio,
        'ok': total > 0 and abs(ratio - required_java_ratio) < 1e-9,
    }
