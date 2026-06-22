from __future__ import annotations
from pathlib import Path
import shutil, subprocess, time


def prepare_workdir(task: dict, run_id: str) -> Path:
    src = Path(task['_task_dir'])
    dst = Path('.work') / run_id
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst, ignore=shutil.ignore_patterns('hidden_tests'))
    return dst


def run_command(command: str, cwd: Path, timeout: int) -> dict:
    start = time.time()
    proc = subprocess.run(command, cwd=str(cwd), shell=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=timeout)
    return {'command': command, 'exit_code': proc.returncode, 'output': proc.stdout[-12000:], 'seconds': time.time() - start}
