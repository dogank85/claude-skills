# Orchestration Skill — Hardening Plan (#1 Session Extraction, #2 Runaway Protection, #3 Parallel Barrier)

## Context

The orchestration skill (`.claude/skills/orchestration-skill/`) launches headless agents (claude/gemini/codex) in a fire-and-forget pattern and tracks them via lightweight status files. It works on the happy path, but three issues only surface under messy, real-world conditions:

1. **Session-ID extraction is fragile.** `finish_task.py` extracts `session_id` with `cat <log> | jq -r .session_id`, but the agent runs with stderr merged into the log (`> log 2>&1` in `delegate_task.py:162`). Any stderr line (a deprecation/node warning) makes `jq` fail on the whole file → no `session_id` captured → `--parent_task_id` resume silently breaks. This is correlated with exactly the noisy runs we can't control.
2. **No runaway protection.** Nothing bounds a hung agent. `watch_task.py`'s timeout only stops *watching*; the agent process keeps running and burning tokens indefinitely. Cancellation is manual.
3. **No parallel barrier.** The skill is single-task shaped. True multi-agent orchestration needs fan-out: launch N agents, wait for all N. Today that means manually tracking IDs and eyeballing `list_active_tasks`.

Intended outcome: harden the existing flow (#1, #2) and add the one missing primitive for fan-out (#3), without altering the skill's core architecture or refactoring working code.

Only the canonical copy at `.claude/skills/orchestration-skill/` is edited. A PostToolUse hook (`scripts/sync_orchestration_skill.sh`) fans changes out to `.gemini`, `.agent`, `.agents`, `.codex`, `.opencode`, and the `../claude-skills` marketplace repo — so all edits target the canonical path and the sync handles propagation.

Scope decisions (confirmed with user): #3 = `wait_for_tasks.py` only (no `delegate_batch`); #2 default kill timeout = 30 min, configurable per task.

---

## #1 — Robust session-ID extraction

**File:** `scripts/finish_task.py` (extraction block, lines ~17–34)

Replace the two `subprocess` + `jq` branches (claude/gemini via `cat | jq`, codex via `grep | jq`) with a single Python regex over the log contents — uniform across all three agents, tolerant of mixed stderr, multi-line/pretty-printed JSON, and surrounding noise:

```python
import re
session_id = None
try:
    with open(args.log_file, 'r') as f:
        log_content = f.read()
    m = re.search(r'"session_id"\s*:\s*"([^"]+)"', log_content)
    if m:
        session_id = m.group(1)
except Exception as e:
    print(f"Error extracting session ID: {e}", file=sys.stderr)
```

This removes the `jq` dependency for extraction and the per-agent branching. The existing guard `if session_id and session_id != "null"` before writing to the status file is preserved.

**Also:** `delegate_task.py` computes `extract_session_cmd` for all three agents (lines ~98, 116, 125, 140) but never uses it — pre-existing dead code. Since we're editing `delegate_task.py` for #2 anyway, remove these dead assignments in the same pass to avoid confusion (they imply an extraction path that doesn't exist).

---

## #2 — Runaway protection (auto-kill hung agents)

**Files:** `scripts/delegate_task.py` (arg + wrapper generation, lines ~9–19 and ~159–171), `scripts/finish_task.py` (exit-code interpretation, lines ~42–48)

1. Add a `--timeout` arg to `delegate_task.py` (type=int, default=1800 = 30 min).
2. Rewrite the wrapper bash script (`<task_id>.sh`) to bound the agent with a portable sleep+kill watchdog (no dependency on GNU `timeout`/`gtimeout`, which macOS lacks by default):

