---
name: orchestration-skill
description: Orchestrate headless agents (Claude, Codex, Antigravity) using a "Fire and Forget" pattern. Use this skill when the user wants to delegate tasks to other agents, run background work, launch parallel agents, or orchestrate multi-agent workflows. Also use when the user mentions delegation, background agents, orchestration, or wants to run something with a different AI agent.
version: 1.4.0
---

# Orchestration Skill

This skill enables the orchestration of other AI agents (Claude Code, Codex CLI, Antigravity) in a headless, asynchronous manner. It is designed to prevent context bloat in the orchestrator by strictly avoiding the consumption of background agent logs.

## Core Philosophy: "Fire and Forget"

1.  **Delegate**: The orchestrator launches a task and immediately releases the connection.
2.  **Isolate**: The worker agent runs in its own process, writing to its own log files.
3.  **Check**: The orchestrator periodically checks a lightweight status file, never the full logs.

## What a delegated agent can actually do

Delegation only pays off if the worker has the tools its task needs, so decide this
*before* writing the prompt. Headless agents deny all tools by default, and when one
Claude session spawns another the environment hardening forces `--permission-mode` back
to default — `--dangerously-skip-permissions` is silently ignored. The remedy that
survives that hardening is an explicit allowlist, which `delegate_task.py` sets for you:

| Invocation | Tools the worker gets | Use it for |
| --- | --- | --- |
| `--agent claude` (default) | `Read Edit Write Glob Grep` — **no Bash** | Reading, auditing, refactoring, writing files |
| `--agent claude --sandbox` | adds `Bash`, confined to a sandbox | Anything that must *execute*: tests, typecheck, builds, `git`, package managers |

Note the inversion: here `--sandbox` **grants** capability rather than removing it. The
containment and the power are tied together deliberately — an unattended agent gets a
shell only when it also gets a sandbox to run it in, so it can never run arbitrary
commands loose in the real repo.

The practical consequence: a task phrased "run the test suite and report failures" sent
*without* `--sandbox` produces a worker that can read the tests but never run them. It
will usually write a plausible-sounding summary anyway, which is the most expensive
failure mode this skill has — you get a confident answer built on nothing. If the verb in
your prompt is run/execute/build/install/commit, pass `--sandbox`.

## Tools

**IMPORTANT:** All scripts are located in `.claude/skills/orchestration-skill/scripts/`. When running from the project root, you must use the full path. The examples below show the correct paths when running from the project root directory.

### `delegate_task`
Launches a new task with a specified agent.

**Usage (from project root):**
```bash
python3 .claude/skills/orchestration-skill/scripts/delegate_task.py --agent claude --prompt "Refactor the login component"

# To resume context from a previous task:
python3 .claude/skills/orchestration-skill/scripts/delegate_task.py --agent claude --prompt "Fix the bugs" --parent_task_id 12345

# To run in a sandbox:
python3 .claude/skills/orchestration-skill/scripts/delegate_task.py --agent claude --prompt "Run tests" --sandbox

# To escalate to the high tier (see the roster below for what each tier runs):
python3 .claude/skills/orchestration-skill/scripts/delegate_task.py --agent codex --prompt "Debug race condition" --effort high

# To pin a specific model, overriding the tier's choice:
python3 .claude/skills/orchestration-skill/scripts/delegate_task.py --agent claude --prompt "Draft the migration" --model fable

# To use Antigravity (agy) — a multi-provider router with its own capacity:
python3 .claude/skills/orchestration-skill/scripts/delegate_task.py --agent antigravity --prompt "Refactor the landing page" --effort high
# NOTE: agy prints plain text (no JSON), so --parent_task_id resume is NOT
# supported for antigravity — it warns and runs a fresh conversation.

# To generate a detailed report:
python3 .claude/skills/orchestration-skill/scripts/delegate_task.py --agent claude --prompt "Audit security" --report

# To bound a task's runtime (default 1800s / 30 min). The agent is auto-killed
# if it exceeds the limit and the task is marked FAILED with a timeout error:
python3 .claude/skills/orchestration-skill/scripts/delegate_task.py --agent claude --prompt "Big refactor" --timeout 3600

# Combine flags for comprehensive analysis:
python3 .claude/skills/orchestration-skill/scripts/delegate_task.py --agent codex --effort high --report --prompt "Production audit"
```

