import argparse
import json
import os
import subprocess
import sys
import time
import uuid

def build_agent_command(agent, effort, sandbox, prompt_file, parent_session_id, timeout):
    """Return the shell command string that runs the chosen agent.

    Pure function (no side effects) so the per-agent invocation can be
    unit-tested without launching subprocesses. Session ID extraction for
    resume is handled separately in finish_task.py (regex over the JSON log).
    """
    # Determine model/flags based on effort level.
    gemini_model = "gemini-3-flash-preview"
    claude_model = "haiku"
    # agy (antigravity) is a multi-provider model router that selects models by
    # their exact display name (spaces and parens included). Its high tier is a
    # Claude model drawing on Antigravity's own capacity — independent of the
    # Gemini OAuth quota the `gemini` backend consumes.
    antigravity_model = "Gemini 3.5 Flash (High)"

    if effort == "high":
        gemini_model = "gemini-3.1-pro-preview"
        claude_model = "sonnet"
        antigravity_model = "Claude Opus 4.6 (Thinking)"

    if agent == "claude":
        # NOTE: do NOT use `--bare` here — it skips macOS keychain reads, so a
        # delegated Claude can't load the user's login and fails with
        # "Not logged in". Auth must work for delegation to function.
        cmd = f"claude -p \"$(cat '{prompt_file}')\" --output-format json"
        cmd += f' --model {claude_model}'
        # Headless claude denies all tools by default, and when spawned from
        # another Claude session (always true for delegation) the
        # CLAUDE_CODE_SUBPROCESS_ENV_SCRUB hardening forces --permission-mode
        # back to default — so acceptEdits / --dangerously-skip-permissions are
        # silently ignored. The sanctioned remedy is an explicit --allowedTools
        # allowlist, which survives the hardening. Tie capability to containment:
        # file + search tools by default (enough to write summaries and refactor),
        # adding Bash only under --sandbox so an unattended agent can't run
        # arbitrary shell in the user's real repo.
        if sandbox:
            cmd += ' --sandbox --allowedTools "Read Edit Write Glob Grep Bash"'
        else:
            cmd += ' --allowedTools "Read Edit Write Glob Grep"'
        if parent_session_id:
            cmd += f' --resume {parent_session_id}'
        return cmd

    if agent == "gemini":
        cmd = f"gemini -p \"$(cat '{prompt_file}')\" --output-format json --yolo --model {gemini_model}"
        if sandbox:
            cmd += ' --sandbox'
        if parent_session_id:
            cmd += f' --resume {parent_session_id}'
        return cmd

    if agent == "codex":
        if parent_session_id:
            cmd = f"codex exec resume {parent_session_id} \"$(cat '{prompt_file}')\" --json"
        else:
            cmd = f"codex exec \"$(cat '{prompt_file}')\" --json"
        if effort == "high":
            cmd += ' -c model_reasoning_effort="high"'
        if sandbox:
            cmd += ' --sandbox workspace-write'
        return cmd

    if agent == "antigravity":
        # agy runs non-interactively with -p and prints PLAIN TEXT (it has no
        # --output-format json), so there is no session_id to capture — resume
        # is unsupported and the caller drops parent_session_id before this.
        # --print-timeout raises agy's own 5-minute default wait to match the
        # orchestration watchdog, so long tasks aren't cut short by agy itself.
        cmd = f"agy -p \"$(cat '{prompt_file}')\" --model \"{antigravity_model}\""
        cmd += f' --add-dir "{os.getcwd()}"'
        cmd += ' --dangerously-skip-permissions'
        cmd += f' --print-timeout {timeout}s'
        if sandbox:
            cmd += ' --sandbox'
        return cmd

    raise ValueError(f"Unknown agent: {agent}")


