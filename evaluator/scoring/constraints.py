from __future__ import annotations
from pathlib import Path
import fnmatch, subprocess


CRITICAL_PATTERNS = ['-DskipTests', 'maven.test.skip', '@Disabled', '@Ignore', 'System.exit(0)']


def check_constraints(task: dict, work_dir: Path, model_text: str) -> list[dict]:
    violations = []
    text = model_text or ''
    for pat in task.get('constraints', {}).get('forbid_patterns', []) + CRITICAL_PATTERNS:
        if pat and pat in text:
            violations.append({'severity': 'critical', 'type': 'forbid_pattern', 'detail': pat})

    repo_dir = work_dir / 'repo'
    try:
        diff = subprocess.run('git diff --name-only', cwd=str(repo_dir), shell=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=10)
        changed = [line.strip() for line in diff.stdout.splitlines() if line.strip()]
    except Exception:
        changed = []

    for pattern in task.get('constraints', {}).get('forbid_modify', []):
        for f in changed:
            if fnmatch.fnmatch(f, pattern):
                violations.append({'severity': 'critical', 'type': 'forbid_modify', 'detail': f})

    required = task.get('constraints', {}).get('require_files_changed', [])
    for pattern in required:
        if changed and not any(fnmatch.fnmatch(f, pattern) for f in changed):
            violations.append({'severity': 'major', 'type': 'required_change_missing', 'detail': pattern})
    return violations
