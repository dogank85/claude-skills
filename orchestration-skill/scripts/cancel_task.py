import argparse
import json
import os
import signal
import subprocess
import sys


def resolve_pid(data):
    pid = data.get("pid")
    if pid is not None:
        return pid
    pid_file = data.get("pid_file")
    if pid_file and os.path.exists(pid_file):
        try:
            with open(pid_file, 'r') as f:
                return int(f.read().strip())
        except (ValueError, IOError):
            pass
    return None


def is_pid_alive(pid):
    if not pid:
        return False
    try:
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        return True  # Process exists but we can't signal it


def collect_descendants(pid):
    """Every descendant PID of `pid`, deepest-first.

    Mirrors the recursive kill_tree() the delegation wrapper already uses. Walking
    the tree explicitly is what keeps this safe: the wrapper is launched with a
    plain `nohup ... &` (no setsid), so it inherits the *orchestrator's* process
    group — signalling that group would kill the session that started the task.
    """
    try:
        result = subprocess.run(
            ["pgrep", "-P", str(pid)],
            capture_output=True, text=True, timeout=5,
        )
    except (OSError, subprocess.SubprocessError):
        return []

    descendants = []
    for token in result.stdout.split():
        if not token.isdigit():
            continue
        child = int(token)
        descendants.extend(collect_descendants(child))
        descendants.append(child)
    return descendants


def terminate_tree(pid):
    """SIGTERM every descendant of `pid`, deepest-first. `pid` itself is spared.

    Sparing the wrapper is deliberate: its `wait` then returns 143 and it goes on
    to run finish_task.py, so a cancelled task gets the same summary fallback and
    notifications that a watchdog timeout does.
    """
    killed = []
    for target in collect_descendants(pid):
        try:
            os.kill(target, signal.SIGTERM)
            killed.append(target)
        except (ProcessLookupError, PermissionError):
            pass
    return killed


def write_status(status_file, data):
    try:
        with open(status_file, 'w') as f:
            json.dump(data, f)
    except IOError as e:
        print(json.dumps({"error": f"Failed to write status file: {str(e)}"}))
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Cancel a running task.")
    parser.add_argument("--task_id", required=True, help="The ID of the task to cancel.")
    args = parser.parse_args()

    status_file = os.path.join("logs", "orchestration", "status", f"{args.task_id}.status.json")

    if not os.path.exists(status_file):
        print(json.dumps({"error": f"Status file not found: {status_file}"}))
        sys.exit(1)

    try:
        with open(status_file, 'r') as f:
            data = json.load(f)
    except Exception as e:
        print(json.dumps({"error": f"Failed to read status file: {str(e)}"}))
        sys.exit(1)

    if data.get("status") != "RUNNING":
        print(json.dumps({"error": f"Task {args.task_id} is not running (status: {data.get('status')})."}))
        sys.exit(0)

    pid = resolve_pid(data)
    if not pid:
        print(json.dumps({"error": "No PID found in status file."}))
        sys.exit(1)

    # Record CANCELLED *before* killing anything. The kill makes the wrapper run
    # finish_task.py, which reads this file and preserves an existing CANCELLED
    # rather than relabelling the task FAILED on the 143 exit code.
    data["status"] = "CANCELLED"
    write_status(status_file, data)

    if not is_pid_alive(pid):
        print(json.dumps({
            "status": "CANCELLED",
            "task_id": args.task_id,
            "warning": "Process was not running, but status updated.",
        }))
        return

    killed = terminate_tree(pid)
    print(json.dumps({
        "status": "CANCELLED",
        "task_id": args.task_id,
        "terminated_pids": killed,
    }))


if __name__ == "__main__":
    main()
