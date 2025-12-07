---
name: orchestration-skill
description: A skill for orchestrating headless agents (Claude, Gemini, Codex) using a "Fire and Forget" pattern to minimize context bloat.
version: 1.0.0
---

# Orchestration Skill

This skill enables the orchestration of other AI agents (Claude Code, Gemini CLI, Codex CLI) in a headless, asynchronous manner. It is designed to prevent context bloat in the orchestrator by strictly avoiding the consumption of background agent logs.

## Core Philosophy: "Fire and Forget"

1.  **Delegate**: The orchestrator launches a task and immediately releases the connection.
2.  **Isolate**: The worker agent runs in its own process, writing to its own log files.
3.  **Check**: The orchestrator periodically checks a lightweight status file, never the full logs.

## Tools

### `delegate_task`
Launches a new task with a specified agent.

**Usage:**
```bash
python3 scripts/delegate_task.py --agent claude --prompt "Refactor the login component"
# To resume context from a previous task:
python3 scripts/delegate_task.py --agent claude --prompt "Fix the bugs" --parent_task_id 12345
# To run in a sandbox:
python3 scripts/delegate_task.py --agent claude --prompt "Run tests" --sandbox
# To run in a sandbox:
python3 scripts/delegate_task.py --agent claude --prompt "Run tests" --sandbox
# To trigger high reasoning mode (Gemini 3 Pro / Claude Sonnet / Codex High Effort):
python3 scripts/delegate_task.py --agent gemini --prompt "Debug race condition" --effort high
# To generate a detailed report:
python3 scripts/delegate_task.py --agent claude --prompt "Audit security" --report
```

**Returns:**
A JSON object containing the `task_id` and `pid`.

### `check_status`
Checks the status of a specific task.

**Usage:**
```bash
python3 scripts/check_status.py --task_id <TASK_ID>
```

**Returns:**
A JSON object with `status` ("RUNNING", "COMPLETED", "FAILED") and `summary_file` path if complete.

### `list_active_tasks`
Lists all currently running tasks.

**Usage:**
```bash
python3 scripts/list_active_tasks.py
```

## Directory Structure

*   `logs/`: Stores all task logs and status files.
    *   `logs/raw/<task_id>.log`: Full stdout/stderr of the agent.
    *   `logs/status/<task_id>.status.json`: Structured status file.
    *   `logs/status/<task_id>.pid`: File containing the process ID (PID) of the agent task.
    *   `logs/results/<task_id>.summary.md`: Concise summary written by the agent.
    *   `logs/results/<task_id>_report.md`: Detailed report (if requested).

## Workflow Example

1.  **Orchestrator** decides to implement a feature.
2.  **Orchestrator** calls `delegate_task.py`.
3.  **Orchestrator** receives `task_id: "12345"`.
4.  **Orchestrator** continues with other work or waits.
5.  **Orchestrator** calls `check_status.py --task_id 12345`.
6.  **Orchestrator** receives `status: "COMPLETED"`.
7.  **Orchestrator** reads `logs/12345.summary.md` to verify the result.

## Rules of Engagement

To maintain a clean and predictable environment, Orchestrators must adhere to the following rules:

1.  **NO Root File Creation**: Never instruct an agent to create a report or document in the project root (e.g., `PROJECT_STATUS.md`).
2.  **Targeted Output**: Always instruct agents to write their outputs to the pre-assigned `logs/results/<task_id>.summary.md` or `logs/results/<task_id>_report.md` path.
3.  **Containment**: Agents should only write to files if explicitly necessary for the task (e.g., refactoring code). Documentation and reports belong in `logs/results/`.
