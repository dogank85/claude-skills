#!/bin/bash
echo $$ > /Users/dogankarakaya/LocalProjects/HeroKid/.claude/skills/orchestration-skill/logs/status/d42ae117.pid
codex exec 'CRITICAL: Fix All Production Blockers

Based on the QA audit consensus (tasks 18d133c1 and d1dcd4c2), fix all 4 verified production blockers immediately.

## BLOCKER 1: Story Generation Pipeline (CRITICAL)
**Files to fix:**
- packages/api/src/lib/generateStoryAsync.ts
- packages/api/src/routers/story.ts

**Required fixes:**
1. Change import from `env` to `apiEnv`:
   ```typescript
   // BEFORE: import { env } from '"'"'../env'"'"';
   // AFTER: import { apiEnv } from '"'"'../env'"'"';
   ```
2. Update all references from `env.PROPERTY` to `apiEnv.PROPERTY`
3. Fix field name mismatch: persist to `storyContent` instead of `content`
4. Add/import missing function `verifyChildProfileOwnership` or remove references
5. Ensure Supabase client uses correct env vars (SUPABASE_SERVICE_ROLE_KEY)

## BLOCKER 2: Web Dashboard Authentication (CRITICAL)
**Files to fix:**
- apps/web/app/providers.tsx
- packages/api/src/context.ts (or client setup)

**Required fixes:**
1. Configure tRPC client to send Supabase auth tokens in headers
2. Option A: Read Supabase session from cookies and inject into Authorization header
3. Option B: Update context.ts to read cookies directly
4. Ensure protected tRPC calls (auth.me, credits, stories) work from web dashboard
5. Test that logged-in state propagates correctly

## BLOCKER 3: PDF Export Route (CRITICAL)
**Files to fix:**
- apps/web/app/api/generate-pdf/route.tsx

**Required fixes:**
1. Fix import: Change `db` to `prisma`:
   ```typescript
   // BEFORE: import { db } from '"'"'@herokid/database'"'"';
   // AFTER: import { prisma } from '"'"'@herokid/database'"'"';
   ```
2. Update all `db.` references to `prisma.`
3. Fix env var: Change `SUPABASE_SERVICE_KEY` to `SUPABASE_SERVICE_ROLE_KEY`
4. Add authentication check (ensure only story owner can export)

## BLOCKER 4: Payment Verification (HIGH PRIORITY)
**Files to fix:**
- packages/api/src/routers/credits.ts
- apps/mobile/app/credits/purchase.tsx (if needed)

**Required fixes:**
1. Remove or lock down mock `purchaseCredits` endpoint
2. Ensure Stripe checkout flow is the ONLY way to purchase credits
3. Complete Apple/Google IAP verification (remove security warnings)
4. Update mobile UI to use real payment flow instead of "Payment Integration Required" alert
5. Add tests for payment verification

## Deliverables:
Write summary to logs/results/<task_id>.summary.md with:
- List of files modified
- Verification that each blocker is fixed
- Any remaining issues or follow-up work

Write detailed changes to logs/results/<task_id>_report.md with:
- Code changes made for each blocker
- Testing steps performed
- Verification of fixes

IMPORTANT: Test each fix to ensure it actually works. Run relevant tests if available.

IMPORTANT INSTRUCTIONS FOR HEADLESS EXECUTION:
1. Perform the requested task.
2. When finished, you MUST write a concise summary of your work to this EXISTING file: /Users/dogankarakaya/LocalProjects/HeroKid/.claude/skills/orchestration-skill/logs/results/d42ae117.summary.md
   IMPORTANT: Use your file editing capabilities to update this file.
3. The summary file should be in Markdown format.
4. Do not ask for confirmation. Just do it.
5. You MUST also write a detailed report of your findings/actions to this EXISTING file: /Users/dogankarakaya/LocalProjects/HeroKid/.claude/skills/orchestration-skill/logs/results/d42ae117_report.md
5. DO NOT create any other files. You are ONLY allowed to write to the summary file (and report file if specified). Do NOT create files in the project root.
' --json -c model_reasoning_effort="high" > /Users/dogankarakaya/LocalProjects/HeroKid/.claude/skills/orchestration-skill/logs/raw/d42ae117.log 2>&1
python3 /Users/dogankarakaya/LocalProjects/HeroKid/.claude/skills/orchestration-skill/scripts/finish_task.py --task_id d42ae117 --log_file /Users/dogankarakaya/LocalProjects/HeroKid/.claude/skills/orchestration-skill/logs/raw/d42ae117.log --status_file /Users/dogankarakaya/LocalProjects/HeroKid/.claude/skills/orchestration-skill/logs/status/d42ae117.status.json --summary_file /Users/dogankarakaya/LocalProjects/HeroKid/.claude/skills/orchestration-skill/logs/results/d42ae117.summary.md --agent codex --pid_file /Users/dogankarakaya/LocalProjects/HeroKid/.claude/skills/orchestration-skill/logs/status/d42ae117.pid
