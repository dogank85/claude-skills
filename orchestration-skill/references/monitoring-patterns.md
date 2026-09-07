# Monitoring and Resumption Patterns

> **Note:** These are low-level CLI reference patterns. In practice, always use the orchestration skill's scripts (`delegate_task.py`, `check_status.py`, `watch_task.py`, etc.) rather than running CLI commands directly. The scripts handle PID tracking, crash detection, status updates, and notifications automatically.

Patterns for monitoring background delegations, error handling, and resuming conversations.

## Background Task Monitoring

### Using BashOutput Tool

When you delegate to an agent in background mode (using `&`), monitor progress with the BashOutput tool:

```bash
# Start delegation in background
claude -p "Run /workflows/example-workflow" \
  --output-format json \
  --permission-mode acceptEdits &

# System will return process ID (e.g., 12345)
# Monitor progress
BashOutput(bash_id="12345")
```

### Polling Strategy

For long-running workflows (dev-story, epic-tech-context):

```bash
# Poll every 30 seconds
while true; do
  BashOutput(bash_id="12345")
  sleep 30
done
```

### Multiple Background Tasks

Track multiple delegations simultaneously:

```bash
# Launch 3 tasks
claude -p "Task 1" &
PID1=$!

agy -p "Task 2" &
PID2=$!

codex exec "Task 3" &
PID3=$!

# Monitor all
BashOutput(bash_id="$PID1")
BashOutput(bash_id="$PID2")
BashOutput(bash_id="$PID3")
```

---

## Session Resumption

### Claude Code Resume

Resume a previous Claude Code session by session ID:

```bash
# Initial delegation
result=$(claude -p "Run workflow Part 1" --output-format json)
session_id=$(echo "$result" | jq -r '.session_id')

# Resume later
claude --resume "$session_id" "Continue with Part 2"

# Resume in non-interactive mode
claude --resume "$session_id" "Finish the implementation" --no-interactive
```

### Codex CLI Resume

Resume Codex exec sessions:

```bash
# Initial delegation
codex exec "Review the change for race conditions"

# Resume last session
codex exec resume --last "Fix the race conditions you found"

# Resume specific session
codex exec resume <SESSION_ID> "Continue implementation"
```

---

## Error Handling Patterns

### Detecting Failures

**Claude Code (JSON output):**
```bash
result=$(claude -p "Run workflow" --output-format json)
is_error=$(echo "$result" | jq -r '.is_error')

if [ "$is_error" = "true" ]; then
  echo "Error occurred:"
  echo "$result" | jq -r '.result'
  exit 1
fi
```

**Codex CLI (exit code):**
```bash
if ! codex exec "Run workflow" 2>error.log; then
  echo "Error occurred:" >&2
  cat error.log >&2
  exit 1
fi
```

### Retry Strategy

Retry failed delegations with exponential backoff:

```bash
retry_count=0
max_retries=3
delay=5

while [ $retry_count -lt $max_retries ]; do
  if claude -p "Run workflow" --output-format json; then
    echo "Success!"
    break
  else
    retry_count=$((retry_count + 1))
    echo "Attempt $retry_count failed. Retrying in $delay seconds..."
    sleep $delay
    delay=$((delay * 2))  # Exponential backoff
  fi
done

if [ $retry_count -eq $max_retries ]; then
  echo "Failed after $max_retries attempts"
  exit 1
fi
```

### Graceful Degradation

Fall back to alternative agent on failure:

```bash
# Try Codex first (fast execution)
if codex exec --full-auto "Run workflow" 2>/dev/null; then
  echo "Completed with Codex"
else
  echo "Codex failed, falling back to Claude Code..."

  # Fall back to Claude Code (more robust)
  if claude -p "Run workflow" --output-format json --permission-mode acceptEdits; then
    echo "Completed with Claude Code"
  else
    echo "Both agents failed"
    exit 1
  fi
fi
```

---

## Output Collection Patterns

### Aggregating Results

Collect and aggregate results from parallel delegations:

```bash
# Launch parallel tasks
claude -p "Task 1" --output-format json > result1.json &
PID1=$!

claude -p "Task 2" --output-format json > result2.json &
PID2=$!

codex exec "Task 3" --json > result3.json &
PID3=$!

# Wait for all to complete
wait $PID1 $PID2 $PID3

# Aggregate results
echo "=== Task 1 Result ==="
cat result1.json | jq -r '.result'

echo "=== Task 2 Result ==="
cat result2.json | jq -r '.result'

echo "=== Task 3 Result ==="
cat result3.json
```

