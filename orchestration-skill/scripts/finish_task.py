import argparse
import json
import os
import re
import subprocess
import sys

def notification_fields(agent, task_id, exit_code, summary_content):
    """Build every string the three notification surfaces need, in one place.

    These used to be assigned inside the macOS-notification try block, while the
    ntfy and channel pushes below read them — so a single osascript failure (a
    locked screen, a headless run) took out the two notifications that actually
    reach the user. Computing them up front, with no I/O, keeps a failure in one
    surface from silencing the others.
    """
    # Agent icons and sounds matching status_vis.py
    agent_config = {
        "claude": {"icon": "🤖", "sound": "Tink"},
        "codex": {"icon": "🔶", "sound": "Glass"},
        "antigravity": {"icon": "🪐", "sound": "Submarine"}
    }
    config = agent_config.get(agent, {"icon": "🔶", "sound": "Pop"})
    agent_display = agent.capitalize()

    status_word = "Failed" if exit_code != 0 else "Complete"
    project_name = os.environ.get("ORCHESTRATION_PROJECT_NAME", os.path.basename(os.getcwd()))
    title = f"{project_name}: {config['icon']} {agent_display} Task {task_id} {status_word}"

    # Extract first line or headline for preview
    preview = summary_content.strip().split('\n')[0] if summary_content else "Task finished successfully."
    if len(preview) > 100:
        preview = preview[:97] + "..."

    return config["icon"], config["sound"], agent_display, title, preview


def main():
    parser = argparse.ArgumentParser(description="Finalize a delegated task.")
    parser.add_argument("--task_id", required=True, help="The ID of the task.")
    parser.add_argument("--log_file", required=True, help="Path to the log file.")
    parser.add_argument("--status_file", required=True, help="Path to the status file.")
    parser.add_argument("--summary_file", required=True, help="Path to the summary file.")
    parser.add_argument("--agent", required=True, help="The agent used.")
    parser.add_argument("--exit_code", type=int, default=0, help="Exit code from the agent command.")
    parser.add_argument("--timeout", type=int, default=None, help="Configured timeout (seconds), used to label timeout kills.")
    args = parser.parse_args()

    # Exit codes that mean the watchdog (or GNU timeout) killed a hung agent:
    # 143 = 128 + SIGTERM (our kill_tree), 124 = GNU `timeout` convention.
    timed_out = args.exit_code in (143, 124)

    # 1. Extract Session ID
    # The agent runs with stderr merged into the log (`> log 2>&1`), so the log
    # may contain warnings before/around the JSON. A regex scan is robust to that
    # noise as well as multi-line/pretty-printed JSON and codex's JSONL stream —
    # and works uniformly for all three agents without a jq dependency.
    session_id = None
    try:
        with open(args.log_file, 'r') as f:
            log_content = f.read()
        m = re.search(r'"session_id"\s*:\s*"([^"]+)"', log_content)
        if m:
            session_id = m.group(1)
    except Exception as e:
        print(f"Error extracting session ID: {e}", file=sys.stderr)

    # 2. Update Status File
    try:
        if os.path.exists(args.status_file):
            with open(args.status_file, 'r') as f:
                data = json.load(f)
            
            # cancel_task.py writes CANCELLED before killing the agent, which is
            # what makes this script run at all on a cancel. Honour that: the 143
            # exit code below is the *mechanism* of the cancel, not a failure.
            if data.get("status") == "CANCELLED":
                pass
            elif timed_out:
                data["status"] = "FAILED"
                limit = f" after {args.timeout}s" if args.timeout else ""
                data["error"] = f"Agent killed (timeout{limit})."
            elif args.exit_code != 0:
                data["status"] = "FAILED"
                data["error"] = f"Agent exited with code {args.exit_code}"
            else:
                data["status"] = "COMPLETED"
            if session_id and session_id != "null":
                data["session_id"] = session_id
            
            with open(args.status_file, 'w') as f:
                json.dump(data, f)
        else:
            print(f"Status file not found: {args.status_file}", file=sys.stderr)
    except Exception as e:
        print(f"Error updating status file: {e}", file=sys.stderr)

    # 3. Summary Fallback Logic
    summary_content = ""
    try:
        if os.path.exists(args.summary_file):
            if os.path.getsize(args.summary_file) == 0:
                # Summary is empty, perform fallback
                with open(args.summary_file, 'w') as f:
                    f.write("WARNING: Agent failed to write summary. Extracted from log:\n\n")
                    f.write("```json\n")
                
                # Append tail of log file
                try:
                    with open(args.log_file, 'r') as lf:
                        lines = lf.readlines()
                        tail_lines = lines[-20:] if len(lines) > 20 else lines
                    with open(args.summary_file, 'a') as sf:
                        sf.writelines(tail_lines)
                except IOError:
                    pass
                
                with open(args.summary_file, 'a') as f:
                    f.write("\n```\n")
            
            # Read summary for notification
            with open(args.summary_file, 'r') as f:
                summary_content = f.read()
    except Exception as e:
        print(f"Error in summary fallback: {e}", file=sys.stderr)

    icon, sound, agent_display, title, preview = notification_fields(
        args.agent, args.task_id, args.exit_code, summary_content
    )

    # 4. Trigger macOS Notification
    try:
        # Escape for AppleScript
        escaped_preview = preview.replace('\\', '\\\\').replace('"', '\\"')
        cmd = f'osascript -e \'display notification "{escaped_preview}" with title "{title}" sound name "{sound}"\''
        subprocess.run(cmd, shell=True)
    except Exception as e:
        print(f"Error sending notification: {e}", file=sys.stderr)

    # 5. Push Notification via ntfy.sh (iPhone) — requires ORCHESTRATION_NTFY_TOPIC env var
    ntfy_topic = os.environ.get("ORCHESTRATION_NTFY_TOPIC")
    if ntfy_topic:
        try:
            ntfy_title = f"{icon} {agent_display} Task {args.task_id}"
            ntfy_body = preview if summary_content else "Task finished successfully."
            subprocess.run([
                "curl", "-s",
                "-H", f"Title: {ntfy_title}",
                "-H", "Priority: default",
                "-H", "Tags: white_check_mark",
                "-d", ntfy_body,
                f"https://ntfy.sh/{ntfy_topic}"
            ], capture_output=True, timeout=10)
        except Exception as e:
            print(f"Error sending push notification: {e}", file=sys.stderr)

    # 6. Push to Claude Code channel (localhost:9999)
    try:
        status_word = "SUCCESS" if args.exit_code == 0 else "FAILED"
        channel_payload = json.dumps({
            "type": "task-complete",
            "source": "orchestration",
            "content": f"Agent '{args.agent}' finished task '{args.task_id}' — {status_word}.\n{preview}",
            "meta": {
                "task_id": args.task_id,
                "agent": args.agent,
                "exit_code": str(args.exit_code),
                "summary_file": args.summary_file,
                "report_file": args.summary_file.replace('.summary.md', '_report.md')
            }
        })
        subprocess.run(
            ["curl", "-s", "-X", "POST",
             "-H", "Content-Type: application/json",
             "-d", channel_payload,
             f"http://127.0.0.1:{os.environ.get('ORCHESTRATION_CHANNEL_PORT', '9999')}/push"],
            timeout=3, capture_output=True
        )
    except Exception:
        pass  # Channel may not be running; silent fallback

if __name__ == "__main__":
    main()
