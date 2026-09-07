import argparse
import json
import os
import sys
import time

TERMINAL = {"COMPLETED", "FAILED", "CANCELLED"}


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


def mark_crashed(status_file, data):
    """A task claiming RUNNING whose process is gone has crashed. Persist that
    so other watchers and check_status agree, mirroring watch_task.py."""
    data["status"] = "FAILED"
    data["error"] = "Process crashed or was killed externally."
    try:
        with open(status_file, 'w') as f:
            json.dump(data, f)
    except IOError:
        pass
    return data


def print_summary(task_id, data):
    agent = data.get("agent", "unknown")
    status = data.get("status", "UNKNOWN")
    start = data.get("start_time")
    duration = format_duration(time.time() - start) if start else "?"
    print(f"\n--- Task {task_id} ({agent}) {status} in {duration} ---")
    error = data.get("error")
    if error:
        print(f"Error: {error}")
    summary_file = data.get("summary_file")
    if summary_file and os.path.exists(summary_file) and os.path.getsize(summary_file) > 0:
        with open(summary_file, 'r') as f:
            print(f.read().strip())
    report_file = data.get("report_file")
    if report_file and os.path.exists(report_file) and os.path.getsize(report_file) > 0:
        print(f"Report: {report_file}")


def main():
    parser = argparse.ArgumentParser(description="Wait for multiple delegated tasks to finish (parallel barrier).")
    parser.add_argument("--ids", required=True, help="Comma-separated task IDs to wait for.")
    parser.add_argument("--interval", type=int, default=15, help="Polling interval in seconds (default: 15).")
    parser.add_argument("--timeout", type=int, default=3600, help="Max wait time in seconds for the whole batch (default: 3600).")
    args = parser.parse_args()

    task_ids = [t.strip() for t in args.ids.split(",") if t.strip()]
    if not task_ids:
        print("--- No task IDs provided ---")
        sys.exit(1)

    status_dir = os.path.join(os.path.abspath("logs"), "orchestration", "status")
    status_files = {tid: os.path.join(status_dir, f"{tid}.status.json") for tid in task_ids}

    missing = [tid for tid, sf in status_files.items() if not os.path.exists(sf)]
    if missing:
        print(f"--- Status file(s) not found for: {', '.join(missing)} ---")
        sys.exit(1)

    start_wait = time.time()
    final = {}  # task_id -> data, captured once a task reaches a terminal state
    last_done = -1
    last_beat = 0.0
    KEEPALIVE = 300  # seconds

    while True:
        for tid in task_ids:
            if tid in final:
                continue
            data = read_status(status_files[tid])
            if data is None:
                continue  # transient/corrupt read; retry next poll
            status = data.get("status", "UNKNOWN")
            if status == "RUNNING":
                pid = resolve_pid(data)
                if pid and not is_pid_alive(pid):
                    data = mark_crashed(status_files[tid], data)
                    status = data["status"]
            if status in TERMINAL:
                final[tid] = data

        if len(final) == len(task_ids):
            break

        if time.time() - start_wait > args.timeout:
            elapsed = format_duration(time.time() - start_wait)
            pending = [t for t in task_ids if t not in final]
            print(f"--- Batch timeout after {elapsed}: {len(pending)} task(s) still running: {', '.join(pending)} ---")
            for tid in task_ids:
                if tid in final:
                    print_summary(tid, final[tid])
            sys.exit(2)

        # Heartbeat: only when something actually changed, plus a slow keepalive
        # so a long quiet batch still isn't dead air. This watcher normally runs
        # in the background and its stdout lands in the orchestrator's context —
        # a line every poll would be ~240 lines an hour of pure noise, which is
        # the context bloat this whole skill exists to avoid.
        now = time.time()
        if len(final) != last_done or now - last_beat >= KEEPALIVE:
            elapsed = format_duration(now - start_wait)
            running = [t for t in task_ids if t not in final]
            print(f"[{elapsed}] {len(final)}/{len(task_ids)} done — running: {', '.join(running)}", flush=True)
            last_done = len(final)
            last_beat = now

        time.sleep(args.interval)

    elapsed = format_duration(time.time() - start_wait)
    completed = sum(1 for d in final.values() if d.get("status") == "COMPLETED")
    failed = len(final) - completed
    print(f"=== Batch complete in {elapsed}: {completed} completed, {failed} failed ===")
    for tid in task_ids:
        print_summary(tid, final[tid])

    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
