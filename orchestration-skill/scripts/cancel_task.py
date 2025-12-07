import argparse
import json
import os
import signal
import sys

def main():
    parser = argparse.ArgumentParser(description="Cancel a running task.")
    parser.add_argument("--task_id", required=True, help="The ID of the task to cancel.")
    args = parser.parse_args()

    # Updated to point to project-local logs
    status_file = os.path.join(os.getcwd(), "logs", "orchestration", "status", f"{args.task_id}.status.json")

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

    pid = data.get("pid")
    if not pid:
        print(json.dumps({"error": "No PID found in status file."}))
        sys.exit(1)

    try:
        # Try to kill the process group to ensure child processes are also killed
        os.killpg(os.getpgid(pid), signal.SIGTERM)
        # Also try killing the PID directly just in case
        try:
            os.kill(pid, signal.SIGTERM)
        except:
            pass
            
        print(json.dumps({"status": "CANCELLED", "task_id": args.task_id}))
        
        # Update status file
        data["status"] = "CANCELLED"
        with open(status_file, 'w') as f:
            json.dump(data, f)
            
    except ProcessLookupError:
        print(json.dumps({"status": "CANCELLED", "warning": "Process was not running, but status updated."}))
        data["status"] = "CANCELLED"
        with open(status_file, 'w') as f:
            json.dump(data, f)
    except Exception as e:
        print(json.dumps({"error": f"Failed to kill process: {str(e)}"}))
        sys.exit(1)

if __name__ == "__main__":
    main()
