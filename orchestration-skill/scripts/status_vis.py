#!/usr/bin/env python3
import json
import os
import time
import sys

def get_active_tasks():
    # Path to the status directory relative to the project root
    # We assume this script is run from the project root or we can find the logs dir
    # But for the status line, the CWD is usually the project root.
    
    # Try to find the logs directory
    cwd = os.getcwd()
    status_dir = os.path.join(cwd, "logs", "orchestration", "status")
    
    if not os.path.exists(status_dir):
        return []
        
    active_tasks = []
    current_time = time.time()
    
    try:
        for filename in os.listdir(status_dir):
            if not filename.endswith(".status.json"):
                continue
                
            file_path = os.path.join(status_dir, filename)
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                    
                if data.get("status") == "RUNNING":
                    # Calculate duration
                    start_time = data.get("start_time", current_time)
                    duration = int(current_time - start_time)
                    
                    if duration < 60:
                        dur_str = f"{duration}s"
                    else:
                        dur_str = f"{duration//60}m"
                        
                    active_tasks.append({
                        "agent": data.get("agent", "unknown"),
                        "duration": dur_str
                    })
            except:
                continue
    except:
        pass
        
    return active_tasks

def main():
    tasks = get_active_tasks()
    
    if not tasks:
        return
        
    # Icon Mapping
    icons = {
        "gemini": "💎",
        "claude": "🔶",
        "codex": "⚡",
        "unknown": "❓"
    }
    
    output_parts = []
    for task in tasks:
        icon = icons.get(task["agent"], icons["unknown"])
        output_parts.append(f"{icon} {task['duration']}")
        
    if output_parts:
        # Print with a leading pipe separator and pipe join
        # Example: " | 💎 236m | ⚡ 12s"
        print(" | " + " | ".join(output_parts), end="")

if __name__ == "__main__":
    main()
