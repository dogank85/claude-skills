import json
import os
import glob


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


def main():
    log_dir = os.path.join("logs", "orchestration", "status")

    if not os.path.exists(log_dir):
        print("[]")
        return

    active_tasks = []

    for status_file in glob.glob(os.path.join(log_dir, "*.status.json")):
        try:
            with open(status_file, 'r') as f:
                data = json.load(f)

            if data.get("status") == "RUNNING":
                # Verify if it's actually running (crash detection)
                pid = resolve_pid(data)
                is_running = False
                if pid:
                    try:
                        os.kill(pid, 0)
                        is_running = True
                    except ProcessLookupError:
                        pass

                if is_running:
                    active_tasks.append(data)
        except:
            pass

    print(json.dumps(active_tasks, indent=2))

if __name__ == "__main__":
    main()
