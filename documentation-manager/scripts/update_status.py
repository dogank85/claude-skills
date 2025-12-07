#!/usr/bin/env python3
import os
import argparse
import datetime
import re

def get_project_root():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.abspath(os.path.join(script_dir, "../../../.."))

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
