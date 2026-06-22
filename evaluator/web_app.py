from __future__ import annotations

import argparse
import json
import os
import re
import threading
import time
import traceback
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from evaluator.runner import run_one
from evaluator.task_loader import discover_tasks, validate_task_mix
from evaluator.reporting.json_report import write_json

PROJECT_ROOT = Path(__file__).resolve().parents[1]
WEB_RUNS_DIR = PROJECT_ROOT / "results" / "web_runs"

JOBS: dict[str, dict] = {}
JOB_SECRETS: dict[str, dict] = {}
JOBS_LOCK = threading.Lock()


def percentile(values: list[float], pct: float):
    if not values:
        return None
    ordered = sorted(values)
    idx = int(round((len(ordered) - 1) * pct))
    return ordered[max(0, min(idx, len(ordered) - 1))]


def safe_model_key(name: str | None) -> str:
    value = re.sub(r"[^A-Za-z0-9_.-]+", "-", (name or "web-model").strip()).strip("-")
    return value[:60] or "web-model"


def summarize_results(results: list[dict]) -> dict:
    total = len(results)
    successes = sum(1 for r in results if r.get("success"))
    java_results = [r for r in results if r.get("language") == "java"]
    java_successes = sum(1 for r in java_results if r.get("success"))

    with_violations = [r for r in results if r.get("constraint_violations")]
    with_critical = [
        r
        for r in results
        if any(v.get("severity") == "critical" for v in r.get("constraint_violations", []))
    ]

    total_cost = sum(float(r.get("cost_usd") or 0.0) for r in results)
    latencies = [
        float(r.get("latency_seconds") or 0.0)
        for r in results
        if r.get("latency_seconds") is not None
    ]

    task_groups: dict[str, list[bool]] = {}
    for r in results:
        task_groups.setdefault(r.get("task_id", "unknown"), []).append(bool(r.get("success")))
    stable_groups = sum(1 for vals in task_groups.values() if len(set(vals)) <= 1)

    return {
        "total_runs": total,
        "successful_runs": successes,
        "overall_success_rate": successes / total if total else None,
        "java_runs": len(java_results),
        "java_success_rate": java_successes / len(java_results) if java_results else None,
        "constraint_violation_rate": len(with_violations) / total if total else None,
        "critical_constraint_violation_rate": len(with_critical) / total if total else None,
        "total_cost_usd": round(total_cost, 6),
        "cost_per_success_usd": round(total_cost / successes, 6) if successes else None,
        "p50_latency_seconds": percentile(latencies, 0.50),
        "p90_latency_seconds": percentile(latencies, 0.90),
        "p95_latency_seconds": percentile(latencies, 0.95),
        "stability_score": stable_groups / len(task_groups) if task_groups else None,
        "task_count": len(task_groups),
    }


def public_task(task: dict) -> dict:
    return {
        "id": task.get("id"),
        "language": task.get("language"),
        "category": task.get("category"),
        "difficulty": task.get("difficulty"),
        "framework": task.get("framework", []),
        "real_repo": bool(task.get("real_repo")),
        "prompt": (task.get("prompt") or "")[:1200],
        "test_commands": task.get("commands", {}).get("test", []),
    }


def sanitized_job(job: dict | None):
    if not job:
        return None
    safe = {k: v for k, v in job.items() if not k.startswith("_")}
    return json.loads(json.dumps(safe, ensure_ascii=False))


def save_job_snapshot(job: dict):
    safe = sanitized_job(job)
    if not safe:
        return
    run_dir = WEB_RUNS_DIR / safe["id"]
    run_dir.mkdir(parents=True, exist_ok=True)
    write_json(run_dir / "job.json", safe)
    write_json(run_dir / "runs.json", {"results": safe.get("results", [])})
    write_json(run_dir / "summary.json", safe.get("summary", {}))


def update_job(job_id: str, **changes):
    with JOBS_LOCK:
        job = JOBS[job_id]
        job.update(changes)
        job["updated_at"] = time.time()
        snapshot = dict(job)
    save_job_snapshot(snapshot)


