---
name: orchestration-skill
description: A skill for orchestrating headless agents (Claude, Gemini, Codex) using a "Fire and Forget" pattern to minimize context bloat.
version: 1.0.0
---

# Orchestration Skill

Use this skill to orchestrate headless agents (Claude, Gemini, Codex) using an asynchronous "Fire and Forget" pattern. This approach prevents context bloat in the primary orchestrator by isolating background work and relying on lightweight status monitoring.

## Core Patterns

### "Fire and Forget" Delegation
1.  **Launch**: Delegate a task to a background worker and release the connection immediately.
2.  **Isolate**: Force workers to run in separate processes and write to unique log paths.
3.  **Monitor**: Periodically check the structured JSON status files rather than raw logs.

## Tool Reference

### `delegate_task`
Initiate a new headless task with a background agent.

**Basic Usage:**
```bash
python3 scripts/delegate_task.py --agent claude --prompt "Implement the user profile API"
```

**Advanced Patterns:**
- **Resume Session**: Chain context by providing a `--parent_task_id <ID>`.
- **Sandbox Mode**: Isolate execution using `--sandbox`.
- **High Reasoning**: Use `--effort high` to escalate to premium models (e.g., `gemini-3-pro-preview`).
- **Detailed Audit**: Generate a deep report in `logs/results/` using `--report`.

**Agent Behaviors:**
- **Gemini**: Defaults to `gemini-3-flash-preview` for speed. Use `--effort high` for `gemini-3-pro-preview`.
- **Claude**: Defaults to `sonnet-4.5`.
- **Codex**: Defaults to `gpt-5.2` with medium effort.

### `check_status`
Retrieve the current state and results of a specific task.
```bash
python3 scripts/check_status.py --task_id <TASK_ID>
```

### `cancel_task`
Terminate a running task and its associated processes.
```bash
python3 scripts/cancel_task.py --task_id <TASK_ID>
```

### `list_active_tasks`
View all currently running orchestration tasks.
```bash
python3 scripts/list_active_tasks.py
```

### `status_vis`
Render a visual timeline or summary table of recent task activity.
```bash
python3 scripts/status_vis.py
```

## Operational Rules

1.  **Maintain Containment**: Never instruct agents to write files in the project root.
2.  **Redirect Output**: Enforce writing of summaries to `logs/results/<task_id>.summary.md`.
3.  **Asychronous-Only**: Avoid blocking the orchestrator while waiting for task completion.
4.  **Security**: Use `--sandbox` when executing untrusted or experimental code generation.
