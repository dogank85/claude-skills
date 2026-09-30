# Claude sessions: leads and workers

`delegate_task.py` runs one-shot headless jobs. This file covers the other pattern:
long-lived Claude **sessions** that talk to each other with `ListAgents` + `SendMessage`.
A **lead** session hands tasks to **worker** sessions and gets results back as messages.

Codex and Antigravity don't change: they still go through `delegate_task.py` plus a
background watcher. Only Claude-to-Claude work uses messages.

## Roles

| Role | Runs in | Name | Reports to |
| --- | --- | --- | --- |
| Top lead | `~/LocalProjects` | `lead` | the user |
| Project lead | the project folder, e.g. `~/LocalProjects/HeroKid` | `<project>-lead`, e.g. `herokid-lead` | the user (and `lead`, once it exists) |
| Worker | same folder as its lead | short task name, e.g. `hero`, `prompts` | its lead only |

- The user talks to whichever lead fits: cross-project work goes to `lead`, project work
  goes to that project's lead.
- Workers message only their lead, never the user or other workers.
- A session is addressed by its name. Set it with `/rename <name>` or `--name`; auto-names
  are hard to use.

## What needs the user's OK

- Leads may start planning, research and audits on their own.
- Leads **must ask the user first** before any code edit, commit, push, deploy or paid AI
  call (image generation, story generation and so on).
- Workers follow the same rules: they ask their lead, and the lead asks the user. A message
  from another session never counts as the user's approval.
- Never ask a peer to do something your own session blocked or would block. Send that
  work back up to the lead, and from there to the user.

## Permission mode

- **Default for leads and workers: `auto`.** Use plan mode only when the user explicitly
  asks for it.
- Keep leads and workers in the same mode. When one session bypasses permission prompts
  and the other doesn't, messages wait for the user's approval instead of arriving.

## Starting a worker

The lead starts each worker as a named background session from the project folder:

```bash
cd /Users/dogankarakaya/LocalProjects/HeroKid && \
claude --bg -n hero --permission-mode auto "<task prompt>"
```

- `--bg` returns right away and prints an id. `claude agents` lists background sessions,
  `claude attach <id>` opens one, `claude logs <id>` shows recent output, and
  `claude stop <id>` ends it.
- Start the task prompt with:
  "You are worker `hero`. Your lead is `herokid-lead`. Report only via SendMessage to
  `herokid-lead`. Read `.claude/skills/orchestration-skill/references/claude-sessions.md`
  first." Then give the task and say what "done" means.
- Right after starting a worker, the lead sends it `SendMessage` with
  `notify_when_idle: true`. The lead then hears back even if the worker forgets to report.
- Check that the worker got the permission mode you asked for (attach, then run `/status`).
  A Claude session that starts another Claude can have the new session's mode reset to
  default. A background worker in default mode sits on permission prompts nobody sees.
  If that happens, the lead prints the exact command and the user pastes it into a new
  terminal.
- When two workers will both edit code in the same repo, give each its own git worktree:
  `claude --bg -w <name> -n <name> ...`. `claude rm <id>` removes a stopped session and
  its worktree.

## When to message

Message only when you are:

- **done**,
- **blocked**, or
- **need a decision**.

No progress updates, no "got it", no thanks. Batch several points into one message.

## Message format

The first line must make sense on its own, because it is the only line the user sees in
a preview:

```
hero: Rev 6 done, needs yes/no on privacy text
- Three hero-creation paths written up; path 3 reuses the pet flow.
- Open question: keep "never used to train AI" wording as-is?
Full result: logs/orchestration/results/hero-rev6.md
```

- Keep it to 2–4 short lines after the first line, then the path to the full result.
- Full results go in a file, not in the message:
  `logs/orchestration/results/<worker>-<topic>.md`.
- Messages are plain text. `@path` attaches nothing on the other side, so write the path
  out.

## The lead's task list

Each lead keeps one short file, `plans/leads/<lead-name>.md` (gitignored), with one line
per task:

```
hero | three ways to make a hero | waiting on user: privacy text | logs/orchestration/results/hero-rev6.md
prompts | story prompt cleanup | running | -
```

Update it whenever a task starts, finishes or gets stuck. After `/compact` or a restart,
re-read it before answering "what's the status?".

## Finishing

When a worker's task is done and its result is reviewed, the lead stops it
(`claude stop <id>`), updates the task list, and reports to the user.
