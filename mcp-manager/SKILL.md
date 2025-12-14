---
name: mcp-manager
description: This skill should be used when the user wants to add, remove, or list MCP servers for Claude Code, Codex CLI, or Gemini CLI.
license: Complete terms in LICENSE.txt
---

# MCP Manager

This skill provides guidance for managing Model Context Protocol (MCP) servers for Claude Code, Codex CLI, and Gemini CLI.

## About This Skill

This skill helps you manage MCP servers for different command-line interfaces. It provides instructions on how to add, list, and remove servers for Claude, Codex, and Gemini.

### When to Use This Skill

Use this skill when the user asks to:

- Add a new MCP server.
- Configure an existing MCP server.
- List available MCP servers.
- Remove an MCP server.

The user must specify which CLI they are targeting (Claude, Codex, or Gemini).

## How to Use This Skill

1.  **Identify the target CLI:** Ask the user which CLI they want to configure (Claude, Codex, or Gemini).
2.  **Gather server details:** Ask the user for the necessary information to configure the server. This may include:
    - Server name
    - Transport type (stdio, http, sse)
    - URL or command
    - Authentication details (API keys, headers, etc.)
    - Scope (for Claude and Gemini)
3.  **Consult the reference documents:** The `references/` directory contains detailed documentation for each CLI's MCP implementation. Use these documents to construct the correct command.
    - For Claude, refer to `references/claude_mcp.md`.
    - For Codex, refer to `references/codex_mcp.md`.
    - For Gemini, refer to `references/gemini_mcp.md`.
4.  **Construct and execute the command:** Based on the user's request and the reference material, construct the appropriate command and execute it using the `run_shell_command` tool.

### Example: Adding a Server

**User:** "I want to add a new MCP server for Gemini."

**You:** "Okay, what is the name of the server, what is the transport type, and what is the command or URL?"

**User:** "The name is `my-server`, it's a stdio server, and the command is `python server.py`."

**Action:**

1.  Consult `references/gemini_mcp.md` to find the `gemini mcp add` command syntax.
2.  Construct the command: `gemini mcp add my-server python server.py`
3.  Execute the command using `run_shell_command`.

### Example Commands

Here are some example commands for each CLI. Refer to the documentation in the `references/` directory for more details.

#### Claude Code

```bash
# Add a remote HTTP server
claude mcp add --transport http notion https://mcp.notion.com/mcp

# Add a local stdio server
claude mcp add --transport stdio airtable --env AIRTABLE_API_KEY=YOUR_KEY -- npx -y airtable-mcp-server

# List servers
claude mcp list

# Remove a server
claude mcp remove github
```

#### Codex CLI

```bash
# Add a stdio server
codex mcp add context7 -- npx -y @upstash/context7-mcp

# List servers
codex mcp list

# Remove a server
codex mcp remove context7
```

#### Gemini CLI

```bash
# Add a stdio server
gemini mcp add my-stdio-server /path/to/server arg1 arg2

# Add an HTTP server
gemini mcp add --transport http http-server https://api.example.com/mcp/

# List servers
gemini mcp list

# Remove a server
gemini mcp remove my-server
```
