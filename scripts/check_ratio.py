#!/usr/bin/env python3
from evaluator.task_loader import discover_tasks, validate_task_mix
import json
print(json.dumps(validate_task_mix(discover_tasks('tasks')), indent=2, ensure_ascii=False))
