#!/bin/bash
echo $$ > /Users/dogankarakaya/LocalProjects/HeroKid/.claude/skills/orchestration-skill/logs/status/f667de1d.pid
codex exec 'CRITICAL: Fix All Production Blockers - Round 2

Based on independent assessments from both agents (tasks 8b284fb8 and 8a9c02b6), fix all critical blockers preventing production launch.

## COMBINED CRITICAL ISSUES TO FIX:

### 1. Missing Google Cloud Environment Variables (CRITICAL)
**Files to fix:**
- .env.example
- packages/ai/src/imagen/client.ts
- packages/ai/src/gemini/client.ts

**Required fixes:**
- Add GOOGLE_CLOUD_PROJECT to .env.example
- Add GOOGLE_APPLICATION_CREDENTIALS or service account JSON to env
- Add graceful error handling when env vars missing (don'"'"'t crash on import)
- Document all required Google/Vertex AI credentials

### 2. Safety Score Hardcoded (CRITICAL - COPPA RISK!)
**File:** packages/api/src/lib/generateStoryAsync.ts

**Required fix:**
- Remove hardcoded `safetyScore: 1.0`
- Use actual safety score from Nano Banana API response
- Ensure safety filtering is active and working
- Add validation that safety score is properly set

### 3. Broken Test Files (HIGH - Blocks CI/CD)
**Files:**
- packages/api/src/routers/library.test.ts
- packages/api/src/routers/story.integration.test.ts

**Required fixes:**
- Fix 35 TypeScript compilation errors
- Fix syntax errors and duplicate imports
- Ensure tests can compile and run

### 4. Mobile IAP Incomplete
**File:** apps/mobile/src/screens/PurchaseScreen.tsx

**Required fix:**
- Review TODO comments about react-native-iap
- Verify if mobile purchase flow is complete
- Wire up any missing IAP logic
- If incomplete, document what'"'"'s needed

### 5. Environment Documentation
**Files to update:**
- .env.example
- docs/ENV_VARIABLES.md

**Add missing:**
- GOOGLE_CLOUD_PROJECT
- Google service account credentials
- Vertex AI configuration
- Supabase storage bucket names
- Any other missing critical env vars

### 6. Validate Supabase Storage Configuration
**Required:**
- Document required Supabase buckets (stories, temp-uploads, pdfs)
- Add bucket name env vars to .env.example
- Add validation/error handling when buckets don'"'"'t exist

## Deliverables:
Write summary to logs/results/<task_id>.summary.md with:
- List of all issues fixed
- Verification that critical blockers resolved
- Any remaining issues that need manual intervention (like actual API keys)

Write detailed report to logs/results/<task_id>_report.md with:
- Code changes for each fix
- Validation steps performed
- What still needs manual configuration

IMPORTANT: Focus on CODE fixes. Don'"'"'t worry about actual API keys - just ensure placeholders are documented and code handles missing keys gracefully.

IMPORTANT INSTRUCTIONS FOR HEADLESS EXECUTION:
1. Perform the requested task.
2. When finished, you MUST write a concise summary of your work to this EXISTING file: /Users/dogankarakaya/LocalProjects/HeroKid/.claude/skills/orchestration-skill/logs/results/f667de1d.summary.md
   IMPORTANT: Use your file editing capabilities to update this file.
3. The summary file should be in Markdown format.
4. Do not ask for confirmation. Just do it.
5. You MUST also write a detailed report of your findings/actions to this EXISTING file: /Users/dogankarakaya/LocalProjects/HeroKid/.claude/skills/orchestration-skill/logs/results/f667de1d_report.md
5. DO NOT create any other files. You are ONLY allowed to write to the summary file (and report file if specified). Do NOT create files in the project root.
' --json > /Users/dogankarakaya/LocalProjects/HeroKid/.claude/skills/orchestration-skill/logs/raw/f667de1d.log 2>&1
python3 /Users/dogankarakaya/LocalProjects/HeroKid/.claude/skills/orchestration-skill/scripts/finish_task.py --task_id f667de1d --log_file /Users/dogankarakaya/LocalProjects/HeroKid/.claude/skills/orchestration-skill/logs/raw/f667de1d.log --status_file /Users/dogankarakaya/LocalProjects/HeroKid/.claude/skills/orchestration-skill/logs/status/f667de1d.status.json --summary_file /Users/dogankarakaya/LocalProjects/HeroKid/.claude/skills/orchestration-skill/logs/results/f667de1d.summary.md --agent codex --pid_file /Users/dogankarakaya/LocalProjects/HeroKid/.claude/skills/orchestration-skill/logs/status/f667de1d.pid
