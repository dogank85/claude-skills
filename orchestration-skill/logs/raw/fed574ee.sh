#!/bin/bash
gemini -p "PRODUCTION READINESS: Environment & Configuration Audit

**Task: Ensure production deployment readiness**

1. **Review Current Environment Setup**
   - Check .env.example completeness
   - Verify docs/ENV_VARIABLES.md accuracy
   - Identify missing critical env vars

2. **Stripe Configuration Analysis**
   - Document what Stripe setup is needed
   - Test vs Production key strategy
   - Webhook endpoint configuration
   - Price ID setup for credit packs

3. **Resend Email Configuration**
   - What's needed for COPPA emails
   - Template requirements
   - From/To email setup

4. **Cron Secret Generation**
   - Best practices for CRON_SECRET
   - Rotation strategy

5. **Deployment Checklist**
   - What must be configured before launch
   - What can wait for post-launch
   - Security requirements (secrets management)
   - Monitoring/alerting setup needs

6. **Risk Assessment**
   - What breaks if we deploy now?
   - What's the minimum viable config?
   - What's the blast radius of missing config?

**Output:**
- Complete deployment checklist
- Required vs optional env vars
- Step-by-step production setup guide
- Risk assessment for current state

Write findings to summary file.

IMPORTANT INSTRUCTIONS FOR HEADLESS EXECUTION:
1. Perform the requested task.
2. When finished, you MUST write a concise summary of your work to this EXISTING file: /Users/dogankarakaya/LocalProjects/HeroKid/.claude/skills/orchestration-skill/logs/results/fed574ee.summary.md
   IMPORTANT: Use your `write_file` tool to write the summary to {summary_file}. If that is not available, use `run_shell_command` with `echo`.
3. The summary file should be in Markdown format.
4. Do not ask for confirmation. Just do it.
5. You MUST also write a detailed report of your findings/actions to this EXISTING file: /Users/dogankarakaya/LocalProjects/HeroKid/.claude/skills/orchestration-skill/logs/results/fed574ee_report.md
5. DO NOT create any other files. You are ONLY allowed to write to the summary file (and report file if specified). Do NOT create files in the project root.
" --output-format json --yolo --model gemini-3-pro-preview > /Users/dogankarakaya/LocalProjects/HeroKid/.claude/skills/orchestration-skill/logs/raw/fed574ee.log 2>&1
python3 /Users/dogankarakaya/LocalProjects/HeroKid/.claude/skills/orchestration-skill/scripts/finish_task.py --task_id fed574ee --log_file /Users/dogankarakaya/LocalProjects/HeroKid/.claude/skills/orchestration-skill/logs/raw/fed574ee.log --status_file /Users/dogankarakaya/LocalProjects/HeroKid/.claude/skills/orchestration-skill/logs/status/fed574ee.status.json --summary_file /Users/dogankarakaya/LocalProjects/HeroKid/.claude/skills/orchestration-skill/logs/results/fed574ee.summary.md --agent gemini
