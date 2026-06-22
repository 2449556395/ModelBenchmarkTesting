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

Required response format:
You MUST return actual code changes in one of the following machine-applicable formats.

Option A: unified diff, preferably fenced as ```diff. Example:
```diff
diff --git a/src/main/java/example/Foo.java b/src/main/java/example/Foo.java
--- a/src/main/java/example/Foo.java
+++ b/src/main/java/example/Foo.java
@@ -1,3 +1,3 @@
- old code
+ new code
```

Option B: JSON file edits, fenced as ```json. Example:
```json
{{
  "edits": [
    {{"path": "src/main/java/example/Foo.java", "content": "full replacement file content here"}}
  ]
}}
```

Important scoring rules:
- A plain explanation is not enough and will fail.
- If your response cannot be applied as a patch or JSON edits, the task fails.
- If no files are changed, the task fails.
- The final code must pass the configured tests such as Maven/JUnit.
- Do not delete tests, skip tests, disable tests, or violate constraints.
""".strip()
