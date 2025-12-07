---
description: Delegate a task to a headless agent (Gemini, Claude, or Codex).
usage: /delegate <prompt> --agent <agent_name> [--effort high] [--parent_task_id <id>]
---

# Delegate Task

This command delegates a task to a background agent using the orchestration skill.

## Usage

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/delegate_task.py --prompt "$1" "${@:2}"
```

## Arguments

-   `prompt`: The task description or instruction.
-   `--agent`: The agent to use (`gemini`, `claude`, `codex`).
-   `--effort`: (Optional) `high` (for smarter models) or `standard` (default, faster).
-   `--sandbox`: (Optional) Run in a sandbox.
-   `--report`: (Optional) Generate a detailed report.
-   `--parent_task_id`: (Optional) Resume context from a previous task.

## Examples

Delegate a research task to Gemini:
`/delegate "Research the best libraries for React state management" --agent gemini`

Delegate a complex coding task to Codex with high effort:
`/delegate "Refactor the authentication module" --agent codex --effort high`
