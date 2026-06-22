from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path
from typing import Any


def _run(cmd: list[str], cwd: Path, timeout: int = 30) -> subprocess.CompletedProcess:
    return subprocess.run(
        cmd,
        cwd=str(cwd),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=timeout,
        check=False,
    )


def _git_diff(repo_dir: Path) -> tuple[list[str], str]:
    names = _run(["git", "diff", "--name-only"], repo_dir)
    diff = _run(["git", "diff", "--"], repo_dir)
    changed = [line.strip() for line in names.stdout.splitlines() if line.strip()]
    return changed, diff.stdout


def _strip_fence(text: str) -> str:
    text = text.strip()
    m = re.fullmatch(r"```(?:json|diff|patch)?\s*(.*?)\s*```", text, flags=re.S)
    return m.group(1).strip() if m else text


def extract_unified_diff(model_text: str) -> str | None:
    text = model_text or ""

    fenced = re.findall(r"```(?:diff|patch)\s*(.*?)```", text, flags=re.S | re.I)
    for block in fenced:
        block = block.strip()
        if "diff --git " in block or re.search(r"^---\s+", block, flags=re.M):
            return block + "\n"

    idx = text.find("diff --git ")
    if idx >= 0:
        return text[idx:].strip() + "\n"

    # Some models return a bare unified diff without `diff --git`.
    if re.search(r"^---\s+", text, flags=re.M) and re.search(r"^\+\+\+\s+", text, flags=re.M) and re.search(r"^@@", text, flags=re.M):
        return text.strip() + "\n"

    return None


def _candidate_json_strings(model_text: str) -> list[str]:
    text = model_text or ""
    out: list[str] = []

    for block in re.findall(r"```json\s*(.*?)```", text, flags=re.S | re.I):
        out.append(block.strip())

    stripped = text.strip()
    if stripped.startswith("{") or stripped.startswith("["):
        out.append(stripped)

    # Last resort: first top-level-looking object containing "edits".
    m = re.search(r"(\{.*\"edits\".*\})", text, flags=re.S)
    if m:
        out.append(m.group(1).strip())

    return out


def extract_json_edits(model_text: str) -> list[dict[str, Any]] | None:
    for candidate in _candidate_json_strings(model_text):
        try:
            data = json.loads(_strip_fence(candidate))
        except Exception:
            continue

        if isinstance(data, dict):
            edits = data.get("edits") or data.get("files") or data.get("file_edits")
        elif isinstance(data, list):
            edits = data
        else:
            edits = None

        if not isinstance(edits, list):
            continue

        normalized: list[dict[str, Any]] = []
        for edit in edits:
            if not isinstance(edit, dict):
                continue
            path = edit.get("path") or edit.get("file") or edit.get("filename")
            content = edit.get("content") if "content" in edit else edit.get("text")
            if isinstance(path, str) and isinstance(content, str):
                normalized.append({"path": path, "content": content})
        if normalized:
            return normalized

    return None


def _safe_target(repo_dir: Path, rel_path: str) -> Path:
    rel = Path(rel_path)
    if rel.is_absolute():
        raise ValueError(f"absolute paths are not allowed: {rel_path}")
    if any(part in {"..", ""} for part in rel.parts):
        raise ValueError(f"path traversal is not allowed: {rel_path}")

    target = (repo_dir / rel).resolve()
    root = repo_dir.resolve()
    if root not in target.parents and target != root:
        raise ValueError(f"path escapes repo: {rel_path}")
    return target


def apply_json_edits(repo_dir: Path, edits: list[dict[str, Any]]) -> tuple[bool, str]:
    if not edits:
        return False, "no JSON edits found"

    for edit in edits:
        target = _safe_target(repo_dir, str(edit["path"]))
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(str(edit["content"]), encoding="utf-8")

    return True, ""


def apply_unified_diff(repo_dir: Path, diff_text: str) -> tuple[bool, str]:
    if not diff_text or not diff_text.strip():
        return False, "empty diff"

    check = subprocess.run(
        ["git", "apply", "--check", "-"],
        cwd=str(repo_dir),
        input=diff_text,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=30,
        check=False,
    )
    if check.returncode != 0:
        return False, (check.stderr or check.stdout or "git apply --check failed").strip()

    apply = subprocess.run(
        ["git", "apply", "-"],
        cwd=str(repo_dir),
        input=diff_text,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=30,
        check=False,
    )
    if apply.returncode != 0:
        return False, (apply.stderr or apply.stdout or "git apply failed").strip()

    return True, ""


def apply_model_changes(model_text: str, repo_dir: Path) -> dict[str, Any]:
    """
    Apply model-provided edits to repo_dir.

    Supported model response formats:
    1. Unified diff, optionally fenced as ```diff.
    2. JSON edits:
       {"edits": [{"path": "src/main/...", "content": "full file content"}]}

    Returns a dict intentionally suitable for persistence in run results.
    """
    before_files, before_diff = _git_diff(repo_dir)
    assert not before_diff, "repo should be clean before applying model changes"

    method = None
    patch_applied = False
    patch_error = ""

    diff_text = extract_unified_diff(model_text)
    if diff_text:
        method = "unified_diff"
        patch_applied, patch_error = apply_unified_diff(repo_dir, diff_text)
    else:
        edits = extract_json_edits(model_text)
        if edits:
            method = "json_edits"
            try:
                patch_applied, patch_error = apply_json_edits(repo_dir, edits)
            except Exception as exc:
                patch_applied, patch_error = False, str(exc)
        else:
            method = "none"
            patch_applied = False
            patch_error = "model response did not contain a unified diff or JSON edits"

    files_changed, final_diff = _git_diff(repo_dir)

    if patch_applied and not files_changed:
        patch_applied = False
        patch_error = "patch applied but produced no actual git diff"

    return {
        "patch_method": method,
        "patch_applied": patch_applied,
        "patch_error": patch_error,
        "files_changed": files_changed,
        "final_diff": final_diff,
    }