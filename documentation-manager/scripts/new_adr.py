#!/usr/bin/env python3
import os
import argparse
import datetime
import re

def get_project_root():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.abspath(os.path.join(script_dir, "../../../.."))

def ensure_adr_dir(root):
    adr_dir = os.path.join(root, "docs", "adr")
    if not os.path.exists(adr_dir):
        print(f"Initializing ADR directory at {adr_dir}...")
        os.makedirs(adr_dir)
    return adr_dir

def get_next_adr_number(adr_dir):
    files = os.listdir(adr_dir)
    max_num = 0
    for f in files:
        if f.endswith(".md"):
            match = re.match(r"^(\d+)-", f)
            if match:
                num = int(match.group(1))
                if num > max_num:
                    max_num = num
    return max_num + 1

def create_adr(root, title):
    adr_dir = ensure_adr_dir(root)
    next_num = get_next_adr_number(adr_dir)
    
    slug = title.lower().replace(" ", "-")
    # Clean slug
    slug = re.sub(r"[^a-z0-9-]", "", slug)
    
    filename = f"{next_num:03d}-{slug}.md"
    filepath = os.path.join(adr_dir, filename)
    
    today = datetime.date.today().isoformat()
    
    template = f"""# {next_num}. {title}

Date: {today}

## Status

Accepted

## Context

The issue motivating this decision, and any context that influences it.

## Decision

The change that we're proposing or have agreed to implement.

## Consequences

What becomes easier or more difficult to do and any risks introduced by the change.
"""

    with open(filepath, "w") as f:
        f.write(template)
        
    print(f"✅ Created New ADR: {filepath}")

def main():
    parser = argparse.ArgumentParser(description="Create a new Architecture Decision Record (ADR)")
    parser.add_argument("title", help="Title of the decision")
    args = parser.parse_args()

    root = get_project_root()
    create_adr(root, args.title)

if __name__ == "__main__":
    main()