```bash
#!/bin/bash
echo $$ > <pid_file>
<agent_cmd> > <log_file> 2>&1 &
AGENT_PID=$!
( sleep <timeout> && kill -TERM $AGENT_PID 2>/dev/null ) &
WATCHDOG_PID=$!
wait $AGENT_PID
EXIT_CODE=$?
kill $WATCHDOG_PID 2>/dev/null   # cancel watchdog if agent finished first
<finish_cmd> --exit_code $EXIT_CODE
```

   - On a SIGTERM kill, `wait` yields exit code 143; finish_task treats 143 (and 124, GNU timeout's code) as a timeout rather than a generic failure.
   - **Process-group nuance to verify on macOS:** killing only `$AGENT_PID` may orphan child processes the agent spawned. The wrapper already runs under its own `nohup` group, and `cancel_task.py` uses `os.killpg(os.getpgid(pid), SIGTERM)`. During implementation, verify whether `kill -TERM $AGENT_PID` reaps children on macOS; if not, make the agent a group leader (e.g. `setsid` if available, else a bash subshell + `kill -- -$PID`) and kill the group. This is the one detail to confirm empirically before shipping.

3. In `finish_task.py`, interpret the exit code: when 143/124, set `data["status"] = "FAILED"` with `data["error"] = "Agent killed (timeout after <N>s)."`. The existing empty-summary fallback (tail of log) still runs, so the orchestrator gets context on what the agent was doing when killed.
4. Add `"timeout"` to the status JSON written in `delegate_task.py` so `check_status`/`watch_task` can surface it.

---

## #3 — Parallel barrier: `wait_for_tasks.py`

**New file:** `scripts/wait_for_tasks.py`

A multi-task generalization of `watch_task.py`. Reuses the same self-contained-helper pattern the existing scripts use (`read_status`, `resolve_pid`, `is_pid_alive`, crash detection) — duplicated locally to match the codebase style rather than introducing a shared module (see Cleanup note).

```
python3 .claude/skills/orchestration-skill/scripts/wait_for_tasks.py --ids a,b,c [--interval 15] [--timeout 3600]
```

Behavior:
- Parse comma-separated `--ids`; validate each status file exists.
- Poll all tasks each interval. For each `RUNNING` task, apply the same crash detection as `watch_task.py` (PID dead → mark FAILED).
- Exit when **all** tasks reach a terminal state (COMPLETED / FAILED / CANCELLED) or the global `--timeout` elapses.
- On completion, print one consolidated block: per-task header (id, agent, status, duration) followed by each task's summary (or fallback). This single print is what wakes the orchestrator once for the whole batch when run via `run_in_background`.
- Exit 0 if all COMPLETED; non-zero if any FAILED/timed out (so the orchestrator can branch).

Fan-out usage (documented, not scripted): orchestrator calls `delegate_task.py` N times, collects the returned `task_id`s, then runs `wait_for_tasks.py --ids <all>` via `run_in_background`.

---

## SKILL.md + manifest updates

**File:** `SKILL.md`
- Add a **`wait_for_tasks`** entry to the Tools section (usage + returns), mirroring the `watch_task` entry style.
- Add a **Parallel Fan-Out** workflow example: delegate ×N → collect IDs → `wait_for_tasks` in background → single wake with all summaries.
- Document the new `--timeout` flag under `delegate_task` and note that agents are auto-killed after the limit (default 30 min) and marked FAILED with a timeout error.
- Update Rules of Engagement #4 (Auto-Wake) to mention `wait_for_tasks` as the auto-wake mechanism for batches.
- Bump `version: 1.0.0` → `1.1.0`.

**File:** `plugin.json` — bump `"version"` to `1.1.0`.

(No change needed to the antigravity/`agy` story — explicitly out of scope for this plan.)

---

## Verification

Run from project root (`/Users/dogankarakaya/LocalProjects/HeroKid`). EAS/mobile rules don't apply — this is pure Python tooling.

**#1 (unit, no agent spawn):** Create a temp log file containing a stderr warning line followed by a JSON object with `"session_id":"abc123"`. Run the new extraction logic against it; confirm it returns `abc123`. Repeat with a pretty-printed multi-line JSON variant and a codex-style JSONL variant — all three must yield the ID. Then a live smoke test: delegate a trivial claude task, confirm `session_id` is present in `logs/orchestration/status/<id>.status.json`, then `delegate_task ... --parent_task_id <id>` and confirm resume works.

**#2:** `delegate_task.py --agent claude --prompt "sleep then respond" --timeout 5` (or a prompt that will run >5s). Confirm the agent process is gone within ~5–7s, the status file shows `FAILED` with a timeout error, and a fallback summary (log tail) was written. Separately confirm a fast task that finishes before the timeout is unaffected and the watchdog subshell is cleaned up (no lingering `sleep` process).

**#3:** Delegate 2–3 trivial tasks (e.g. "echo done"), collect their IDs, run `wait_for_tasks.py --ids <a,b,c>` via `run_in_background`. Confirm: it blocks until all reach terminal state, prints one consolidated block with all summaries, wakes the orchestrator once, and returns non-zero if one task is made to fail.

**Sync check:** After edits, confirm the PostToolUse hook propagated changes — spot-check that `.gemini/skills/orchestration-skill/scripts/wait_for_tasks.py` and the marketplace copy exist and match the canonical file.

---

## Out of scope (flagged, not changed)
- **Helper duplication:** `resolve_pid`/`read_status`/`is_pid_alive` are copied across 5 scripts after this change. Consolidating into a shared `_common.py` is a worthwhile separate cleanup but would touch 4 working files — deferred to keep this change isolated.
- **Antigravity (`agy`) integration:** deferred per user. When revisited, note `agy` v1.0.0 has no `--output-format json` and no `--model` flag, but does have `--conversation <ID>` (resume) and a built-in `--print-timeout` — a materially different contract from gemini.
- **Hardcoded model IDs** (`haiku`/`sonnet`/`gemini-3-flash-preview`) in `delegate_task.py` — original critique item #4, not in this batch.
