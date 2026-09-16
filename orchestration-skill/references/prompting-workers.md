# Prompting a delegated worker

A delegated worker is not a chat partner. It gets one prompt, no follow-up turn, and no
human watching. Everything it needs to decide, it has to decide alone — and whatever it
gets wrong, you find out 20 minutes later from a summary that reads like success.

That changes what a good prompt looks like, and it changes it *differently per backend*.
The three models behind `--agent` fail in opposite directions, so the same prompt text
produces a different defect depending on which one you sent it to.

## The asymmetry

| | `--agent claude` | `--agent codex` | `--agent antigravity` |
| --- | --- | --- | --- |
| Model | `sonnet` / `opus` | `gpt-6-astra` | `gemini-3.8-flash-high` |
| Default scope behavior | **Widens** — adds steps you didn't ask for | **Narrows** — stops at a first pass | Follows the ask literally |
| Default verbosity | **Over-writes** long documents | Moderate | **Under-writes** — terse by default |
| Stopping behavior | Runs to completion | **Stops to await review that never comes** | Runs to completion |
| So your prompt must | Constrain scope, cap length | Define "done", forbid stopping | Ask for detail explicitly |

The codex row is the dangerous one. GPT-6 Astra is designed to reach a first implementation
and hand back for review — which is right in an interactive session and silently wrong
here. It stops, the wrapper fires, and you get a summary describing a first pass as though
it were the finished job.

`--effort high` on antigravity routes to `claude-opus-4-6-thinking`, a **Claude** model. At
that tier the claude column applies, not the antigravity one.

## Rules for every backend

**Settle ambiguity yourself; make the worker record it.** All three vendors document a
"pause and ask the user" behavior. There is no user. A worker that hits an ambiguity either
stalls or guesses silently, and a silent guess is worse. Tell it to choose the reasonable
reading, proceed, and state the assumption in its summary — then you can audit the
judgment call instead of discovering it as a surprise.

**Put the whole specification in the first prompt.** There is no second turn to repair an
under-specified task. Anthropic's guidance for its strongest agentic model is to give "the
complete task specification up front" and leave it to run — which is exactly this pattern,
so the effort you spend on the prompt is the effort you would otherwise spend re-delegating.

**Do not instruct self-verification.** "Double-check your work", "verify before
summarizing", "add a final verification step" — these used to help and now hurt. Anthropic
and OpenAI both report that current models already verify, and the instruction compounds
into wasted tokens without improving the result.

If what you actually want is *assurance the work was checked*, that is a tools problem, not
a wording problem: pass `--sandbox` so the worker has a shell to run the tests with. A
worker without Bash cannot verify anything, and will still write you a confident report —
the failure mode SKILL.md calls "a confident answer built on nothing." Tools, not words.

**Use one delimiter style.** XML tags or Markdown headings, consistently within a prompt.
Mixing them makes the model guess at which boundary is real.

**Long prompts: material first, the ask last.** When you are embedding a spec, a diff, or
file contents, put it up front and close with the instruction, bridged by an anchor
("Given the above, ..."). Critical constraints are the exception — those go at the very top
where they cannot be lost in the middle.

## `--agent claude`

**Constrain the scope.** Opus 5 applies its own judgment about what a task should be and
will add steps. For anything narrow, say so:

> Deliver what was asked, at the scope asked. Make routine judgment calls yourself. If a
> better approach exists, note it in one sentence and continue with the task as specified
> rather than substituting it.

**Cap further delegation.** Opus 5 spawns subagents readily, so a worker can fan out on its
own and multiply the cost of a delegation you thought was one agent. One line prevents it:
*"Do not delegate to subagents; complete this yourself."*

**For audits, ask for everything and filter afterward.** This one is counterintuitive:
"only report high-severity issues" or "be conservative" makes Opus 5 report *less*, because
it follows the instruction literally. You lose real findings. Ask for the complete list and
narrow it in a second pass — either your own reading, or a follow-up delegation.

**Calibrate the summary length.** Opus 5 writes long documents, and you read its summary
straight into your own context — the thing this skill exists to protect. One line prevents
it: *"Match the summary to its substance; no filler sections or restated recap."*

## `--agent codex`

**Define what "done" means, concretely.** This is the single highest-value sentence you can
add to a codex prompt. Not "implement the feature" but "done means: the change is
implemented, the test suite runs, failures caused by the change are fixed, and the affected
tests pass." Astra pulls toward the earliest defensible stopping point, so name a later one.

