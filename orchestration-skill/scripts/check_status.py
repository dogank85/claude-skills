import argparse
import json
import os
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


def main():
    parser = argparse.ArgumentParser(description="Check the status of a delegated task.")
    parser.add_argument("--task_id", required=True, help="The ID of the task to check.")

    args = parser.parse_args()

    status_file = os.path.join("logs", "orchestration", "status", f"{args.task_id}.status.json")
    
    if not os.path.exists(status_file):
        print(json.dumps({"error": "Task not found"}))
        sys.exit(1)
        
    try:
        with open(status_file, 'r') as f:
            data = json.load(f)
            
        # Check for crash (PID not running but status is RUNNING)
        if data.get("status") == "RUNNING":
            pid = resolve_pid(data)
            if pid:
                try:
                    # Signal 0 checks if process exists
                    os.kill(pid, 0)
                except ProcessLookupError:
                    data["status"] = "FAILED"
                    data["error"] = "Process crashed or was killed externally."
                    # Update the file to reflect reality
                    with open(status_file, 'w') as f:
                        json.dump(data, f)
        
        # Check for summary file warnings
        if data.get("status") == "COMPLETED":
            summary_file = data.get("summary_file")
            if summary_file and os.path.exists(summary_file):
                try:
                    with open(summary_file, 'r') as f:
                        content = f.read()
                        if not content:
                            data["warning"] = "Summary file is empty."
                        elif "WARNING: Agent failed to write summary" in content:
                            data["warning"] = "Agent failed to write summary. Fallback used."
                except:
                    data["warning"] = "Could not read summary file."
            else:
                data["warning"] = "Summary file missing."
            
        print(json.dumps(data, indent=2))
        
    except json.JSONDecodeError:
        print(json.dumps({"status": "ERROR", "message": "Corrupted status file."}))
    except Exception as e:
        print(json.dumps({"status": "ERROR", "message": str(e)}))

if __name__ == "__main__":
    main()
