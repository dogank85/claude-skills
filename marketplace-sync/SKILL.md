---
name: marketplace-sync
description: Syncs skills from your current project to a local marketplace repository.
version: 1.0.0
---

# Marketplace Sync Skill

This skill synchronizes skills developed in your current project (under `.claude/skills`) to a local clone of your marketplace repository.

## When to Use

Use this skill when:
- You have made changes to a skill in your project.
- You want to publish those changes to your shared marketplace.

## How to Use

Run the sync script provided by this skill:

```bash
python3 scripts/sync.py --marketplace /path/to/claude-skills
```

### Arguments

- `--marketplace`: (Required) The absolute path to your local marketplace repository.
- `--source`: (Optional) The path to your project's skills directory. Defaults to `.claude/skills`.

## Features

- **Clean Sync**: Removes old files in the marketplace destination before copying to ensuring deleted files are removed.
- **Exclusions**: Automatically excludes `logs/`, `.git/`, `__pycache__/`, `node_modules/`, and other runtime artifacts.