**Pre-authorize the safe actions, in words.** Astra will not act unless it knows an action
is safe, and it has nobody to ask. `--sandbox` grants the shell; it does not grant the
*permission*. Without both, a sandboxed worker stalls politely. OpenAI's own phrasing is
the template:

> The local tests use disposable fixtures and have no production access. Run them, fix
> failures caused by the requested change, and rerun affected tests without asking for
> approval at each step.

**How much this matters here, measured.** Two A/B runs on this harness — a failing test
suite, and a 240-record destructive data migration asked for as "write the migration" —
showed *no* early stopping either way. `codex exec` is non-interactive and the injected
step 4 ("Do not ask for confirmation. Just do it.") appears to cover it already. So treat
the two rules above as cheap insurance for genuinely long or multi-stage work, not as
something every codex prompt needs.

**Don't over-tighten boundaries.** If you inherited cautious phrasing from older models —
strong warnings, ask-first-always language — Astra takes it seriously and will stop where
you would have been happy for it to continue.

## `--agent antigravity`

**Ask for detail explicitly.** Gemini 3 answers directly and efficiently by default, which
here means a summary saying it finished without saying what it did. If you need specific
things reported — files touched, commands run, what was checked — list them, or the summary
will say it finished without saying what it did.

**Nudge reasoning in the prompt — it's your only effort dial.** agy bakes effort into the
model slug, so within a tier there is nothing to turn. An in-prompt "think carefully before
answering" is the one lever available, and Google documents it as effective at the cost of
extra thinking tokens. Use it for anything diagnostic.

**Structure helps here.** See the scaffolding note below.

**Watch the tier boundary.** `--effort high` is `claude-opus-4-6-thinking`. Prompt it as a
Claude worker.

## How much structure to use

Google recommends heavy scaffolding — explicit plan/execute/validate steps, worked
examples. OpenAI says elaborate recipes now hinder results. Both are right about their own
model, and the resolution is a rule rather than a contradiction:

**Scaffold inversely to model capability.** `gemini-3.8-flash-high` is the lightest model in
the roster and benefits from structure and an example. `gpt-6-astra` and `opus` are strong
enough that a detailed itinerary constrains them below what they'd do unprompted — for
those, state the goal, the definition of done, and the constraints, then get out of the way.

## Coverage note

No vendor document covers the default `sonnet` worker. Anthropic's Opus 5 guide describes
behaviors that *changed* from prior models and explicitly does not generalize backward, so
the claude section above is calibrated for `--effort high`. The shared rules apply to
`sonnet` with confidence; treat the claude-specific items as likely-but-unverified there.

## Worked examples

The same task, phrased for each backend. Task: find out why story generation is failing for
one art style.

**claude** (`--sandbox`, `--effort high`):

> Scene image generation fails intermittently for the watercolour art style only; other
> styles succeed. Find the cause.
>
> Report every candidate cause you find, with the evidence for each — do not pre-filter to
> the most likely one, I'll narrow it down. Stay within diagnosis: don't fix anything, and
> don't delegate to subagents. If you have to assume something about how the pipeline is
> configured, state the assumption.

*Why:* report-everything defeats the literal-conservatism problem, the scope line stops it
from shipping a fix you haven't reviewed, and the delegation cap keeps one agent as one agent.

**codex** (`--sandbox`):

> Scene image generation fails intermittently for the watercolour art style only. Find the
> cause and fix it.
>
> Done means: the cause is identified, the fix is applied, the relevant tests run, and they
> pass. The local tests use disposable fixtures and have no production access — run them,
> fix failures caused by your change, and rerun without asking for approval at each step.
> Do not stop after diagnosis to report back; there is no one to report to. Continue through
> to passing tests.

*Why:* every clause exists to defeat early stopping. Diagnosis is the natural stopping
point, so "done" is defined past it and the stop is forbidden by name.

**antigravity** (default tier):

> Scene image generation fails intermittently for the watercolour art style only; other
> styles succeed. Think carefully before answering, then find the cause.
>
> In your summary, report: the files you examined, what you found in each, the cause you
> landed on, and the evidence for it. Don't just state the conclusion.

*Why:* the reasoning nudge is the only effort control available, and the explicit reporting
list counteracts the terse default.
