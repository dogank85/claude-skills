#!/usr/bin/env python3
import os
import argparse
import datetime
import re

def get_project_root():
    # Assume script is in .claude/skills/documentation-manager/scripts
    # Root is 4 levels up
    script_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.abspath(os.path.join(script_dir, "../../../.."))

def ensure_changelog(root):
    changelog_path = os.path.join(root, "CHANGELOG.md")
    if not os.path.exists(changelog_path):
        print("Initializing CHANGELOG.md...")
        with open(changelog_path, "w") as f:
            f.write("# Changelog\n\nAll notable changes to this project will be documented in this file.\n\n")
    return changelog_path

def add_entry(root, message, type_):
    changelog_path = ensure_changelog(root)
    today = datetime.date.today().isoformat()
    
    with open(changelog_path, "r") as f:
        content = f.read()

    # Simple logic: Check if today's header exists
    header_pattern = f"## [{today}]"
    
    entry_line = f"- **{type_.upper()}**: {message}"
    
    if header_pattern in content:
        # Insert after the header
        lines = content.splitlines()
        new_lines = []
        inserted = False
        for line in lines:
            new_lines.append(line)
            if not inserted and line.startswith(f"## [{today}]"):
                new_lines.append(entry_line)
                inserted = True
        
        with open(changelog_path, "w") as f:
            f.write("\n".join(new_lines) + "\n")
    else:
        # Prepend new section after main title
        lines = content.splitlines()
        insert_idx = 0
        for i, line in enumerate(lines):
            if line.startswith("# Changelog"):
                insert_idx = i + 2 # Skip title and description
                break
        
        new_section = [
            f"",
            f"## [{today}]",
            entry_line
        ]
        
        lines[insert_idx:insert_idx] = new_section
        with open(changelog_path, "w") as f:
            f.write("\n".join(lines) + "\n")

    print(f"✅ Logged to CHANGELOG.md: {message}")

def main():
    parser = argparse.ArgumentParser(description="Log a change to CHANGELOG.md")
    parser.add_argument("message", help="Description of the change")
    parser.add_argument("--type", choices=["feat", "fix", "changed", "docs", "refactor"], default="changed", help="Type of change")
    args = parser.parse_args()

    root = get_project_root()
    add_entry(root, args.message, args.type)

if __name__ == "__main__":
    main()
