#!/bin/bash
codex exec "CRITICAL: Install Dependencies & Validate Security Fixes

**Task: Verify all security fixes work correctly**

1. **Install Dependencies**
   - Run: pnpm install (from root)
   - Verify all workspaces install correctly
   - Confirm vitest is available

2. **Run Security Fix Tests**
   - Run: pnpm --filter @herokid/api test -- story-credit-gating.test.ts
   - Run: pnpm --filter @herokid/web test -- apps/web/app/api/cron/
   - Document any test failures

3. **Verify Security Fixes**
   - Confirm Stripe webhook signature verification works
   - Confirm credit reservation is atomic
   - Confirm cron auth fails closed
   - Confirm COPPA emails are implemented

4. **Fix Any Test Failures**
   - If tests fail, fix them
   - Re-run tests until they pass

5. **Environment Variable Audit**
   - Check which env vars are REQUIRED but missing
   - List what needs to be configured for production
   - Verify .env.example is complete

**Output:**
- Test results (pass/fail counts)
- List of any issues found
- List of required env vars still missing
- Confirmation that security fixes are working

Write summary to task file.

IMPORTANT INSTRUCTIONS FOR HEADLESS EXECUTION:
1. Perform the requested task.
2. When finished, you MUST write a concise summary of your work to this EXISTING file: /Users/dogankarakaya/LocalProjects/HeroKid/.claude/skills/orchestration-skill/logs/results/4e5fc4fc.summary.md
   IMPORTANT: Use your file editing capabilities to update this file.
3. The summary file should be in Markdown format.
4. Do not ask for confirmation. Just do it.
5. You MUST also write a detailed report of your findings/actions to this EXISTING file: /Users/dogankarakaya/LocalProjects/HeroKid/.claude/skills/orchestration-skill/logs/results/4e5fc4fc_report.md
5. DO NOT create any other files. You are ONLY allowed to write to the summary file (and report file if specified). Do NOT create files in the project root.
" --json > /Users/dogankarakaya/LocalProjects/HeroKid/.claude/skills/orchestration-skill/logs/raw/4e5fc4fc.log 2>&1
python3 /Users/dogankarakaya/LocalProjects/HeroKid/.claude/skills/orchestration-skill/scripts/finish_task.py --task_id 4e5fc4fc --log_file /Users/dogankarakaya/LocalProjects/HeroKid/.claude/skills/orchestration-skill/logs/raw/4e5fc4fc.log --status_file /Users/dogankarakaya/LocalProjects/HeroKid/.claude/skills/orchestration-skill/logs/status/4e5fc4fc.status.json --summary_file /Users/dogankarakaya/LocalProjects/HeroKid/.claude/skills/orchestration-skill/logs/results/4e5fc4fc.summary.md --agent codex
