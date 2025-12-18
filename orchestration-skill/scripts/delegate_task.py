import argparse
import json
import os
import subprocess
import sys
import time
import uuid
import shlex

def main():
    parser = argparse.ArgumentParser(description="Delegate a task to a headless agent.")
    parser.add_argument("--agent", required=True, choices=["claude", "gemini", "codex"], help="The agent to use.")
    parser.add_argument("--prompt", required=True, help="The task description/prompt.")
    parser.add_argument("--task_id", help="Optional custom task ID.")
    parser.add_argument("--parent_task_id", help="Optional parent task ID to resume session from.")
    parser.add_argument("--sandbox", action="store_true", help="Enable sandboxing for the agent.")
    parser.add_argument("--report", action="store_true", help="Request a detailed report in logs/results/.")
    parser.add_argument("--effort", choices=["standard", "high"], default="standard", help="Set the reasoning effort level (standard=fast, high=smart).")
    
    args = parser.parse_args()
    
    # 1. Generate Task ID
    task_id = args.task_id or str(uuid.uuid4())[:8]
    
    # 2. Setup Logs Directory
    # Resolve relative to the Current Working Directory (Project Root)
    # This makes the skill portable and keeps logs in the user's project
    base_log_dir = os.path.join(os.getcwd(), "logs", "orchestration")
    raw_dir = os.path.join(base_log_dir, "raw")
    status_dir = os.path.join(base_log_dir, "status")
    results_dir = os.path.join(base_log_dir, "results")

    os.makedirs(raw_dir, exist_ok=True)
    os.makedirs(status_dir, exist_ok=True)
    os.makedirs(results_dir, exist_ok=True)
    
    log_file = os.path.join(raw_dir, f"{task_id}.log")
    status_file = os.path.join(status_dir, f"{task_id}.status.json")
    summary_file = os.path.join(results_dir, f"{task_id}.summary.md")
    report_file = os.path.join(results_dir, f"{task_id}_report.md")
    pid_file = os.path.join(status_dir, f"{task_id}.pid")

    # Initialize output files
    with open(summary_file, 'w') as f:
        f.write("")
        
    if args.report:
        with open(report_file, 'w') as f:
            f.write("")
    
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

    augmented_prompt = (
        f"{args.prompt}\n\n"
        "IMPORTANT INSTRUCTIONS FOR HEADLESS EXECUTION:\n"
        "1. Perform the requested task.\n"
        f"{write_instruction}"
        "3. The summary file should be in Markdown format.\n"
        "4. Do not ask for confirmation. Just do it.\n"
        f"{report_instruction}"
        "5. DO NOT create any other files. You are ONLY allowed to write to the summary file (and report file if specified). Do NOT create files in the project root.\n"
    )
    
    # Securely quote the prompt for shell usage
    safe_prompt = shlex.quote(augmented_prompt)
    
    # 5. Construct the Command
    agent_cmd = ""
    
    # Determine model/flags based on effort level
    gemini_model = "auto"
    claude_model = "sonnet-4.5"
    codex_model = "gpt-5.2"
    
    if args.effort == "high":
        gemini_model = "gemini-3-pro-preview"
        claude_model = "sonnet"

    if args.agent == "claude":
        agent_cmd = f'claude -p {safe_prompt} --output-format json'
        agent_cmd += f' --model {claude_model}'
        if args.sandbox:
            agent_cmd += ' --sandbox'
        if parent_session_id:
            agent_cmd += f' --resume {parent_session_id}'
            
    elif args.agent == "gemini":
        agent_cmd = f'gemini -p {safe_prompt} --output-format json --yolo --model {gemini_model}'
        if args.sandbox:
            agent_cmd += ' --sandbox'
        if parent_session_id:
            agent_cmd += f' --resume {parent_session_id}'
            
    elif args.agent == "codex":
        # Construct base command with model
        base_cmd = f'codex exec --model {codex_model}'
        
        if parent_session_id:
            agent_cmd = f'{base_cmd} resume {parent_session_id} {safe_prompt} --json'
        else:
            agent_cmd = f'{base_cmd} {safe_prompt} --json'
        
        if args.effort == "high":
            agent_cmd += ' -c model_reasoning_effort="high"'
        else:
            # Explicitly set medium/default if needed, or rely on model default
            agent_cmd += ' -c model_reasoning_effort="medium"'
            
        if args.sandbox:
            agent_cmd += ' --sandbox workspace-write'
    
    # 6. Launch the Agent via Wrapper Script
    wrapper_script = os.path.join(raw_dir, f"{task_id}.sh")
    
    # Use absolute path for finish_task.py
    skill_dir = os.path.dirname(os.path.abspath(__file__))
    finish_script = os.path.join(skill_dir, "finish_task.py")
    
    finish_cmd = (
        f"python3 {finish_script} "
        f"--task_id {task_id} "
        f"--log_file {log_file} "
        f"--status_file {status_file} "
        f"--summary_file {summary_file} "
        f"--agent {args.agent} "
        f"--pid_file {pid_file}"
    )
    
    with open(wrapper_script, 'w') as f:
        f.write("#!/bin/bash\n")
        # Write PID of the shell to pid_file immediately
        f.write(f"echo $$ > {pid_file}\n")
        f.write(f"{agent_cmd} > {log_file} 2>&1\n")
        f.write(f"{finish_cmd}\n")
        
    os.chmod(wrapper_script, 0o700) # Only owner can execute
    
    # Launch background process
    # We don't track the PID of this 'nohup' call because the wrapper script itself 
    # will write its own PID (which is the one we care about for killing/monitoring)
    full_cmd = f"nohup {wrapper_script} > /dev/null 2>&1 &"
    subprocess.Popen(full_cmd, shell=True)
    
    # 7. Write Initial Status File
    # PID is initially null, updated by wrapper script (or shortly after by check_status if needed)
    status_data = {
        "task_id": task_id,
        "status": "RUNNING",
        "pid": None, # Will be filled by wrapper script writing to pid_file, or check_status reading pid_file
        "pid_file": pid_file,
        "agent": args.agent,
        "log_file": log_file,
        "summary_file": summary_file,
        "report_file": report_file if args.report else None,
        "start_time": time.time(),
        "parent_session_id": parent_session_id
    }
    
    with open(status_file, 'w') as f:
        json.dump(status_data, f)

    print(json.dumps(status_data, indent=2))

    # Remind orchestrator about context chaining if not used
    if not args.parent_task_id:
        print("\n💡 Tip: Use --parent_task_id <id> to chain context from a related task.", file=sys.stderr)

if __name__ == "__main__":
    main()
