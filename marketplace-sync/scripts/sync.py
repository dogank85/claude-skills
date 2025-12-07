#!/usr/bin/env python3
import os
import shutil
import sys
import argparse

def main():
    parser = argparse.ArgumentParser(description="Sync skills from current project to marketplace")
    parser.add_argument("--marketplace", required=True, help="Path to local marketplace repository")
    parser.add_argument("--source", default=".claude/skills", help="Path to skills in current project (default: .claude/skills)")
    args = parser.parse_args()

    # Resolve paths
    source_base = os.path.abspath(args.source)
    marketplace_path = os.path.abspath(args.marketplace)

    print(f"📦 Syncing skills...")
    print(f"   Source: {source_base}")
    print(f"   Dest:   {marketplace_path}")
    print("-" * 50)

    if not os.path.exists(source_base):
        print(f"❌ Source directory not found: {source_base}")
        sys.exit(1)

    if not os.path.exists(marketplace_path):
        print(f"❌ Marketplace directory not found: {marketplace_path}")
        sys.exit(1)

    # Patterns to exclude
    exclude_patterns = shutil.ignore_patterns(
        "__pycache__", ".git", ".DS_Store", "logs", "node_modules", ".venv", "venv"
    )

    # Find skills in source
    skills_found = 0
    skills_synced = 0
    
    for item in os.listdir(source_base):
        source_item_path = os.path.join(source_base, item)
        
        # Check if it looks like a skill (has SKILL.md)
        if os.path.isdir(source_item_path) and os.path.exists(os.path.join(source_item_path, "SKILL.md")):
            skills_found += 1
            skill_name = item
            dest_item_path = os.path.join(marketplace_path, skill_name)
            
            print(f"🔄 Syncing {skill_name}...")
            
            try:
                # Remove destination if exists (clean sync)
                if os.path.exists(dest_item_path):
                    shutil.rmtree(dest_item_path)
                
                # Copy
                shutil.copytree(source_item_path, dest_item_path, ignore=exclude_patterns)
                print(f"   ✅ Synced")
                skills_synced += 1
            except Exception as e:
                print(f"   ❌ Failed: {e}")

    print("-" * 50)
    print(f"🚀 Completed. Synced {skills_synced}/{skills_found} skills found.")

if __name__ == "__main__":
    main()