def get_job(job_id: str):
    with JOBS_LOCK:
        return sanitized_job(JOBS.get(job_id))


def build_models_config(payload: dict, model_key: str) -> dict:
    use_mock = (
        bool(payload.get("use_mock"))
        or payload.get("model_name") == "mock"
        or payload.get("model_id") == "mock"
    )
    if use_mock:
        return {"models": {model_key: {"type": "mock"}}}

    api_key = (payload.get("api_key") or "").strip()
    base_url = (payload.get("base_url") or "").strip()
    model_id = (payload.get("model_id") or payload.get("model_name") or "").strip()

    if not api_key:
        raise ValueError("API Key is required unless using mock model")
    if not base_url:
        raise ValueError("Base URL is required unless using mock model")
    if not model_id:
        raise ValueError("Model ID is required unless using mock model")

    cfg = {
        "type": "openai_compatible",
        "base_url": base_url,
        "api_key": api_key,
        "model": model_id,
        "temperature": float(payload.get("temperature", 0.2) or 0.2),
        "timeout_seconds": int(payload.get("timeout_seconds", 120) or 120),
        "input_cost_per_1k": float(payload.get("input_cost_per_1k", 0) or 0),
        "output_cost_per_1k": float(payload.get("output_cost_per_1k", 0) or 0),
    }

    thinking = (payload.get("thinking_level") or "").strip()
    if thinking and thinking.lower() not in {"none", "off", "default"}:
        cfg["reasoning_effort"] = thinking
        cfg["thinking_level"] = thinking

    return {"models": {model_key: cfg}}


def make_error_result(task: dict, model_key: str, rep: int, exc: Exception) -> dict:
    return {
        "run_id": f"{task['id']}__{model_key}__r{rep}__error__{uuid.uuid4().hex[:8]}",
        "task_id": task["id"],
        "language": task.get("language"),
        "category": task.get("category"),
        "difficulty": task.get("difficulty"),
        "model": model_key,
        "repetition": rep,
        "success": False,
        "public_tests_pass": False,
        "hidden_tests_pass": None,
        "constraint_violations": [
            {"severity": "critical", "type": "runner_exception", "message": str(exc)}
        ],
        "cost_usd": 0.0,
        "input_tokens": 0,
        "output_tokens": 0,
        "latency_seconds": 0.0,
        "total_seconds": 0.0,
        "test_results": [],
        "human_review": {},
        "work_dir": None,
        "error": str(exc),
    }


def run_job(job_id: str):
    os.chdir(PROJECT_ROOT)
    results: list[dict] = []

    try:
        with JOBS_LOCK:
            payload = dict(JOB_SECRETS.get(job_id, {}))

        all_tasks = discover_tasks(str(PROJECT_ROOT / "tasks"))
        task_by_id = {t["id"]: t for t in all_tasks}

        selected_ids = payload.get("task_ids") or [t["id"] for t in all_tasks]
        selected_tasks = []
        for task_id in selected_ids:
            if task_id not in task_by_id:
                raise ValueError(f"unknown task id: {task_id}")
            selected_tasks.append(task_by_id[task_id])

        repetitions = int(payload.get("repetitions", 1) or 1)
        if repetitions <= 0:
            raise ValueError("repetitions must be positive")

        model_display_name = payload.get("model_name") or payload.get("model_id") or "web-model"
        model_key = safe_model_key(model_display_name)
        if not payload.get("use_mock") and model_key == "mock":
            model_key = "web-model-" + uuid.uuid4().hex[:6]

        models_config = build_models_config(payload, model_key)
        total_units = len(selected_tasks) * repetitions

        update_job(
            job_id,
            status="running",
            total_units=total_units,
            completed_units=0,
            current_task=None,
            error=None,
        )

        completed = 0
        for rep in range(1, repetitions + 1):
            for task in selected_tasks:
                update_job(job_id, current_task=task["id"])

                try:
                    result = run_one(task, model_key, models_config, rep)
                    result["model_display_name"] = model_display_name
                    result["web_job_id"] = job_id
                except Exception as exc:
                    result = make_error_result(task, model_key, rep, exc)

                results.append(result)
                completed += 1
                update_job(
                    job_id,
                    results=results,
                    summary=summarize_results(results),
                    completed_units=completed,
                )

        update_job(
            job_id,
            status="completed",
            current_task=None,
            finished_at=time.time(),
            summary=summarize_results(results),
            results=results,
        )
    except Exception as exc:
        update_job(
            job_id,
            status="failed",
            error=str(exc),
            traceback=traceback.format_exc(),
            finished_at=time.time(),
            summary=summarize_results(results),
            results=results,
        )
    finally:
        with JOBS_LOCK:
            JOB_SECRETS.pop(job_id, None)
            if job_id in JOBS:
                JOBS[job_id].pop("_api_key", None)
                snapshot = dict(JOBS[job_id])
            else:
                snapshot = None
        if snapshot:
            save_job_snapshot(snapshot)


