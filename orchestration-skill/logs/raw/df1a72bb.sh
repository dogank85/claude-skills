#!/bin/bash
echo $$ > /Users/dogankarakaya/LocalProjects/HeroKid/.claude/skills/orchestration-skill/logs/status/df1a72bb.pid
gemini -p 'PHASE 1: Immediate Production Blockers - Make the project ready for testing

**Your Mission: Complete all Phase 1 critical tasks to unblock production deployment**

## Tasks:

### 1. Install Dependencies
- Run: `pnpm install` from project root
- If network/registry issues occur, document the error and try alternatives:
  - Check if there'"'"'s a package-lock or pnpm-lock that might help
  - Try clearing cache: `pnpm store prune`
  - Document what'"'"'s preventing installation
- Verify all workspaces install correctly
- Confirm vitest is available after install

### 2. Run All Tests
Once dependencies are installed:
- Run: `pnpm test` (full test suite)
- Run: `pnpm --filter @herokid/api test -- story-credit-gating.test.ts` (credit security tests)
- Run: `pnpm --filter @herokid/web test -- apps/web/app/api/cron/` (cron security tests)
- Document pass/fail results with details
- If tests fail, analyze WHY and document what needs fixing

### 3. Environment Variable Configuration
Create/update these critical files:

**A. Update .env.example** - Add ALL missing variables identified:
- NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY
- NANO_BANANA_API_KEY
- TEST_DATABASE_URL
- RESEND_API_KEY (critical for COPPA)
- TRANSACTIONAL_EMAIL_FROM
- Any others found missing

**B. Create .env.local.template** - Production-ready template with:
- STRIPE_WEBHOOK_SECRET=[REQUIRED - Generate in Stripe Dashboard]
- CRON_SECRET=[REQUIRED - Generate random 32-char string]
- RESEND_API_KEY=[REQUIRED - Get from Resend.com]
- Instructions for each secret

**C. Update docs/ENV_VARIABLES.md** - Document:
- Which vars are REQUIRED vs OPTIONAL
- Security implications of each
- How to generate/obtain each secret
- Production vs development differences

### 4. Fix Any Test Failures
If tests fail:
- Analyze the root cause
- Fix the code if it'"'"'s a real bug
- Update tests if they'"'"'re incorrect
- Re-run tests until they pass
- Document what was fixed

### 5. Validation Checklist
Create a checklist file: `PRE_DEPLOYMENT_CHECKLIST.md` with:
- [ ] Dependencies installed
- [ ] All tests passing
- [ ] Environment variables documented
- [ ] Security secrets identified
- [ ] Ready for Phase 2 (Stripe/Resend setup)

## Output Requirements:
- Test results summary (pass/fail counts, any failures detailed)
- List of files created/modified
- Any blocking issues that need human intervention
- Clear go/no-go for Phase 2

## Important:
- If you encounter errors, document them clearly
- Don'"'"'t skip failing tests - we need to know what'"'"'s broken
- Be thorough - this determines if we can deploy safely

Write comprehensive findings to summary file.

IMPORTANT INSTRUCTIONS FOR HEADLESS EXECUTION:
1. Perform the requested task.
2. When finished, you MUST write a concise summary of your work to this EXISTING file: /Users/dogankarakaya/LocalProjects/HeroKid/.claude/skills/orchestration-skill/logs/results/df1a72bb.summary.md
   IMPORTANT: Use your `write_file` tool to write the summary to {summary_file}. If that is not available, use `run_shell_command` with `echo`.
3. The summary file should be in Markdown format.
4. Do not ask for confirmation. Just do it.
5. You MUST also write a detailed report of your findings/actions to this EXISTING file: /Users/dogankarakaya/LocalProjects/HeroKid/.claude/skills/orchestration-skill/logs/results/df1a72bb_report.md
5. DO NOT create any other files. You are ONLY allowed to write to the summary file (and report file if specified). Do NOT create files in the project root.
' --output-format json --yolo --model gemini-3-pro-preview > /Users/dogankarakaya/LocalProjects/HeroKid/.claude/skills/orchestration-skill/logs/raw/df1a72bb.log 2>&1
python3 /Users/dogankarakaya/LocalProjects/HeroKid/.claude/skills/orchestration-skill/scripts/finish_task.py --task_id df1a72bb --log_file /Users/dogankarakaya/LocalProjects/HeroKid/.claude/skills/orchestration-skill/logs/raw/df1a72bb.log --status_file /Users/dogankarakaya/LocalProjects/HeroKid/.claude/skills/orchestration-skill/logs/status/df1a72bb.status.json --summary_file /Users/dogankarakaya/LocalProjects/HeroKid/.claude/skills/orchestration-skill/logs/results/df1a72bb.summary.md --agent gemini --pid_file /Users/dogankarakaya/LocalProjects/HeroKid/.claude/skills/orchestration-skill/logs/status/df1a72bb.pid
