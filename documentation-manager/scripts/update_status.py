#!/usr/bin/env python3
import os
import argparse
import datetime
import re

def get_project_root():
    # Walk up from the current working directory to the nearest .git,
    # so the script writes into the project it is run from regardless
    # of where the skill itself is installed (repo, plugin cache, etc.).
    path = os.getcwd()
    while True:
        if os.path.exists(os.path.join(path, ".git")):
            return path
        parent = os.path.dirname(path)
        if parent == path:
            raise SystemExit("Error: no .git found above the current directory; run from inside the project.")
        path = parent

def update_status(root, status_text, blockers=None):
    status_path = os.path.join(root, "docs", "PROJECT_STATUS.md")
    
    # Simple overwrite or prepend? 
    # Let's use a structured format:
    # # Project Status
    # **Last Updated:** YYYY-MM-DD
    # ## Current Focus
    # ...
    # ## Blockers
    # ...
    
    today = datetime.date.today().isoformat()
    
    content = f"""# Project Status

**Last Updated:** {today}

## Current Focus
{status_text}

## Blockers
{blockers if blockers else "None"}

## Status History (Archives)
See `CHANGELOG.md` for detailed history.
"""
    
    with open(status_path, "w") as f:
        f.write(content)
        
    print(f"✅ Updated PROJECT_STATUS.md")

def main():
    parser = argparse.ArgumentParser(description="Update PROJECT_STATUS.md")
    parser.add_argument("status", help="Current status/focus description")
    parser.add_argument("--blockers", help="Any active blockers", default=None)
    args = parser.parse_args()

    root = get_project_root()
    update_status(root, args.status, args.blockers)

if __name__ == "__main__":
    main()
