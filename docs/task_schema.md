# Task Schema

每个任务目录包含 `task.json`。核心字段：

- `id`: 全局唯一任务 ID
- `language`: `java` 或其他语言
- `framework`: 技术栈标签，例如 `spring-boot`, `junit5`, `maven`
- `category`: `feature_change` / `bugfix` / `test_completion` / `build_fix` / `refactor` / `security` 等
- `difficulty`: `easy` / `medium` / `hard`
- `prompt`: 给模型的任务说明
- `commands.test`: 自动化测试命令
- `constraints.forbid_modify`: 禁止修改的 glob
- `constraints.forbid_patterns`: 禁止出现在模型输出或代码中的模式
- `constraints.require_files_changed`: 需要修改的 glob
- `limits`: 超时、成本、最大迭代等