def main():
    parser = argparse.ArgumentParser(description="Delegate a task to a headless agent.")
    parser.add_argument("--agent", required=True, choices=["claude", "gemini", "codex", "antigravity"], help="The agent to use.")
    parser.add_argument("--prompt", required=True, help="The task description/prompt.")
    parser.add_argument("--task_id", help="Optional custom task ID.")
    parser.add_argument("--parent_task_id", help="Optional parent task ID to resume session from.")
    parser.add_argument("--sandbox", action="store_true", help="Enable sandboxing for the agent.")
    parser.add_argument("--report", action="store_true", help="Request a detailed report in logs/results/.")
    parser.add_argument("--effort", choices=["standard", "high"], default="standard", help="Set the reasoning effort level (standard=fast, high=smart).")
    parser.add_argument("--timeout", type=int, default=1800, help="Max agent runtime in seconds before it is auto-killed (default: 1800 = 30 min).")

    args = parser.parse_args()
    
    # 1. Generate Task ID
    task_id = args.task_id or str(uuid.uuid4())[:8]
    
    # 2. Setup Logs Directory
    base_log_dir = os.path.abspath("logs")
    orchestration_dir = os.path.join(base_log_dir, "orchestration")
    raw_dir = os.path.join(orchestration_dir, "raw")
    status_dir = os.path.join(orchestration_dir, "status")
    results_dir = os.path.join(orchestration_dir, "results")

    os.makedirs(raw_dir, exist_ok=True)
    os.makedirs(status_dir, exist_ok=True)
    os.makedirs(results_dir, exist_ok=True)
    
    log_file = os.path.join(raw_dir, f"{task_id}.log")
    pid_file = os.path.join(raw_dir, f"{task_id}.pid")
    status_file = os.path.join(status_dir, f"{task_id}.status.json")
    summary_file = os.path.join(results_dir, f"{task_id}.summary.md")
    report_file = os.path.join(results_dir, f"{task_id}_report.md")

    # Pre-create summary and report files to avoid permission issues
    # And set permissions to be writable by everyone (0o666) to avoid issues with different users/containers
    with open(summary_file, 'w') as f:
        f.write("")
    os.chmod(summary_file, 0o666)
    
    if args.report:
        with open(report_file, 'w') as f:
            f.write("")
        os.chmod(report_file, 0o666)
    
    # 3. Resolve Parent Session ID
    parent_session_id = None
    if args.parent_task_id:
        parent_status_file = os.path.join(status_dir, f"{args.parent_task_id}.status.json")
        if os.path.exists(parent_status_file):
            try:
                with open(parent_status_file, 'r') as f:
                    data = json.load(f)
                    parent_session_id = data.get("session_id")
            except:
                print(f"WARNING: Could not read parent status file: {parent_status_file}")
        else:
            print(f"WARNING: Parent status file not found: {parent_status_file}")

    # Antigravity (agy) has no JSON output, so no session_id is ever captured
    # and conversation resume is impossible. Warn and run a fresh conversation
    # rather than silently pretending the parent context carried over.
    if args.agent == "antigravity" and args.parent_task_id:
        print("WARNING: --parent_task_id is not supported for --agent antigravity "
              "(agy emits no session_id); running a fresh conversation.")
        parent_session_id = None

    # 4. Construct the Prompt
    report_instruction = ""
    if args.report:
        report_instruction = f"5. You MUST also write a detailed report of your findings/actions to this EXISTING file: {report_file}\n"

    # Agent-specific instructions for writing files
    write_instruction = f"2. When finished, you MUST write a concise summary of your work to this EXISTING file: {summary_file}\n"
    if args.agent == "claude":
        write_instruction += "   IMPORTANT: Use the `Edit` tool (or `bash` with `echo`) to write to it. The `Write` tool might fail if it tries to read first.\n"
    elif args.agent == "gemini":
        write_instruction += "   IMPORTANT: Use your `write_file` tool to write the summary to {summary_file}. If that is not available, use `run_shell_command` with `echo`.\n"
    elif args.agent == "codex":
        write_instruction += "   IMPORTANT: Use your file editing capabilities to update this file.\n"
    elif args.agent == "antigravity":
        write_instruction += "   IMPORTANT: Use your file-editing tools (or a shell `echo`) to write the summary to this file.\n"

    augmented_prompt = (
        f"{args.prompt}\n\n"
        "IMPORTANT INSTRUCTIONS FOR HEADLESS EXECUTION:\n"
        "1. Perform the requested task.\n"
        f"{write_instruction}"
        "3. The summary file should be in Markdown format.\n"
        "4. Do not ask for confirmation. Just do it.\n"
        f"{report_instruction}"
        "5. Besides any files the task explicitly asks you to create, do not create unrelated files. You MUST still write the summary file (and report file if specified) so the run can be tracked.\n"
    )
    
    # Write prompt to file to avoid shell injection issues
    prompt_file = os.path.join(raw_dir, f"{task_id}.prompt.txt")
    with open(prompt_file, 'w') as f:
        f.write(augmented_prompt)
    
    # 5. Construct the Command
    # Session ID extraction is handled in finish_task.py (regex over the log).
    agent_cmd = build_agent_command(
        agent=args.agent,
        effort=args.effort,
        sandbox=args.sandbox,
        prompt_file=prompt_file,
        parent_session_id=parent_session_id,
        timeout=args.timeout,
    )

    # 6. Launch the Agent
    # To avoid complex shell escaping issues with nohup and sh -c, we write a wrapper script.
    wrapper_script = os.path.join(raw_dir, f"{task_id}.sh")
    
    # Use absolute path for finish_task.py to ensure it runs correctly
    skill_dir = os.path.dirname(os.path.abspath(__file__))
    finish_script = os.path.join(skill_dir, "finish_task.py")
    
    finish_cmd = (
        f"python3 {finish_script} "
        f"--task_id {task_id} "
        f"--log_file {log_file} "
        f"--status_file {status_file} "
        f"--summary_file {summary_file} "
        f"--agent {args.agent} "
        f"--timeout {args.timeout}"
    )

    # The agent runs in the background so a watchdog can bound its runtime. macOS
    # has no `setsid`/`timeout`, so we recursively SIGTERM the agent's process
    # subtree (grandchildren first) via pgrep — killing only the agent, not the
    # wrapper, so finish_task still runs to record status and notify. On a
    # watchdog kill, `wait` returns 143 (128+SIGTERM), which finish_task reads
    # as a timeout.
    with open(wrapper_script, 'w') as f:
        f.write("#!/bin/bash\n")
        f.write(f"echo $$ > {pid_file}\n")
        f.write("kill_tree() {\n")
        f.write("  local pid=$1\n")
        f.write('  for child in $(pgrep -P "$pid" 2>/dev/null); do kill_tree "$child"; done\n')
        f.write('  kill -TERM "$pid" 2>/dev/null\n')
        f.write("}\n")
        f.write(f"{agent_cmd} > {log_file} 2>&1 &\n")
        f.write("AGENT_PID=$!\n")
        f.write(f"( sleep {args.timeout} && kill_tree $AGENT_PID ) &\n")
        f.write("WATCHDOG_PID=$!\n")
        f.write("wait $AGENT_PID\n")
        f.write("EXIT_CODE=$?\n")
        f.write("kill $WATCHDOG_PID 2>/dev/null\n")
        f.write("pkill -P $WATCHDOG_PID 2>/dev/null\n")
        f.write(f"{finish_cmd} --exit_code $EXIT_CODE\n")

    os.chmod(wrapper_script, 0o755)
    
    # Launch the wrapper script in background
    full_cmd = f"nohup {wrapper_script} > /dev/null 2>&1 &"
    
    process = subprocess.Popen(full_cmd, shell=True)
    
    # 7. Write Status File
    status_data = {
        "task_id": task_id,
        "status": "RUNNING",
        "pid": None,
        "pid_file": pid_file,
        "agent": args.agent,
        "log_file": log_file,
        "summary_file": summary_file,
        "report_file": report_file if args.report else None,
        "start_time": time.time(),
        "timeout": args.timeout,
        "parent_session_id": parent_session_id
    }
    
    with open(status_file, 'w') as f:
        json.dump(status_data, f)
    
    print(json.dumps(status_data, indent=2))

if __name__ == "__main__":
    main()
