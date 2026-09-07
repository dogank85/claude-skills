# Agent Capabilities Inventory

This is a template. The actual capabilities depend on what's installed in your project. Before delegating, discover what's available using the commands below.

## Discovering Available Capabilities

### Claude Code
- Skills: Check `.claude/skills/` directory or run `claude agents`
- MCP servers: Check `.mcp.json` or run `/mcp`

### Codex CLI
- Skills: Check Codex skill directories
- Built-in tools: file editing, shell commands

### Antigravity CLI (`agy`)
- Multi-provider model router: run `agy models` to list available models
- Model selection by exact display name via `--model "<name>"`
- Built-in tools: file editing, shell commands

## Delegation Strategy

When orchestrating tasks, consider these general guidelines:

### Delegate to Claude Code when:
- Workflow requires complex tool orchestration
- Need reliable file read/write operations
- Multi-step tool execution with validation
- Comprehensive analysis or audit tasks

### Delegate to Codex CLI when:
- Workflow is pure execution (running tests, commands)
- Straightforward implementation tasks
- Fast, instructions-only approach works

### Delegate to Antigravity CLI when:
- You need additional capacity from its own multi-provider router
- You want high-reasoning work routed to Claude Opus 4.6 via `--effort high`
- Multi-file implementation/redesign tasks where its built-in file tools shine
- NOTE: conversation resume (`--parent_task_id`) is unsupported — agy emits no session_id

### Keep in the orchestrator when:
- Task coordination and planning
- Deciding which agent handles what
- Reviewing and synthesizing results from multiple agents

## Customizing This File

To populate this file with your project's specific capabilities:
1. Check installed Claude skills: `ls .claude/skills/`
2. Check Codex capabilities: review Codex skill directories
3. Add project-specific delegation rules below

## Project-Specific Capabilities

<!-- Add your project's specific skills, MCPs, and delegation rules here -->
