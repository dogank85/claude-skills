<!-- Codex CLI Custom Prompt Template -->
<!-- Location: ~/.codex/prompts/ -->
<!-- Name: The filename (without .md) becomes the command name -->
<!-- Invoked as: /prompts:<name> -->

---
description: Brief description shown in the slash popup
argument-hint: [FILES=<paths>] [CUSTOM_ARG="<value>"]
---

Your prompt instructions here.

## Features you can use:

### Positional placeholders:
- $1, $2, ... $9 for space-separated arguments
- $ARGUMENTS for all arguments together

### Named placeholders:
- Use uppercase names like $FILE or $TICKET_ID
- Supply as KEY=value when invoking
- Quote values with spaces: FOCUS="loading state"

### Literal dollar signs:
- Use $$ to emit a single $

## Task
Describe what this custom prompt should accomplish.
If files are specified, stage them first: $FILES.
Use other arguments as needed: $CUSTOM_ARG
