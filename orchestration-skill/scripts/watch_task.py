import argparse
import json
import os
import sys
import time


def format_duration(seconds):
    minutes = int(seconds) // 60
    secs = int(seconds) % 60
    if minutes > 0:
        return f"{minutes}m {secs}s"
    return f"{secs}s"


def read_status(status_file):
    try:
        with open(status_file, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError, IOError):
        return None


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


def main():
    parser = argparse.ArgumentParser(description="Watch a delegated task and output summary on completion.")
    parser.add_argument("--task_id", required=True, help="The task ID to watch.")
    parser.add_argument("--interval", type=int, default=15, help="Polling interval in seconds (default: 15).")
    parser.add_argument("--timeout", type=int, default=1800, help="Max wait time in seconds (default: 1800).")
    args = parser.parse_args()

    base_log_dir = os.path.abspath("logs")
    status_file = os.path.join(base_log_dir, "orchestration", "status", f"{args.task_id}.status.json")

    if not os.path.exists(status_file):
        print(f"--- Task {args.task_id}: status file not found ---")
        sys.exit(1)

    start_wait = time.time()

    while True:
        data = read_status(status_file)
        if data is None:
            print(f"--- Task {args.task_id}: corrupted status file ---")
            sys.exit(1)

        status = data.get("status", "UNKNOWN")
        agent = data.get("agent", "unknown")
        task_start = data.get("start_time", start_wait)
        duration = format_duration(time.time() - task_start)

        if status == "COMPLETED":
            print(f"--- Task {args.task_id} ({agent}) completed in {duration} ---")
            summary_file = data.get("summary_file")
            if summary_file and os.path.exists(summary_file):
                with open(summary_file, 'r') as f:
                    content = f.read().strip()
                if content:
                    print(f"\n{content}")
                else:
                    print("\n(Summary file is empty)")
            report_file = data.get("report_file")
            if report_file and os.path.exists(report_file) and os.path.getsize(report_file) > 0:
                print(f"\nReport: {report_file}")
            sys.exit(0)

        elif status == "FAILED":
            print(f"--- Task {args.task_id} ({agent}) FAILED after {duration} ---")
            error = data.get("error")
            if error:
                print(f"Error: {error}")
            summary_file = data.get("summary_file")
            if summary_file and os.path.exists(summary_file) and os.path.getsize(summary_file) > 0:
                with open(summary_file, 'r') as f:
                    print(f"\n{f.read().strip()}")
            sys.exit(1)

        elif status == "CANCELLED":
            print(f"--- Task {args.task_id} ({agent}) was CANCELLED after {duration} ---")
            sys.exit(0)

        elif status == "RUNNING":
            pid = resolve_pid(data)
            if pid and not is_pid_alive(pid):
                data["status"] = "FAILED"
                data["error"] = "Process crashed or was killed externally."
                try:
                    with open(status_file, 'w') as f:
                        json.dump(data, f)
                except IOError:
                    pass
                print(f"--- Task {args.task_id} ({agent}) CRASHED after {duration} ---")
                print("Error: Process crashed or was killed externally.")
                sys.exit(1)

        elapsed = time.time() - start_wait
        if elapsed > args.timeout:
            print(f"--- Watcher timeout: Task {args.task_id} still running after {format_duration(elapsed)} ---")
            sys.exit(2)

        time.sleep(args.interval)


if __name__ == "__main__":
    main()
