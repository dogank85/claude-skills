# claude-skills

A personal [Claude Code](https://claude.com/claude-code) plugin marketplace by Dogan Karakaya. It bundles a set of skills and slash commands for documentation, image generation, multi-agent orchestration, MCP management, and developer workflow automation across Claude Code, Codex CLI, and Gemini CLI.

The marketplace manifest is [`.claude-plugin/marketplace.json`](.claude-plugin/marketplace.json) and registers under the name **`herokid-local-marketplace`**.

## Installation

Add the marketplace, then install whichever plugins you want:

```bash
# In Claude Code
/plugin marketplace add dogank85/claude-skills
/plugin install orchestration-skill@herokid-local-marketplace
```

Browse and install interactively with `/plugin`. With auto-update enabled, Claude Code re-pulls from GitHub periodically so installed plugins stay current.

## Plugins

| Plugin | Version | What it does |
| --- | --- | --- |
| [`documentation-manager`](documentation-manager) | 1.0.0 | Automates project documentation maintenance — Changelog, ADRs, and status docs. |
| [`gemini-image-gen`](gemini-image-gen) | 1.0.0 | Image generation, editing, and multi-turn visual refinement using Gemini 2.5 Flash and Gemini 3 Pro, with high-fidelity text rendering for branding and asset production. |
| [`herokid-channel`](herokid-channel) | 1.0.0 | General-purpose notification channel. Any local process can `POST` to `localhost:9999` and the message is pushed into the active Claude Code session instantly. |
| [`marketplace-sync`](marketplace-sync) | 1.0.0 | Syncs skills from a project's `.claude/skills` directory into a local clone of this marketplace repo. |
| [`mcp-manager`](mcp-manager) | 1.0.0 | Add, remove, and list MCP servers across Claude Code, Codex CLI, and Gemini CLI. |
| [`orchestration-skill`](orchestration-skill) | 1.2.0 | Headless multi-agent orchestration (Claude, Gemini, Codex, Antigravity) using a fire-and-forget pattern for delegating background and parallel work. |
| [`slash-command-creator`](slash-command-creator) | 1.0.0 | Scaffolds custom slash commands for Claude Code, Codex CLI, and Gemini CLI. |
| [`summary`](summary) | 1.0.0 | Generates structured conversation summaries for AI-agent handoff and context preservation. |

## Repository layout

```
.claude-plugin/marketplace.json   # marketplace manifest (lists all plugins)
<plugin-name>/
  SKILL.md                        # skill definition (name, description, instructions)
  plugin.json                     # plugin metadata
  scripts/ | commands/            # supporting scripts and slash commands (varies by plugin)
```

## Updating the marketplace

After editing or adding a skill in a project, publish it back into this repo with the `marketplace-sync` plugin:

```bash
python3 marketplace-sync/scripts/sync.py --marketplace /path/to/claude-skills
```

Then commit and push so the changes reach anyone who has the marketplace installed.