### Streaming vs Final Output

**Claude Code:**
- Text output: Human-readable, final message only
- JSON output: Structured with metadata (session_id, cost, etc.)
- Stream JSON output: Real-time events (use `--output-format stream-json`)

**Codex CLI:**
- Default: Final message to stdout, progress to stderr
- JSON: JSONL stream with all events (`--json`)
- Output file: Save final message (`-o output.md`)

---

## Timeout Management

### Setting Timeouts

Prevent infinite hangs with timeout:

```bash
# Timeout after 5 minutes
timeout 300 claude -p "Run workflow" || echo "Timed out after 5 minutes"

# Timeout with cleanup
timeout 600 codex exec "Long-running task" || {
  echo "Timed out after 10 minutes"
  # Cleanup or retry logic here
  exit 1
}
```

### Progress Indication

Show progress for long-running delegations:

```bash
# Start delegation in background
claude -p "Run workflow" --output-format json &
PID=$!

# Show spinner while waiting
while kill -0 $PID 2>/dev/null; do
  echo -n "."
  sleep 2
done

echo " Done!"
```

---

## Context Preservation

### Passing Context Between Delegations

**Anti-pattern (bloats context):**
```bash
# DON'T: Read entire output into context
result=$(claude -p "Generate plan")
claude -p "Implement this plan: $result"  # Bloats context!
```

**Good pattern (use files):**
```bash
# DO: Save to file and reference
claude -p "Generate plan" --output-format json | jq -r '.result' > plan.md

# Next agent reads file directly (doesn't bloat orchestrator context)
codex exec --full-auto "Implement plan from plan.md"
```

### Multi-turn Conversations

Preserve context across turns by resuming sessions:

```bash
# Turn 1: Initial analysis
result=$(claude -p "Analyze codebase for Feature X" --output-format json)
session_id=$(echo "$result" | jq -r '.session_id')

# Turn 2: Generate implementation plan (same context)
claude --resume "$session_id" "Generate implementation plan based on analysis"

# Turn 3: Execute implementation (same context)
claude --resume "$session_id" "Execute the implementation plan"
```

---

## Performance Optimization

### Parallel Execution Limits

Don't overload with too many parallel tasks:

```bash
# GOOD: 3-5 parallel tasks
for i in {1..5}; do
  claude -p "Task $i" &
done
wait

# BAD: 20+ parallel tasks (overload)
for i in {1..20}; do
  claude -p "Task $i" &  # Too many!
done
wait
```

### Rate Limiting

Add delays between delegations to respect rate limits:

```bash
for item in 1 2 3 4 5; do
  claude -p "Run workflow for Item $item" --output-format json
  sleep 2  # Delay between requests
done
```

### Caching Strategy

Reuse session context for related tasks:

```bash
# Initial session with full context
result=$(claude -p "Load context and create item 1.1" --output-format json)
session_id=$(echo "$result" | jq -r '.session_id')

# Subsequent tasks reuse cached context (faster)
claude --resume "$session_id" "Create item 1.2"  # Resumes session, context cached
claude --resume "$session_id" "Create item 1.3"  # Even faster with cached context
```

---

## Common Issues and Solutions

### Issue: "Session not found" error

**Cause:** Session expired or invalid session ID

**Solution:** Start new session or use `--continue` instead of `--resume`

```bash
# Instead of:
claude --resume "invalid-session-id" "Continue"

# Do:
claude --continue "Continue from last session"
```

### Issue: Background task hangs

**Cause:** Waiting for user input or approval

**Solution:** Use non-interactive flags

```bash
# Instead of:
claude -p "Run workflow" &  # May hang on approval prompts

# Do:
claude -p "Run workflow" --permission-mode acceptEdits &  # Auto-approves
codex exec --full-auto "Run workflow" &  # Auto-approves
```

### Issue: Output not captured

**Cause:** stdout/stderr mixed or redirected incorrectly

**Solution:** Use explicit output formats

```bash
# Instead of:
result=$(claude -p "Run workflow")  # May include progress output

# Do:
result=$(claude -p "Run workflow" --output-format json)  # Clean JSON only
```

### Issue: Context bloat from delegation

**Cause:** Reading large outputs into orchestrator context

**Solution:** Use files and references

```bash
# Instead of:
large_result=$(claude -p "Generate plan")  # Bloats context
claude -p "Implement: $large_result"

# Do:
claude -p "Generate plan" --output-format json | jq -r '.result' > plan.md
codex exec "Implement plan from plan.md"  # File reference, no bloat
```
