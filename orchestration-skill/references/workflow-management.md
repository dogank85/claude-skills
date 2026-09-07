# Workflow Management

Patterns for managing multi-agent workflows, conversation continuity, and task completion.

## Conversation Continuity

Each agent (Claude and Codex) maintains its own conversation thread. When delegating to an agent:
- If this is the FIRST delegation to that agent → Start a NEW conversation
- If already delegated to that agent → RESUME the existing conversation
- Only start a NEW conversation when the user EXPLICITLY says "start a new conversation"

## High Reasoning Mode

When the user requests "high reasoning" for a delegation:
- Apply high reasoning ONLY to that specific delegation
- Do NOT apply high reasoning to subsequent delegations
- High reasoning must be explicitly requested each time
- The orchestration-skill knows how to handle high reasoning requests

## Task Completion Handling

### Auto-Wake (Default)

After every delegation, the orchestrator starts a background watcher (`watch_task.py` via `run_in_background`). When the task completes:

1. The watcher fires a `<task-notification>` with an `<output-file>` path → **proactively wakes the orchestrator**
2. The orchestrator reads the output file — it contains the summary with metadata (task ID, agent, duration, status)
3. If `--report` was used, the orchestrator also reads: `logs/orchestration/results/<task_id>_report.md`
4. The orchestrator reports the results to the user

This works even when the user is on their phone via Remote Control — the response appears in the conversation automatically.

### Manual "Agent Done" (Fallback)

When the user says an agent is "done" (e.g., "Codex done" or "Claude finished"):
- **Do NOT check status** - The user already knows it's complete
- **Check the summary** by default
- **Only request a full report** when the user explicitly asks

### Duplicate Notification Handling

If the user says "done" before the watcher fires, process the summary as usual. When the watcher notification arrives later for a task already reviewed, briefly acknowledge it and do not re-process.

**Default behavior**: `summary` is sufficient for most cases. Only escalate to `report` when necessary.

## Examples

### Conversation Continuity

```
User: Delegate X to Codex
You: [Start NEW Codex conversation]

User: Delegate Y to Codex
You: [RESUME existing Codex conversation]

User: Start a new conversation and delegate Z to Codex
You: [Start FRESH NEW Codex conversation]
```

### High Reasoning Mode

```
User: Delegate with high reasoning to Codex
You: [Use high reasoning for this delegation only]

User: Delegate another task to Codex
You: [Use normal reasoning, resume Codex conversation]
```

### Task Completion

```
User: Codex done
You: [Check SUMMARY only, no status check]

User: Codex finished, get the report
You: [Get the full REPORT as requested]
```
