#!/bin/bash
echo $$ > /Users/dogankarakaya/LocalProjects/HeroKid/.claude/skills/orchestration-skill/logs/status/8a9c02b6.pid
gemini -p 'Independent Production Readiness Assessment - Fresh Eyes Review

Conduct a completely fresh, independent assessment of the HeroKid project as if you'"'"'re seeing it for the first time. No assumptions - validate everything.

## Assessment Focus:

### 1. User Experience Validation
- Walk through the complete user journey from signup to story creation
- Verify all user flows are complete and functional
- Check for broken links, missing pages, or dead ends
- Validate that features promised in PRD are actually implemented

### 2. Business Logic Validation
- Credit system: Can users buy credits and are they properly deducted?
- Story generation: Does the AI pipeline actually work?
- Avatar creation: Can users create and manage avatars?
- Payment processing: Is Stripe integration complete and secure?
- COPPA compliance: Are all privacy requirements met?

### 3. Technical Health
- Will the code compile and build?
- Are there any obvious bugs or errors?
- Is the database schema complete?
- Are environment variables properly documented?
- Is the deployment configuration ready?

### 4. Product Quality
- Is the MVP feature set complete?
- Are there any missing critical features?
- Is the user experience polished enough for launch?
- Are error messages helpful and user-friendly?

### 5. Launch Blockers
- What would prevent successful deployment?
- What would break on day 1?
- What critical issues exist?

## Deliverables:
Write your assessment to logs/results/<task_id>.summary.md with:
- VERDICT: READY TO LAUNCH / NOT READY / CONDITIONAL LAUNCH
- Confidence level in launch readiness (0-100%)
- Must-fix issues before launch
- Can-defer issues for post-launch
- Overall recommendation

Write detailed analysis to logs/results/<task_id>_report.md with:
- Complete user journey walkthroughs
- Feature completeness assessment
- Critical issues and blockers
- Risk assessment
- Go/No-Go recommendation with justification

IMPORTANT INSTRUCTIONS FOR HEADLESS EXECUTION:
1. Perform the requested task.
2. When finished, you MUST write a concise summary of your work to this EXISTING file: /Users/dogankarakaya/LocalProjects/HeroKid/.claude/skills/orchestration-skill/logs/results/8a9c02b6.summary.md
   IMPORTANT: Use your `write_file` tool to write the summary to {summary_file}. If that is not available, use `run_shell_command` with `echo`.
3. The summary file should be in Markdown format.
4. Do not ask for confirmation. Just do it.
5. You MUST also write a detailed report of your findings/actions to this EXISTING file: /Users/dogankarakaya/LocalProjects/HeroKid/.claude/skills/orchestration-skill/logs/results/8a9c02b6_report.md
5. DO NOT create any other files. You are ONLY allowed to write to the summary file (and report file if specified). Do NOT create files in the project root.
' --output-format json --yolo --model gemini-3-pro-preview > /Users/dogankarakaya/LocalProjects/HeroKid/.claude/skills/orchestration-skill/logs/raw/8a9c02b6.log 2>&1
python3 /Users/dogankarakaya/LocalProjects/HeroKid/.claude/skills/orchestration-skill/scripts/finish_task.py --task_id 8a9c02b6 --log_file /Users/dogankarakaya/LocalProjects/HeroKid/.claude/skills/orchestration-skill/logs/raw/8a9c02b6.log --status_file /Users/dogankarakaya/LocalProjects/HeroKid/.claude/skills/orchestration-skill/logs/status/8a9c02b6.status.json --summary_file /Users/dogankarakaya/LocalProjects/HeroKid/.claude/skills/orchestration-skill/logs/results/8a9c02b6.summary.md --agent gemini --pid_file /Users/dogankarakaya/LocalProjects/HeroKid/.claude/skills/orchestration-skill/logs/status/8a9c02b6.pid