INDEX_HTML = """<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>ModelBenchmarkTesting Web Console</title>
  <style>
    body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; margin: 0; background: #f6f7fb; color: #172033; }
    header { background: #111827; color: white; padding: 18px 28px; }
    main { padding: 22px; max-width: 1320px; margin: auto; }
    .grid { display: grid; grid-template-columns: 380px 1fr; gap: 18px; align-items: start; }
    .card { background: white; border: 1px solid #e5e7eb; border-radius: 14px; padding: 18px; box-shadow: 0 1px 2px rgba(0,0,0,.04); }
    label { display: block; font-weight: 650; margin-top: 12px; font-size: 13px; }
    input, select, button { font: inherit; }
    input, select { width: 100%; box-sizing: border-box; border: 1px solid #cfd5df; border-radius: 9px; padding: 9px 10px; margin-top: 5px; }
    button { border: 0; border-radius: 9px; padding: 10px 14px; background: #2563eb; color: white; cursor: pointer; font-weight: 700; }
    button.secondary { background: #4b5563; }
    button:disabled { opacity: .55; cursor: not-allowed; }
    .task-list { max-height: 520px; overflow: auto; border: 1px solid #e5e7eb; border-radius: 10px; }
    .task { padding: 10px 12px; border-bottom: 1px solid #eef0f4; display: grid; grid-template-columns: 24px 1fr; gap: 8px; }
    .muted { color: #667085; font-size: 12px; }
    .pill { display: inline-block; padding: 2px 7px; border-radius: 999px; background: #eef2ff; color: #3730a3; font-size: 11px; margin-right: 4px; }
    .metrics { display: grid; grid-template-columns: repeat(4, minmax(140px, 1fr)); gap: 10px; }
    .metric { background: #f9fafb; border: 1px solid #e5e7eb; border-radius: 12px; padding: 12px; }
    .metric .v { font-size: 24px; font-weight: 800; margin-top: 4px; }
    progress { width: 100%; height: 18px; }
    table { width: 100%; border-collapse: collapse; font-size: 13px; }
    th, td { padding: 8px; border-bottom: 1px solid #e5e7eb; text-align: left; vertical-align: top; }
    th { background: #f9fafb; position: sticky; top: 0; }
    .ok { color: #047857; font-weight: 800; }
    .bad { color: #b91c1c; font-weight: 800; }
    .row { display: flex; gap: 8px; align-items: center; flex-wrap: wrap; }
    .notice { background: #fff7ed; border: 1px solid #fed7aa; border-radius: 12px; padding: 10px 12px; color: #9a3412; }
    pre { white-space: pre-wrap; background: #0b1020; color: #d1e7ff; padding: 12px; border-radius: 10px; overflow: auto; }
  </style>
</head>
<body>
<header>
  <h2 style="margin:0">ModelBenchmarkTesting Web Console</h2>
  <div class="muted" style="color:#cbd5e1">输入模型 API 参数，选择真实工程任务，自动运行 Maven/JUnit，并生成采购评估指标。</div>
</header>
<main>
  <div class="grid">
    <section class="card">
      <h3>1. 模型配置</h3>
      <div class="notice">API Key 仅用于本次运行，不写入结果文件。若勾选 mock，则无需 Key/URL。</div>
      <label><input type="checkbox" id="useMock" style="width:auto" checked /> 使用 mock 模型测试页面链路</label>
      <label>显示名称</label><input id="modelName" value="mock" placeholder="例如 GPT-4.1-Code" />
      <label>模型 ID</label><input id="modelId" value="mock" placeholder="例如 gpt-4.1 或 vendor/model" />
      <label>Base URL</label><input id="baseUrl" placeholder="例如 https://api.example.com/v1/chat/completions" />
      <label>API Key</label><input id="apiKey" type="password" placeholder="不会保存到磁盘" />
      <label>思考级别</label>
      <select id="thinkingLevel"><option value="none">默认/不传</option><option value="low">low</option><option value="medium">medium</option><option value="high">high</option></select>
      <div class="row">
        <div style="flex:1"><label>输入价格 / 1K tokens</label><input id="inputCost" type="number" step="0.000001" value="0" /></div>
        <div style="flex:1"><label>输出价格 / 1K tokens</label><input id="outputCost" type="number" step="0.000001" value="0" /></div>
      </div>
      <div class="row">
        <div style="flex:1"><label>重复次数</label><input id="repetitions" type="number" min="1" value="1" /></div>
        <div style="flex:1"><label>温度</label><input id="temperature" type="number" step="0.1" value="0.2" /></div>
      </div>
      <label>超时秒数</label><input id="timeoutSeconds" type="number" min="10" value="120" />
      <hr />
      <h3>2. 选择题目</h3>
      <div class="row" style="margin-bottom:8px">
        <button class="secondary" onclick="selectAll(true)">全选</button>
        <button class="secondary" onclick="selectAll(false)">全不选</button>
        <button class="secondary" onclick="selectJava()">只选 Java</button>
      </div>
      <div id="taskList" class="task-list">加载中...</div>
      <div class="row" style="margin-top:14px">
        <button id="startBtn" onclick="startRun()">开始测试</button>
      </div>
    </section>

    <section class="card">
      <h3>3. 运行状态与采购报告</h3>
      <div id="runStatus" class="muted">尚未开始。</div>
      <progress id="progress" value="0" max="1"></progress>
      <div id="metrics" class="metrics" style="margin-top:14px"></div>
      <h3>明细</h3>
      <div style="max-height:520px; overflow:auto"><table id="runsTable"><thead></thead><tbody></tbody></table></div>
      <h3>原始 Summary JSON</h3>
      <pre id="summaryJson">{}</pre>
    </section>
  </div>
</main>
<script>
let tasks = [];
let currentJobId = null;
let pollTimer = null;

function fmtPct(v){ return v === null || v === undefined ? '-' : (v*100).toFixed(1)+'%'; }
function fmtNum(v){ return v === null || v === undefined ? '-' : (Math.round(v*1000)/1000).toString(); }
function esc(s){ return String(s ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c])); }

async function loadTasks(){
  const res = await fetch('/api/tasks');
  const data = await res.json();
  tasks = data.tasks || [];
  renderTasks();
}

function renderTasks(){
  const box = document.getElementById('taskList');
  box.innerHTML = tasks.map(t => `<label class="task"><input type="checkbox" class="taskCb" value="${esc(t.id)}" ${t.language==='java'?'checked':''}/><div><b>${esc(t.id)}</b><div class="muted"><span class="pill">${esc(t.language)}</span><span class="pill">${esc(t.category)}</span><span class="pill">${esc(t.difficulty)}</span>${t.real_repo?'<span class="pill">real_repo</span>':''}</div><div class="muted">${esc((t.prompt||'').slice(0,140))}</div></div></label>`).join('');
}

function selectAll(on){ document.querySelectorAll('.taskCb').forEach(cb => cb.checked = on); }
function selectJava(){ document.querySelectorAll('.taskCb').forEach(cb => { const t = tasks.find(x=>x.id===cb.value); cb.checked = t && t.language === 'java'; }); }

document.getElementById('useMock').addEventListener('change', e => {
  if(e.target.checked){
    document.getElementById('modelName').value='mock';
    document.getElementById('modelId').value='mock';
  }
});

async function startRun(){
  const ids = [...document.querySelectorAll('.taskCb:checked')].map(cb => cb.value);
  if(ids.length === 0){ alert('请至少选择一个题目'); return; }

  const payload = {
    use_mock: document.getElementById('useMock').checked,
    model_name: document.getElementById('modelName').value,
    model_id: document.getElementById('modelId').value,
    base_url: document.getElementById('baseUrl').value,
    api_key: document.getElementById('apiKey').value,
    thinking_level: document.getElementById('thinkingLevel').value,
    input_cost_per_1k: Number(document.getElementById('inputCost').value || 0),
    output_cost_per_1k: Number(document.getElementById('outputCost').value || 0),
    repetitions: Number(document.getElementById('repetitions').value || 1),
    temperature: Number(document.getElementById('temperature').value || 0.2),
    timeout_seconds: Number(document.getElementById('timeoutSeconds').value || 120),
    task_ids: ids,
  };

  document.getElementById('startBtn').disabled = true;
  const res = await fetch('/api/runs', {
    method:'POST',
    headers:{'Content-Type':'application/json'},
    body: JSON.stringify(payload)
  });
  const data = await res.json();
  if(!res.ok){
    alert(data.error || '启动失败');
    document.getElementById('startBtn').disabled = false;
    return;
  }

  currentJobId = data.id;
  poll();
  if(pollTimer) clearInterval(pollTimer);
  pollTimer = setInterval(poll, 1500);
}

async function poll(){
  if(!currentJobId) return;
  const res = await fetch('/api/runs/'+currentJobId);
  const job = await res.json();
  renderJob(job);
  if(['completed','failed'].includes(job.status)){
    clearInterval(pollTimer);
    pollTimer=null;
    document.getElementById('startBtn').disabled = false;
  }
}

function renderJob(job){
  const completed = job.completed_units || 0, total = job.total_units || 1;
  document.getElementById('progress').max = total;
  document.getElementById('progress').value = completed;
  document.getElementById('runStatus').innerHTML =
    `状态：<b>${esc(job.status)}</b> | ${completed}/${total} | 当前：${esc(job.current_task || '-')} | Run ID: ${esc(job.id || '-')}` +
    (job.error ? `<div class="bad">${esc(job.error)}</div>` : '');

  const s = job.summary || {};
  const cards = [
    ['总体成功率', fmtPct(s.overall_success_rate)], ['Java成功率', fmtPct(s.java_success_rate)],
    ['约束违规率', fmtPct(s.constraint_violation_rate)], ['Critical违规率', fmtPct(s.critical_constraint_violation_rate)],
    ['总成本USD', fmtNum(s.total_cost_usd)], ['成功单价USD', fmtNum(s.cost_per_success_usd)],
    ['P50延迟秒', fmtNum(s.p50_latency_seconds)], ['稳定性', fmtPct(s.stability_score)]
  ];
  document.getElementById('metrics').innerHTML =
    cards.map(([k,v]) => `<div class="metric"><div class="muted">${k}</div><div class="v">${v}</div></div>`).join('');
  document.getElementById('summaryJson').textContent = JSON.stringify(s, null, 2);

  const rows = job.results || [];
  document.querySelector('#runsTable thead').innerHTML =
    '<tr><th>题目</th><th>语言</th><th>成功</th><th>测试</th><th>Patch</th><th>修改文件</th><th>失败原因</th><th>违规</th><th>成本</th><th>延迟</th><th>Diff/错误</th></tr>';
  document.querySelector('#runsTable tbody').innerHTML = rows.map(r => {
    const files = (r.files_changed || []).join('<br>');
    const reasons = (r.failure_reasons || []).join('<br>');
    const patchState = r.patch_applied ? 'APPLIED' : 'NOT APPLIED';
    const diffPreview = (r.final_diff || '').slice(0, 1200);
    const detail = r.patch_error || r.error || diffPreview || '';
    return `<tr><td>${esc(r.task_id)}</td><td>${esc(r.language)}</td><td class="${r.success?'ok':'bad'}">${r.success?'PASS':'FAIL'}</td><td>${r.public_tests_pass?'PASS':'FAIL'}</td><td class="${r.patch_applied?'ok':'bad'}">${patchState}<br><span class="muted">${esc(r.patch_method || '')}</span></td><td>${files || '-'}</td><td class="bad">${reasons || '-'}</td><td>${(r.constraint_violations||[]).length}</td><td>${fmtNum(r.cost_usd)}</td><td>${fmtNum(r.latency_seconds)}</td><td><pre style="max-height:180px">${esc(detail)}</pre></td></tr>`;
  }).join('');
}

loadTasks().catch(err => { document.getElementById('taskList').textContent = String(err); });
</script>
</body>
</html>
"""


