from __future__ import annotations
import argparse, json
from pathlib import Path
from evaluator.task_loader import discover_tasks, validate_task_mix
from evaluator.runner import run_one, load_json
from evaluator.reporting.json_report import write_json
from evaluator.reporting.csv_report import write_csv
from evaluator.scoring.cost import cost_per_success
from evaluator.scoring.latency import percentile


def cmd_validate_tasks(args):
    tasks = discover_tasks(args.task_root)
    result = validate_task_mix(tasks, args.required_java_ratio)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    if not result['ok']:
        raise SystemExit(2)


def cmd_list_tasks(args):
    for t in discover_tasks(args.task_root):
        print(f"{t['id']}	{t.get('language')}	{t.get('category')}	{t.get('difficulty')}")


def cmd_run(args):
    models_config = load_json(args.models_config)
    if args.model not in models_config.get('models', {}):
        known = ', '.join(sorted(models_config.get('models', {}).keys())) or '(none)'
        raise SystemExit(f"unknown model: {args.model}. Available models: {known}")
    if args.limit is not None and args.limit <= 0:
        raise SystemExit('--limit must be a positive integer when provided')
    if args.repetitions <= 0:
        raise SystemExit('--repetitions must be a positive integer')

    tasks = discover_tasks(args.task_root)
    if args.language:
        tasks = [t for t in tasks if t.get('language') == args.language]
    if args.limit is not None:
        tasks = tasks[:args.limit]

    results = []
    for rep in range(1, args.repetitions + 1):
        for task in tasks:
            print(f"RUN {task['id']} model={args.model} repetition={rep}")
            results.append(run_one(task, args.model, models_config, rep))
    print(json.dumps({'runs': len(results), 'successes': sum(1 for r in results if r['success'])}, indent=2))


def summarize_results(results_dir: Path) -> dict:
    rows = []
    for p in sorted(results_dir.glob('*.json')):
        rows.append(json.loads(p.read_text(encoding='utf-8')))
    total = len(rows)
    success = sum(1 for r in rows if r.get('success'))
    java_rows = [r for r in rows if r.get('language') == 'java']
    java_success = sum(1 for r in java_rows if r.get('success'))
    violation_tasks = sum(1 for r in rows if r.get('constraint_violations'))
    critical_violation_tasks = sum(1 for r in rows if any(v.get('severity') == 'critical' for v in r.get('constraint_violations', [])))
    costs = [float(r.get('cost_usd') or 0.0) for r in rows]
    latencies = [float(r.get('latency_seconds') or 0.0) for r in rows]
    return {
        'total_runs': total,
        'successful_runs': success,
        'overall_success_rate': None if total == 0 else success / total,
        'java_runs': len(java_rows),
        'java_success_rate': None if not java_rows else java_success / len(java_rows),
        'constraint_violation_rate': None if total == 0 else violation_tasks / total,
        'critical_constraint_violation_rate': None if total == 0 else critical_violation_tasks / total,
        'total_cost_usd': sum(costs),
        'cost_per_success_usd': cost_per_success(sum(costs), success),
        'p50_latency_seconds': percentile(latencies, 0.50),
        'p90_latency_seconds': percentile(latencies, 0.90),
        'p95_latency_seconds': percentile(latencies, 0.95),
    }


def cmd_summarize(args):
    summary = summarize_results(Path(args.results_dir))
    write_json(Path(args.output_json), summary)
    rows = []
    for p in sorted(Path(args.results_dir).glob('*.json')):
        r = json.loads(p.read_text(encoding='utf-8'))
        rows.append({k: r.get(k) for k in ['run_id','task_id','language','category','difficulty','model','success','cost_usd','latency_seconds','total_seconds']})
    write_csv(Path(args.output_csv), rows)
    print(json.dumps(summary, indent=2, ensure_ascii=False))


def main():
    parser = argparse.ArgumentParser(description='Vendor-neutral code model evaluator')
    sub = parser.add_subparsers(required=True)

    p = sub.add_parser('validate-tasks')
    p.add_argument('--task-root', default='tasks')
    p.add_argument('--required-java-ratio', type=float, default=0.8)
    p.set_defaults(func=cmd_validate_tasks)

    p = sub.add_parser('list-tasks')
    p.add_argument('--task-root', default='tasks')
    p.set_defaults(func=cmd_list_tasks)

    p = sub.add_parser('run')
    p.add_argument('--model', required=True)
    p.add_argument('--models-config', default='configs/models.json')
    p.add_argument('--task-root', default='tasks')
    p.add_argument('--language')
    p.add_argument('--limit', type=int)
    p.add_argument('--repetitions', type=int, default=1)
    p.set_defaults(func=cmd_run)

    p = sub.add_parser('summarize')
    p.add_argument('--results-dir', default='results/raw')
    p.add_argument('--output-json', default='results/reports/summary.json')
    p.add_argument('--output-csv', default='results/reports/runs.csv')
    p.set_defaults(func=cmd_summarize)

    args = parser.parse_args()
    args.func(args)


if __name__ == '__main__':
    main()