### Which model runs

`--effort` picks a tier, and each tier is one deliberately-chosen (model, reasoning effort) pair.
The pairing is the point: model and reasoning depth are separate dials on all three CLIs, so
choosing them together once is what lets you delegate with a single flag instead of reasoning about
a grid of combinations at the moment you have least context.

| Tier | `--agent claude` | `--agent codex` | `--agent antigravity` |
| --- | --- | --- | --- |
| *(default)* | `sonnet` + medium effort | `gpt-6-astra` + low effort | `gemini-3.8-flash-high` |
| `--effort high` | `opus` + medium effort | `gpt-6-astra` + medium effort | `claude-opus-4-6-thinking` |

Each ladder escalates on the axis that backend actually rewards: claude changes the *model* and
holds effort steady, codex holds the model and raises *effort*, and agy bakes effort into the model
slug so there is nothing separate to turn.

**`--model` overrides just the model** and keeps the tier's effort — `--model fable --effort high`
runs fable at medium. It is passed through verbatim, so it must be a name that agent's CLI accepts
(`agy models` lists agy's; claude takes `haiku`/`sonnet`/`opus`/`fable` or a full name). Use it when
you know exactly what you want; use the tiers otherwise.

The roster lives in `MODEL_TIERS` at the top of `delegate_task.py`, and
`tests/test_model_roster.py` checks every entry against what the tools currently offer. Run the
tests after any model release — a stale name doesn't error, it just quietly wastes a delegation.
The resolved model is recorded in each task's status file, so you can always tell what actually ran.

**Runtime safety:** Every delegated agent is bounded by a watchdog (default 30 min, override with `--timeout`). If the agent hangs past the limit it is terminated and the task is recorded as `FAILED` with `error: "Agent killed (timeout...)"`, so a stuck worker can never burn tokens indefinitely.

**Keep the two timeouts in step.** The agent's budget (`delegate_task.py --timeout`) and
the watcher's patience (`watch_task.py --timeout` / `wait_for_tasks.py --timeout`) are
separate clocks that both default to 30 min. Raising only the first is the classic
mistake: give the agent 3600s and the watcher still gives up at 1800s, so the second half
of the run has no auto-wake at all — the task finishes into silence and you find out only
when the user next speaks. Whenever you pass `--timeout` to `delegate_task.py`, pass the
watcher a **larger** value (agent timeout + 60s of grace is a good rule, since the watcher
should outlive the watchdog kill in order to report the failure):

```bash
python3 .claude/skills/orchestration-skill/scripts/delegate_task.py --agent claude --prompt "Big refactor" --timeout 3600
python3 .claude/skills/orchestration-skill/scripts/watch_task.py --task_id <TASK_ID> --timeout 3660
```

**Returns:**
A JSON object containing the `task_id` and `pid`.

### `check_status`
Checks the status of a specific task.

**Usage (from project root):**
```bash
python3 .claude/skills/orchestration-skill/scripts/check_status.py --task_id <TASK_ID>
```

**Returns:**
A JSON object with `status` ("RUNNING", "COMPLETED", "FAILED") and `summary_file` path if complete.

### `list_active_tasks`
Lists all currently running tasks.

**Usage (from project root):**
```bash
python3 .claude/skills/orchestration-skill/scripts/list_active_tasks.py
```

### `watch_task`
Watches a delegated task in the background and outputs the summary when it completes. This enables auto-wake: the orchestrator is proactively notified without the user needing to say "agent done".

**Usage (from project root) — MUST use `run_in_background`:**
```bash
python3 .claude/skills/orchestration-skill/scripts/watch_task.py --task_id <TASK_ID>

# Custom polling interval (default: 15 seconds):
python3 .claude/skills/orchestration-skill/scripts/watch_task.py --task_id <TASK_ID> --interval 10

# Custom timeout (default: 1800 seconds / 30 min):
python3 .claude/skills/orchestration-skill/scripts/watch_task.py --task_id <TASK_ID> --timeout 3600
```

**Returns:**
Plain text with a header line and the summary content when the task completes, fails, or is cancelled.

### `wait_for_tasks`
Waits for **multiple** delegated tasks to finish — the parallel barrier for fan-out. Polls all given tasks until every one reaches a terminal state (or the batch times out), then prints one consolidated block with each task's summary. Run via `run_in_background` so the single completion print wakes the orchestrator once for the whole batch.

**Usage (from project root) — MUST use `run_in_background`:**
```bash
python3 .claude/skills/orchestration-skill/scripts/wait_for_tasks.py --ids abc123,def456,ghi789

# Custom polling interval (default: 15s) and batch timeout (default: 3600s):
python3 .claude/skills/orchestration-skill/scripts/wait_for_tasks.py --ids abc123,def456 --interval 10 --timeout 1800
```

**Returns:**
A header (`=== Batch complete ... N completed, M failed ===`) followed by each task's summary. Exit code 0 if all completed, non-zero if any failed or the batch timed out — so the orchestrator can branch on success.

### `cancel_task`
Cancels a running task by terminating the agent and everything it spawned.

**Usage (from project root):**
```bash
python3 .claude/skills/orchestration-skill/scripts/cancel_task.py --task_id <TASK_ID>
```

**Returns:**
A JSON object with `status: "CANCELLED"` and the `terminated_pids` it signalled, or an error if
the task is not running.

A cancel behaves like a timeout kill, not like a crash: the task's own wrapper survives the
cancel on purpose, so it still runs `finish_task.py`. That means you get the summary fallback and
the usual notifications, and the status file settles on `CANCELLED` rather than `FAILED` — so a
watcher already waiting on the task wakes up and reports cleanly instead of hanging.

## Directory Structure

*   `logs/orchestration/`: Stores all orchestration task logs and status files.
    *   `logs/orchestration/raw/<task_id>.log`: Full stdout/stderr of the agent.
    *   `logs/orchestration/status/<task_id>.status.json`: Structured status file (monitored by status line).
    *   `logs/orchestration/results/<task_id>.summary.md`: Concise summary written by the agent.
    *   `logs/orchestration/results/<task_id>_report.md`: Detailed report (if requested).

## Workflow Example

1.  **Orchestrator** decides to implement a feature.
2.  **Orchestrator** runs: `python3 .claude/skills/orchestration-skill/scripts/delegate_task.py --agent claude --prompt "Implement feature X"`
3.  **Orchestrator** receives `task_id: "12345"` in JSON response. Visual icon (🤖) appears in status line automatically.
4.  **Orchestrator** immediately runs (via `run_in_background`): `python3 .claude/skills/orchestration-skill/scripts/watch_task.py --task_id 12345`
5.  **Orchestrator** continues with other work or waits.
6.  When task completes, the watcher fires a task notification that **proactively wakes the orchestrator**.
7.  **Orchestrator** reads `logs/orchestration/results/12345.summary.md` and reports the result to the user.
8.  If `--report` was used, **Orchestrator** also reads `logs/orchestration/results/12345_report.md`.

## Parallel Fan-Out Example

For multi-agent work, launch several tasks and wait for the whole batch with a single barrier instead of tracking each one by hand:

1.  **Orchestrator** delegates N tasks, calling `delegate_task.py` once per task and collecting each returned `task_id` (e.g. `abc123`, `def456`, `ghi789`). They run concurrently.
2.  **Orchestrator** runs (via `run_in_background`):
    `python3 .claude/skills/orchestration-skill/scripts/wait_for_tasks.py --ids abc123,def456,ghi789`
3.  **Orchestrator** continues with other work.
4.  When the **last** task finishes, `wait_for_tasks` prints all summaries at once, which proactively wakes the orchestrator a single time for the entire batch.
5.  **Orchestrator** reviews the consolidated output and reports back. A non-zero exit means at least one task failed.

## Auto-Wake Pattern

Task completion notifications are delivered via two mechanisms:

### Primary: Background Watcher (the real auto-wake)

**Always start a background watcher after delegating** — it is the only mechanism that *proactively wakes* the orchestrator while it sits idle:

```bash
python3 .claude/skills/orchestration-skill/scripts/watch_task.py --task_id <TASK_ID>
```

Run it via `run_in_background` (use `wait_for_tasks.py` for a batch). When the task completes, the watcher fires a task-notification that re-invokes the orchestrator — no user message required.

### Complement: Channel Push (turn-boundary surfacing only)

When a Claude Code channel plugin is running on `localhost:9999`, `finish_task.py` automatically POSTs task completion events to it (port configurable via `ORCHESTRATION_CHANNEL_PORT`, default 9999).

**Caveat — do not rely on this for auto-wake:** the POST succeeds and logs the completion, but the channel does **not** inject mid-turn or while the orchestrator is idle. Delivery is deferred to the next turn boundary — it only surfaces when the user next sends a message. The channel complements the watcher (instant surfacing once a turn is active); it does **not** replace it. Start the watcher even when the channel is active.

### Reading Results After Wake-Up

When the watcher notification arrives with an `<output-file>` path, the orchestrator MUST:

1. **Read the output file** from the notification — it contains the summary with metadata (task ID, agent, duration, status)
2. **Read the report file** (only if `--report` was used): `logs/orchestration/results/<task_id>_report.md`
3. Report the results to the user

### Handling Duplicate Notifications

If the user manually says "agent done" before the watcher fires, read the summary as usual. When the watcher notification arrives later for a task already processed, briefly acknowledge it ("Already reviewed task {task_id} results.") and do not re-process.

## Rules of Engagement

To maintain a clean and predictable environment, Orchestrators must adhere to the following rules:

1.  **NO Root File Creation**: Never instruct an agent to create a report or document in the project root (e.g., `PROJECT_STATUS.md`).
2.  **Don't restate the output path**: `delegate_task.py` already appends the summary/report path and the "write it there" instruction to every prompt it sends. Repeating that in your own prompt text just competes with the injected wording — spend the prompt on the *task* instead.
3.  **Containment**: Agents should only write to files if explicitly necessary for the task (e.g., refactoring code). Documentation and reports belong in `logs/orchestration/results/`.
4.  **Auto-Wake**: Always start a background watcher after delegating to enable proactive notifications — `watch_task.py` for a single task, or `wait_for_tasks.py` for a batch (both via `run_in_background`) — with a timeout larger than the agent's.
5.  **Match tools to the verb**: If the task must execute anything, delegate with `--sandbox` (see "What a delegated agent can actually do"). A worker without Bash will still answer; it just won't have run anything.

## Reference Files

`SKILL.md` covers the whole workflow. Reach for these only when you need depth:

| File | Read it when |
| --- | --- |
| `references/delegation_patterns.md` | Choosing which agent/effort fits a task, or designing a fan-out |
| `references/workflow-management.md` | Chaining tasks, conversation continuity, resume semantics |
| `references/monitoring-patterns.md` | Debugging the status/PID machinery, or driving the CLIs directly |
| `references/claude-headless.md`, `references/codex-sdk.md` | Underlying CLI flags and output formats |

## Status Line Integration

The orchestration skill automatically integrates with Claude Code's status line:

- **Visual Icons**: Each running task shows an icon in your status line:
  - 🤖 = Claude Code task
  - 🔶 = Codex CLI task
  - 🪐 = Antigravity CLI task
- **Duration Display**: Shows elapsed time (e.g., "2m" or "45s")
- **macOS Notifications**: You'll receive a notification when tasks complete
- **Automatic Monitoring**: The `status_vis.py` script monitors `logs/orchestration/status/` for active tasks