class Handler(BaseHTTPRequestHandler):
    server_version = "ModelBenchmarkWeb/0.1"

    def log_message(self, fmt, *args):
        print("%s - - [%s] %s" % (self.address_string(), self.log_date_time_string(), fmt % args))

    def send_body(self, status: int, body: bytes, content_type: str = "application/json; charset=utf-8"):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def send_json(self, status: int, data: dict):
        self.send_body(status, json.dumps(data, indent=2, ensure_ascii=False).encode("utf-8"))

    def read_json(self) -> dict:
        length = int(self.headers.get("Content-Length") or 0)
        if length <= 0:
            return {}
        return json.loads(self.rfile.read(length).decode("utf-8"))

    def do_GET(self):
        path = urlparse(self.path).path

        if path == "/":
            self.send_body(200, INDEX_HTML.encode("utf-8"), "text/html; charset=utf-8")
            return

        if path == "/api/tasks":
            tasks = discover_tasks(str(PROJECT_ROOT / "tasks"))
            self.send_json(200, {"tasks": [public_task(t) for t in tasks], "mix": validate_task_mix(tasks)})
            return

        m = re.fullmatch(r"/api/runs/([A-Za-z0-9_.-]+)/report", path)
        if m:
            job = get_job(m.group(1))
            if not job:
                self.send_json(404, {"error": "job not found"})
            else:
                self.send_json(200, {"summary": job.get("summary", {}), "results": job.get("results", [])})
            return

        m = re.fullmatch(r"/api/runs/([A-Za-z0-9_.-]+)", path)
        if m:
            job = get_job(m.group(1))
            if not job:
                self.send_json(404, {"error": "job not found"})
            else:
                self.send_json(200, job)
            return

        self.send_json(404, {"error": "not found"})

    def do_POST(self):
        path = urlparse(self.path).path
        if path != "/api/runs":
            self.send_json(404, {"error": "not found"})
            return

        try:
            payload = self.read_json()
            job_id = "web_" + uuid.uuid4().hex[:12]
            safe_request = {k: v for k, v in payload.items() if k != "api_key"}

            job = {
                "id": job_id,
                "status": "queued",
                "request": safe_request,
                "created_at": time.time(),
                "updated_at": time.time(),
                "total_units": 0,
                "completed_units": 0,
                "current_task": None,
                "results": [],
                "summary": {},
                "error": None,
            }

            with JOBS_LOCK:
                JOBS[job_id] = job
                JOB_SECRETS[job_id] = dict(payload)

            save_job_snapshot(job)
            thread = threading.Thread(target=run_job, args=(job_id,), name="web-eval-" + job_id, daemon=True)
            thread.start()
            self.send_json(202, {"id": job_id, "status": "queued"})
        except Exception as exc:
            self.send_json(400, {"error": str(exc)})


def main():
    parser = argparse.ArgumentParser(description="Local Web UI for ModelBenchmarkTesting")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()

    os.chdir(PROJECT_ROOT)
    WEB_RUNS_DIR.mkdir(parents=True, exist_ok=True)

    server = ThreadingHTTPServer((args.host, args.port), Handler)
    print("Open http://%s:%s" % (args.host, args.port))
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping...")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()