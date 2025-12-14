---
name: slash-command-creator
description: Use when creating custom slash commands for Claude Code, Gemini CLI, or Codex CLI. Applies when the user requests creating a slash command, custom command, or reusable prompt for any of these three coding assistants.
---

# Slash Command Creator

## Overview

This skill provides templates and documentation for creating custom slash commands across three coding assistant tools: Claude Code, Gemini CLI, and Codex CLI. Each tool has different file formats, locations, and capabilities for custom commands.

## When to Use This Skill

Use this skill when:

- User requests creating a slash command for any of the three tools
- User asks to create a custom command or reusable prompt
- User mentions automating a workflow via slash commands
- User wants to create commands for one, two, or all three tools simultaneously

## Quick Reference

### Command Locations by Tool

| Tool            | Global Location       | Project Location    | Format   |
| --------------- | --------------------- | ------------------- | -------- |
| **Gemini CLI**  | `~/.gemini/commands/` | `.gemini/commands/` | TOML     |
| **Claude Code** | `~/.claude/commands/` | `.claude/commands/` | Markdown |
| **Codex CLI**   | `~/.codex/prompts/`   | N/A                 | Markdown |

### Template Files

Templates are available in `assets/`:

- `gemini-template.toml` - Gemini CLI command template
- `claude-code-template.md` - Claude Code command template
- `codex-template.md` - Codex CLI custom prompt template

### Reference Documentation

Detailed documentation is available in `references/`:

- `gemini-cli-commands.md` - Gemini CLI built-in commands
- `gemini-cli-custom-commands.md` - Gemini CLI custom command creation
- `claude-code-custom-commands.md` - Claude Code custom command creation
- `codex-cli-custom-commands.md` - Codex CLI custom prompt creation

## Critical Architectural Differences

**Understanding what each tool can and cannot do is essential for creating effective commands.**

### Claude Code: Full Tool Execution

**Capabilities:**

- ✅ Can execute tools (Read, Grep, Bash, etc.) during command activation
- ✅ Can programmatically load files and configurations
- ✅ Commands can include multi-step workflows with tool calls
- ✅ Supports `allowed-tools` to restrict which tools can be used

**Example:** A command can include instructions like:

```markdown
STEP 1: Read `.config/settings.yaml`
STEP 2: Read each file listed in the config
STEP 3: Greet the user with loaded context
```

Claude Code will **execute** these Read operations automatically (with user approval if needed).

### Gemini CLI: Shell & File Injection

**Capabilities:**

- ✅ Can execute shell commands via `!{command}` and inject output
- ✅ Can inject file contents via `@{path}`
- ✅ Shell execution requires user confirmation
- ⚠️ Commands are expanded at invocation time, not interactive

**Example:** A command can include:

```toml
prompt = """
Current git status: !{git status}
Package info: @{package.json}
"""
```

Gemini CLI will execute the shell command and read the file, then inject results into the prompt **before** sending to the model.

### Codex CLI: Text Replacement Only

**Capabilities:**

- ✅ Supports argument placeholders (`$1`-`$9`, `$ARGUMENTS`, named variables)
- ❌ **Cannot execute tools or commands**
- ❌ **Cannot automatically load files**
- ⚠️ Can only **instruct** the model to perform actions

**Critical Limitation:**

Codex prompts are **pure text replacement**. When you write:

```markdown
STEP 1: Read `config.yaml`
```

Codex will send this instruction to the model, but **will not execute it automatically**. The model must then:

1. Recognize it should read the file
2. Use its Read tool
3. Wait for user approval
4. Process the file

**Workaround Strategies:**

1. **Explicit Instructions:** Tell the model step-by-step what to do

   ```markdown
   ## ACTIVATION SEQUENCE

   STEP 1: Read `.config/settings.yaml`
   STEP 2: Read `docs/brand-guidelines.md`
   STEP 3: After loading files, introduce yourself
   ```

2. **Pre-load Context:** Use `/mention` to add files before invoking

   ```bash
   /mention config.yaml
   /mention docs/brand-guidelines.md
   /prompts:mycommand
   ```

3. **Accept Limitations:** Design commands as conversational personas that ask for context

### Comparison Table

