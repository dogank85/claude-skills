<!-- Claude Code Custom Command Template -->
<!-- Location: ~/.claude/commands/ (personal) or .claude/commands/ (project) -->
<!-- Name: The filename (without .md) becomes the command name -->
<!-- Namespacing: Use subdirectories (e.g., frontend/component.md) -->

---
allowed-tools: Read, Grep, Glob, Bash
description: Brief description of what this command does
model: claude-sonnet-4-5-20250929
argument-hint: [arg1] [arg2]
---

Your command instructions here.

## Features you can use:

### Argument placeholders:
- Use $1, $2, etc. for positional arguments
- Use $ARGUMENTS for all arguments

### Bash command execution:
- Use !`command` to execute and inject output
- Example: !`git status`

### File references:
- Use @filename to inject file contents
- Example: @package.json

## Task
Describe what the command should accomplish.
