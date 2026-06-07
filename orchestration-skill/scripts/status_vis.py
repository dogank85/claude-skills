#!/usr/bin/env python3
import os
import json
import time
import sys

# ANTML Colors
AMBER = "\033[33m"
RESET = "\033[0m"


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
        return True


def get_active_tasks():
    """Get active orchestration tasks and return ONLY the task icons"""
    cwd = os.getcwd()
    status_dir = os.path.join(cwd, "logs", "orchestration", "status")

    if not os.path.exists(status_dir):
        return []

    active_tasks = []
    current_time = time.time()

    try:
        if os.path.isdir(status_dir):
            for filename in os.listdir(status_dir):
                if not filename.endswith(".status.json"):
                    continue

                file_path = os.path.join(status_dir, filename)
                try:
                    with open(file_path, 'r') as f:
                        data = json.load(f)

                    if data.get("status") == "RUNNING":
                        pid = resolve_pid(data)
                        if not is_pid_alive(pid):
                            continue

                        start_time = data.get("start_time", current_time)
                        duration = int(current_time - start_time)
                        time_str = f"{duration // 60}m" if duration >= 60 else f"{duration}s"

                        agent = data.get("agent", "agent")
                        icon = {"claude": "🤖", "gemini": "⚡", "codex": "🔶", "antigravity": "🪐"}.get(agent, "⌛")
                        active_tasks.append(f"{icon} {AMBER}{time_str}{RESET}")
                except:
                    continue
    except:
        pass

    return active_tasks

def main():
    """Output ONLY active task icons for orchestration, nothing else"""
    tasks = get_active_tasks()

    if tasks:
        output = " | ".join(tasks)
        sys.stdout.write(output)
        sys.stdout.flush()

if __name__ == "__main__":
    main()