| Capability              | Claude Code         | Gemini CLI          | Codex CLI             |
| ----------------------- | ------------------- | ------------------- | --------------------- |
| **Auto-execute tools**  | ✅ Yes              | ❌ No               | ❌ No                 |
| **Auto-load files**     | ✅ Yes              | ✅ Via `@{path}`    | ❌ No (must instruct) |
| **Shell execution**     | ✅ Via `` !`cmd` `` | ✅ Via `!{cmd}`     | ❌ No                 |
| **Workflow automation** | ✅ Full automation  | ⚠️ Expand-then-send | ⚠️ Instruction only   |
| **User approval**       | Per tool call       | Per shell cmd       | Per tool call         |

### When Converting Commands Between Tools

**Claude Code → Codex:**

- Change tool executions to explicit instructions
- Add "ACTIVATION SEQUENCE" sections
- Set expectations: "Read these files, then greet"
- Accept that it won't be automatic

**Claude Code → Gemini:**

- Can preserve some automation via `!{...}` and `@{...}`
- Shell commands work but require confirmation
- File injection is straightforward

**Gemini → Codex:**

- Lose shell execution (`!{...}` → instructional text)
- Lose file injection (`@{...}` → "Read this file" instruction)

**Key Principle:** Design for the tool's capabilities, not against them.

## Creating Commands by Tool

### For Gemini CLI

**File Format:** TOML (`.toml` extension)

**Locations:**

- Global: `~/.gemini/commands/`
- Project: `.gemini/commands/`

**Key Features:**

- `{{args}}` - Inject user arguments (auto-escapes in shell commands)
- `!{command}` - Execute shell commands and inject output
- `@{path}` - Inject file contents
- Namespacing via subdirectories (e.g., `git/commit.toml` → `/git:commit`)

**Process:**

1. Read `assets/gemini-template.toml` for the base template
2. Determine scope (global vs project) based on user needs
3. Create the `.toml` file in the appropriate location
4. Fill in `prompt` (required) and `description` (optional)
5. Use special syntax as needed: `{{args}}`, `!{...}`, `@{...}`

**Reference:** Load `references/gemini-cli-custom-commands.md` for detailed syntax and examples.

### For Claude Code

**File Format:** Markdown (`.md` extension)

**Locations:**

- Personal: `~/.claude/commands/`
- Project: `.claude/commands/`

**Key Features:**

- YAML frontmatter for metadata (optional)
- `$1`, `$2`, `$ARGUMENTS` - Positional argument placeholders
- `` !`command` `` - Execute shell commands and inject output
- `@filename` - Inject file contents
- `allowed-tools` - Restrict which tools can be used
- Namespacing via subdirectories

**Process:**

1. Read `assets/claude-code-template.md` for the base template
2. Determine scope (personal vs project) based on user needs
3. Create the `.md` file in the appropriate location
4. Add YAML frontmatter if needed (description, allowed-tools, model, argument-hint)
5. Write command instructions using placeholders as needed

**Reference:** Load `references/claude-code-custom-commands.md` for detailed syntax and examples.

### For Codex CLI

**File Format:** Markdown (`.md` extension)

**Locations:**

- Global only: `~/.codex/prompts/`

**Key Features:**

- YAML frontmatter for metadata (optional)
- `$1`-`$9` - Positional placeholders (space-separated)
- `$ARGUMENTS` - All arguments together
- Named placeholders: `$FILE`, `$TICKET_ID`, etc. (uppercase)
- Supply named args as `KEY=value` when invoking
- `$$` - Literal dollar sign
- Invoked as `/prompts:<name>`

**Process:**

1. Read `assets/codex-template.md` for the base template
2. Create the `.md` file in `~/.codex/prompts/`
3. Add YAML frontmatter (description, argument-hint)
4. Write prompt instructions using placeholders as needed
5. Inform user to restart Codex or start new session to load

**Reference:** Load `references/codex-cli-custom-commands.md` for detailed syntax and examples.

## Workflow for Creating Commands

### Step 1: Identify Requirements

Ask or infer:

1. Which tool(s)? (Claude Code, Gemini CLI, Codex CLI, or all three)
2. What should the command do?
3. Does it need arguments? What kind?
4. Should it execute shell commands?
5. Should it read files?
6. Global or project-specific? (not applicable for Codex)

### Step 2: Choose Template

Based on the tool(s) identified, read the appropriate template(s) from `assets/`:

- Gemini CLI → `gemini-template.toml`
- Claude Code → `claude-code-template.md`
- Codex CLI → `codex-template.md`

### Step 3: Load Reference Documentation (If Needed)

If the command involves complex features (shell execution, file injection, arguments), load the relevant reference documentation from `references/`.

