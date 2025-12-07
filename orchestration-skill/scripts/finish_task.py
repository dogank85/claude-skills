import argparse
import json
import os
import re
import sys
import subprocess

def send_notification(title, message, sound="Glass"):
    """
    Sends a macOS desktop notification and plays a sound using afplay.
    """
    try:
        # 1. Show Visual Notification
        safe_title = title.replace('"', '\\"')
        safe_message = message.replace('"', '\\"')
        
        # We explicitly remove 'sound name' from osascript because we will play it manually
        apple_script = f'display notification "{safe_message}" with title "{safe_title}"'
        subprocess.run(["osascript", "-e", apple_script], check=False, capture_output=True)
        
        # 2. Play Sound Explicitly
        # Verify sound exists, fallback to Glass, fallback to Ping
        sound_path = f"/System/Library/Sounds/{sound}.aiff"
        if not os.path.exists(sound_path):
            sound_path = "/System/Library/Sounds/Glass.aiff"
            
        subprocess.Popen(["afplay", sound_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
    except Exception as e:
        print(f"Notification failed: {e}", file=sys.stderr)

def extract_session_id(log_path, agent):
    """
    Robustly extracts session_id from a log file that might contain mixed output.
    """
    if not os.path.exists(log_path):
        return None
        
    try:
        with open(log_path, 'r', errors='replace') as f:
            content = f.read()
            
        # Strategy 1: Look for the last JSON object containing "session_id"
        # This regex looks for { ... "session_id": "..." ... } allowing for nested braces is hard with regex,
        # so we look for a simple pattern first.
        
        # Pattern: "session_id": "..."
        # We want the LAST occurrence.
        matches = list(re.finditer(r'"session_id"\s*:\s*"([^"]+)"', content))
        if matches:
            return matches[-1].group(1)
            
        # Strategy 2: If finding the key directly failed (maybe it's not quoted standardly?), try parsing lines as JSON
        # Codex often outputs JSONL
        lines = content.splitlines()
        for line in reversed(lines):
            line = line.strip()
            if not line: continue
            try:
                # Try to find a JSON object in the line (it might be surrounded by other text like "Output: {...}")
                # We find the first '{' and last '}'
                start = line.find('{')
                end = line.rfind('}')
                if start != -1 and end != -1 and end > start:
                    potential_json = line[start:end+1]
                    data = json.loads(potential_json)
                    if "session_id" in data:
                        return data["session_id"]
            except:
                continue
                
    except Exception as e:
        print(f"Error reading log file {log_path}: {e}", file=sys.stderr)
        
    return None

def main():
    parser = argparse.ArgumentParser(description="Finalize a delegated task.")
    parser.add_argument("--task_id", required=True, help="The ID of the task.")
    parser.add_argument("--log_file", required=True, help="Path to the log file.")
    parser.add_argument("--status_file", required=True, help="Path to the status file.")
    parser.add_argument("--summary_file", required=True, help="Path to the summary file.")
    parser.add_argument("--agent", required=True, help="The agent used.")
    parser.add_argument("--pid_file", help="Path to the pid file (optional, used for cleanup if needed).")
    args = parser.parse_args()

    # 1. Extract Session ID Robustly
    session_id = extract_session_id(args.log_file, args.agent)

    # 2. Update Status File
    try:
        if os.path.exists(args.status_file):
            with open(args.status_file, 'r') as f:
                data = json.load(f)
            
            data["status"] = "COMPLETED"
            # We don't unset the PID here because it's historical record, 
            # but arguably the process is gone now.
            
            if session_id:
                data["session_id"] = session_id
            
            with open(args.status_file, 'w') as f:
                json.dump(data, f)
        else:
            print(f"Status file not found: {args.status_file}", file=sys.stderr)
    except Exception as e:
        print(f"Error updating status file: {e}", file=sys.stderr)

    # 3. Summary Fallback Logic
    try:
        if os.path.exists(args.summary_file):
            if os.path.getsize(args.summary_file) == 0:
                # Summary is empty, perform fallback
                with open(args.summary_file, 'w') as f:
                    f.write("WARNING: Agent failed to write summary. Extracted from log:\n\n")
                    f.write("```\n")
                    
                # Append tail of log file (using python to avoid shell injection risk)
                try:
                    with open(args.log_file, 'r', errors='replace') as lf:
                        lines = lf.readlines()
                        tail = lines[-20:] if len(lines) > 20 else lines
                        
                    with open(args.summary_file, 'a') as f:
                        f.writelines(tail)
                except Exception as e:
                     with open(args.summary_file, 'a') as f:
                        f.write(f"Could not read log file: {e}\n")
                
                with open(args.summary_file, 'a') as f:
                    f.write("\n```\n")
    except Exception as e:
        print(f"Error in summary fallback: {e}", file=sys.stderr)

    # 4. Notify User
    try:
        # Determine status for notification
        status_msg = "Task Completed"
        sound = "Glass"
        
        # You could refine this based on whether the log has error keywords, but for now simple is good.
        send_notification("Orchestration Skill", f"{status_msg}: {args.task_id}", sound)
    except Exception as e:
        print(f"Notification error: {e}", file=sys.stderr)

if __name__ == "__main__":
    main()
