from __future__ import annotations
from pathlib import Path


def build_prompt(task: dict, work_dir: Path) -> str:
    repo_dir = work_dir / 'repo'
    files = []
    if repo_dir.exists():
        for p in sorted(repo_dir.rglob('*')):
            if p.is_file() and p.stat().st_size < 20000 and not any(part.startswith('.') for part in p.parts):
                rel = p.relative_to(repo_dir)
                if rel.suffix in {'.java', '.xml', '.py', '.js', '.ts', '.md', '.properties', '.yml', '.yaml', '.json'}:
                    try:
                        files.append(f"--- FILE: {rel} ---\n{p.read_text(encoding='utf-8', errors='replace')}")
                    except Exception:
                        pass
    constraint_text = '\n'.join(f"- {c}" for c in task.get('constraints', {}).get('human', []))
    return f"""
Task ID: {task['id']}
Language: {task.get('language')}
Category: {task.get('category')}
Difficulty: {task.get('difficulty')}

Instruction:
{task.get('prompt', '')}

Constraints:
{constraint_text}

Repository snapshot:
{chr(10).join(files[:80])}

Return either a unified diff or precise file replacement instructions. Do not delete tests, skip tests, or violate constraints.
""".strip()
