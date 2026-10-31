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
| Project lead | the project folder, e.g. `~/LocalProjects/HeroKid` | `<prefix>-lead`, e.g. `hk-lead` | the user (and `lead`, once it exists) |
| Worker | same folder as its lead | `<prefix>-<role>`, e.g. `hk-builder`, `hk-sim` | its lead only |

- The user talks to whichever lead fits: cross-project work goes to `lead`, project work
  goes to that project's lead.
- Workers message only their lead, never the user or other workers.
- A session is addressed by its name. Set it with `/rename <name>` or `--name`; auto-names
  are hard to use.

### Naming

`ListAgents` shows every Claude session on the machine, across projects, so every name
starts with a short project prefix: `hk-` (HeroKid), `elo-` (EloSudoku), `wc-` (worldcup),
`mkt-` (Marketing). Then one role from this fixed list:

| Role | Job |
| --- | --- |
| `lead` | plans, splits work, reviews, talks to the user (one per project) |
| `builder` | writes code and runs tests |
| `reviewer` | reviews only, changes nothing |
| `sim` | simulator or device testing; only a Desktop session with the simulator attached |
| `web` | browser testing |
| `research` | reading, searching, audits; no code |
| `writer` | docs, copy, translations |

- Name the job, never the start order (no `session03`).
- Tool-bound names (`sim`, `web`) are a promise: if the session restarts without that
  tool, rename or stop it before sending it work.
- Number only duplicates: `hk-builder-2`, never `-1`.
- Short, lowercase, no spaces.

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
claude --bg -n hk-builder --permission-mode auto "<task prompt>"
```

- `--bg` returns right away and prints an id. `claude agents` lists background sessions,
  `claude attach <id>` opens one, `claude logs <id>` shows recent output, and
  `claude stop <id>` ends it.
- Start the task prompt with:
  "You are worker `hk-builder`. Your lead is `hk-lead`. Report only via SendMessage to
  `hk-lead`. Read `.claude/skills/orchestration-skill/references/claude-sessions.md`
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
hk-builder: Rev 6 done, needs yes/no on privacy text
- Three hero-creation paths written up; path 3 reuses the pet flow.
- Open question: keep "never used to train AI" wording as-is?
Full result: logs/orchestration/results/hk-builder-rev6.md
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
hk-builder | three ways to make a hero | waiting on user: privacy text | logs/orchestration/results/hk-builder-rev6.md
hk-research | story prompt audit | running | -
```

Update it whenever a task starts, finishes or gets stuck. After `/compact` or a restart,
re-read it before answering "what's the status?".

## Codex review on the PR

Repos with the Codex GitHub app (`chatgpt-codex-connector[bot]`) get a review when a PR is
**opened** or a draft is marked ready. Later pushes are **not** reviewed until someone
comments `@codex review`:

```bash
gh pr comment <n> --body "@codex review"
```

- Done signal: a PR comment holds `"code_review":{"commit_sha":"<sha>",...,"status":"completed"}`
  plus `has_any_findings`. Wait for it with a background watcher (it wakes the lead):

  ```bash
  for i in $(seq 1 60); do
    s=$(gh api repos/<owner>/<repo>/issues/<n>/comments --jq '.[].body' \
      | grep -o '"code_review":{[^}]*}' | grep <short-sha> | tail -1)
    echo "$s" | grep -q '"status":"completed"' && { echo "$s"; exit 0; }
    sleep 30
  done; echo TIMEOUT
  ```

- Findings are inline comments: `gh api repos/<owner>/<repo>/pulls/<n>/comments --jq '.[] | "\(.path):\(.line) \(.body)"'`.
- Loop: show findings to the user, send fixes to the builder, review its diff, push, comment
  `@codex review` again. Merge only on a clean review and the user's OK.

## Finishing

When a worker's task is done and its result is reviewed, the lead stops it
(`claude stop <id>`), updates the task list, and reports to the user.
