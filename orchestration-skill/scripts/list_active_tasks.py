import json
import os
import glob

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    skill_root = os.path.dirname(script_dir)
    log_dir = os.path.join(skill_root, "logs", "status")
    
    if not os.path.exists(log_dir):
        print("[]")
        return

    active_tasks = []
    
    for status_file in glob.glob(os.path.join(log_dir, "*.status.json")):
        try:
            with open(status_file, 'r') as f:
                data = json.load(f)
                
            if data.get("status") == "RUNNING":
                pid = data.get("pid")
                is_running = False
                if pid:
                    try:
                        os.kill(pid, 0)
                        is_running = True
                    except ProcessLookupError:
                        # Process crashed - update status file
                        data["status"] = "FAILED"
                        data["error"] = "Process crashed or was killed externally."
                        try:
                            with open(status_file, 'w') as f:
                                json.dump(data, f)
                        except:
                            pass
                
                if is_running:
                    active_tasks.append(data)
        except:
            pass
            
    print(json.dumps(active_tasks, indent=2))

if __name__ == "__main__":
    main()
