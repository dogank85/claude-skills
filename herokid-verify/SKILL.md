---
name: herokid-verify
description: How to prove a HeroKid change works before calling it done — which checks to run for each kind of change (server/API, web/admin, mobile, AI prompts, DB/schema, docs) and how to write the Evidence block the Definition of Done requires. Use this whenever you finish or are about to report on any HeroKid code change, before committing, before opening or marking a PR ready, when a builder/reviewer asks "is it verified?", or when asked to test, smoke-test, check, or verify a change — even if the word "verify" isn't used.
---

# HeroKid verify

HeroKid is live on iOS and Android with real families using it. A change is done when you can
**show** it works, not when the code looks right. This skill says what "show" means for each
kind of change, so every agent — builder, tester, reviewer — checks the same way and the
reviewer can trust the Evidence block instead of re-doing the work.

## Step 1: classify the change

Look at the diff (`git diff --stat` against the base). A change often touches several kinds —
run the checks for **each** kind it touches.

| Kind | Paths |
| --- | --- |
| Server / API | `packages/api/`, `packages/validators/`, `packages/shared/`, `packages/utils/`, `apps/web/app/api/` |
| Web / admin UI | `apps/web/` (pages, components) |
| Mobile | `apps/mobile/` |
| AI prompts / generation | `packages/ai/`, prompt text anywhere |
| DB / schema | `packages/database/prisma/` |
| Docs only | `*.md`, `docs/` — nothing executable |

## Step 2: run the cheap checks first

These are fast and catch most mistakes, so run them before anything slower. Scope them to the
packages you changed — the whole monorepo is slow and its unrelated failures are noise.

```bash
pnpm turbo run typecheck test --filter=<package>
pnpm --filter <package> lint        # for apps/web and apps/mobile (max-warnings=0)
```

Use `turbo` for typecheck and test, not plain `pnpm --filter <package> test`. Packages like
`@herokid/api` import other workspace packages (e.g. `@herokid/ai`) from their built `dist/`,
and turbo rebuilds those first (`^build`). Plain `pnpm --filter` skips that and tests against a
stale build — you'll get dozens of failures that have nothing to do with the change.

Package names: `@herokid/api`, `@herokid/web`, `@herokid/mobile`, `@herokid/ai`,
`@herokid/validators`, `@herokid/shared`, `@herokid/database`. If you changed a shared package
(`validators`, `shared`, `database`), also typecheck the packages that import it (`api`, `web`,
`mobile`) — a type change there breaks its consumers, not itself.

Run one package's suite at a time. Running the api and mobile suites in parallel overloads the
machine and causes timing failures that disappear on a clean re-run.

If a test fails, fix the cause. Per the Definition of Done: no added sleeps/retries, no
skipping or deleting tests to get green, and stop after 3 failed fix attempts and report.

If a failure looks unrelated to your change, prove it rather than assume it: show the failing
file isn't in your diff and the error has a separate cause (e.g. a local-only path, or the same
failure on the base commit). Report it under "Not caused by this change" — never just "pre-existing".

## Step 2b: check that CI actually ran

A green local run doesn't help if CI skipped the tests. For a PR: `gh pr checks <number>`; for
main: `gh run list --branch main --limit 3`, then `gh run view <id>` for the run that covers
your commit. If a job failed early and later jobs (typecheck, tests, build) were **skipped**,
say so in the Evidence — CI hasn't checked the change, so your local run is the only check.

## Step 3: the checks for each kind

### Server / API
- Cheap checks above for every changed package.
- If you changed behaviour, there should be a test that would have failed before your change.
  If none exists, add one next to the code (`*.test.ts`). Money and privacy paths especially:
  credits (charge, refund, idempotency), photo deletion, auth, consent.
- Read `## Code Review Rules` in `AGENTS.md` — if your change touches photos, credits, or mobile
  releases, say in the Evidence which rule applies and how you met it.

### Web / admin UI
- Cheap checks for `@herokid/web`.
- Visual check only if the owner's web dev server is already running (check
  `curl -s -o /dev/null -w '%{http_code}' http://localhost:3000`). If it is, open the changed page
  in the browser tool and take a screenshot. If it isn't, write "visual check not done — web
  dev server not running". **Never start a dev server yourself** — the owner runs it in their
  own terminal, and a background one fights theirs for the port.

### Mobile
- Cheap checks for `@herokid/mobile`, including the locale-parity test if you touched text
  (`apps/mobile/src/i18n/`). New text must be in all 8 locale files.
- Decide **OTA or rebuild** and say so in the Evidence: a change to native deps, the plugins list,
  `app.json`, `app.config.js`, `eas.json` or build-time env vars needs a full rebuild and a
  `runtimeVersion` bump; everything else can go by OTA. Getting this wrong crashes installed apps.
- Simulator check — **only if it is already running**. Never start Metro, Expo, or a simulator.
  1. Is Metro up? `curl -s http://localhost:8081/status` → should print `packager-status:running`.
  2. Is a simulator booted? `xcrun simctl list devices booted` → at least one device.
  3. If both: navigate with deep links (scheme `herokid://`, e.g. `xcrun simctl openurl booted
     herokid://diagnostics`) and take screenshots of each changed screen:
     `xcrun simctl io booted screenshot logs/verify/<short-name>.png`.
     Look at the screenshot yourself — a screenshot proves nothing if nobody checked it shows
     the change.
  4. If either is missing: write "sim check not done — Metro/simulator not running; hand to
     hk-tester or owner" and list the screens and steps they should check.
- Don't tap through flows that spend credits, generate AI images, or create real accounts —
  those cost money and touch production data. List them for the owner instead.

### AI prompts / generation
- Cheap checks for `@herokid/ai` (and `@herokid/api` if the call site changed).
- Live prompt files are high-risk: they change what every child sees. Don't edit them unless the
  task explicitly says so.
- A real generation costs money and needs the owner's OK. Don't run one by default — instead
  describe in the Evidence what a test generation should check (age group, language, safety),
  and say "real generation not run — needs owner OK". If the owner already OK'd one call, run
  exactly one (the Story/Avatar Labs are the place for this) and include the output.

### DB / schema
- `pnpm --filter @herokid/database db:generate`, then typecheck `api` and `web`.
- If you added a migration under `packages/database/prisma/migrations/`, say so loudly in the
  Evidence: it must be applied to the production DB after the Vercel deploy and before endpoint
  checks. Never run it against production yourself.

### Docs only
- Nothing to run. Check that any file paths, commands, or names you wrote actually exist.
- Evidence: `docs only — no executable change`.

## Step 4: write the Evidence block

End your report with this. Show real output (the summary line of each command is enough), not
"tests pass" from memory — the reviewer reads this instead of re-running everything, so it
has to be true and specific.

```
Evidence:
- Change kinds: server/API, mobile
- Ran: pnpm turbo run typecheck test --filter=@herokid/api → 0 errors; 412 passed, 0 failed
- Ran: pnpm --filter @herokid/mobile test -- locale-parity → 1 suite passed
- CI: PR #270 checks → all green (typecheck, unit tests, build ran)
- Sim check: done — screenshots logs/verify/create-tab.png, logs/verify/credits-popup.png (both show the new button)
- Release: OTA (JS-only, no native/config change)
- Code Review Rules: credits — retry with same idempotencyKey covered by new test story-idempotency.test.ts
- Not done: real story generation (needs owner OK)
```

If something couldn't be checked, say what and why in "Not done". An honest "not done" is
useful; a vague "verified" is what this whole skill exists to prevent.