### Step 4: Create the Command File(s)

For each tool:

1. Determine the correct file path based on scope
2. Create the file with appropriate extension
3. Fill in metadata (frontmatter or TOML fields)
4. Write the command prompt/instructions
5. Add argument placeholders as needed
6. Add shell commands or file references as needed

### Step 5: Inform User

After creating the command(s):

1. Confirm file locations
2. Explain how to invoke (command name/syntax)
3. Note any restart requirements (Codex requires restart)
4. Provide example usage if helpful

## Special Syntax Comparison

| Feature         | Gemini CLI       | Claude Code              | Codex CLI                         |
| --------------- | ---------------- | ------------------------ | --------------------------------- |
| Arguments       | `{{args}}`       | `$1`, `$2`, `$ARGUMENTS` | `$1`-`$9`, `$ARGUMENTS`, `$NAMED` |
| Shell execution | `!{command}`     | `` !`command` ``         | N/A                               |
| File injection  | `@{path}`        | `@filename`              | N/A                               |
| Metadata format | TOML fields      | YAML frontmatter         | YAML frontmatter                  |
| Namespacing     | Subdirs → `:`    | Subdirs (shown in desc)  | N/A                               |
| Scope options   | Global + Project | Personal + Project       | Global only                       |

## Common Patterns

### Simple Command (No Arguments)

**Example:** A command that performs a fixed task

- Gemini: Simple `prompt` field with instructions
- Claude: Markdown body with instructions
- Codex: Markdown body with instructions

### Command with Arguments

**Example:** A command that takes user input

- Gemini: Use `{{args}}` in prompt
- Claude: Use `$1`, `$2`, or `$ARGUMENTS`
- Codex: Use `$1`-`$9` or named like `$FILE`

### Command with Shell Execution

**Example:** A command that runs git commands

- Gemini: Use `!{git status}` or `!{git diff}`
- Claude: Use `` !`git status` `` or `` !`git diff` ``
- Codex: Not supported (use allowed-tools instead)

### Command with File Reading

**Example:** A command that reads and processes files

- Gemini: Use `@{path/to/file}`
- Claude: Use `@filename`
- Codex: Not supported (use @ in invocation instead)

## Tips and Best Practices

### General Guidelines

1. **Be specific in descriptions** - Help users find commands in popups
2. **Document arguments** - Use `argument-hint` to show expected args
3. **Test commands** - Create and test before finalizing
4. **Namespace appropriately** - Use subdirs for organization (Gemini/Claude)
5. **Consider scope** - Global for reusable, project for specific workflows
6. **Mind security** - Shell commands in custom commands require approval
7. **Quote spaces** - When passing paths/values with spaces as arguments
8. **Reference docs** - Load reference docs for complex syntax needs

### Tool-Specific Best Practices

**For Claude Code:**

- Leverage tool execution for automation
- Use `allowed-tools` to restrict command capabilities
- Structure multi-step workflows knowing tools will execute
- Test with approval requirements in mind

**For Gemini CLI:**

- Use `!{...}` for shell commands that gather context
- Use `@{...}` for injecting file contents
- Remember: expansion happens before model sees the prompt
- Test shell commands for security and correctness

**For Codex:**

- Write clear, explicit instructions (model must interpret)
- Include "ACTIVATION SEQUENCE" for multi-step setups
- Set expectations: "After reading X, do Y"
- Consider recommending `/mention` for file pre-loading
- Accept that automation is limited to instruction, not execution

### Converting Between Tools

**When converting commands:**

1. Identify tool executions in the source command
2. Determine if the target tool can replicate the behavior
3. If not, convert to explicit instructions or document workarounds
4. Test thoroughly - behavior will differ between tools
5. Update documentation to reflect tool-specific limitations

## Resources

### assets/

Template files for each tool's command format:

- `gemini-template.toml` - Start here for Gemini CLI commands
- `claude-code-template.md` - Start here for Claude Code commands
- `codex-template.md` - Start here for Codex CLI custom prompts

### references/

Comprehensive documentation for custom command creation:

- `gemini-cli-commands.md` - Built-in Gemini CLI commands reference
- `gemini-cli-custom-commands.md` - Complete Gemini CLI custom command guide
- `claude-code-custom-commands.md` - Complete Claude Code custom command guide
- `codex-cli-custom-commands.md` - Complete Codex CLI custom prompt guide

Load these files when detailed syntax information is needed for complex commands.
