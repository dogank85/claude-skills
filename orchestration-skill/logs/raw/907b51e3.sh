#!/bin/bash
echo $$ > /Users/dogankarakaya/LocalProjects/HeroKid/.claude/skills/orchestration-skill/logs/status/907b51e3.pid
codex exec 'Small Test Task: Verify Prisma Schema Consistency

Quick validation task to test the orchestration system.

## Task:
1. Read packages/database/prisma/schema.prisma
2. Verify that all models referenced in the API routers actually exist in the schema
3. Check for any orphaned models (defined in schema but never used)
4. Identify any missing indexes on frequently queried fields

## Deliverables:
Write a brief summary to logs/results/<task_id>.summary.md with:
- Total models in schema: X
- Models used in API: Y
- Orphaned models: Z (list them)
- Recommended indexes: (list 2-3 suggestions)

Keep it concise - this is just a quick validation.

IMPORTANT INSTRUCTIONS FOR HEADLESS EXECUTION:
1. Perform the requested task.
2. When finished, you MUST write a concise summary of your work to this EXISTING file: /Users/dogankarakaya/LocalProjects/HeroKid/.claude/skills/orchestration-skill/logs/results/907b51e3.summary.md
   IMPORTANT: Use your file editing capabilities to update this file.
3. The summary file should be in Markdown format.
4. Do not ask for confirmation. Just do it.
5. You MUST also write a detailed report of your findings/actions to this EXISTING file: /Users/dogankarakaya/LocalProjects/HeroKid/.claude/skills/orchestration-skill/logs/results/907b51e3_report.md
5. DO NOT create any other files. You are ONLY allowed to write to the summary file (and report file if specified). Do NOT create files in the project root.
' --json > /Users/dogankarakaya/LocalProjects/HeroKid/.claude/skills/orchestration-skill/logs/raw/907b51e3.log 2>&1
python3 /Users/dogankarakaya/LocalProjects/HeroKid/.claude/skills/orchestration-skill/scripts/finish_task.py --task_id 907b51e3 --log_file /Users/dogankarakaya/LocalProjects/HeroKid/.claude/skills/orchestration-skill/logs/raw/907b51e3.log --status_file /Users/dogankarakaya/LocalProjects/HeroKid/.claude/skills/orchestration-skill/logs/status/907b51e3.status.json --summary_file /Users/dogankarakaya/LocalProjects/HeroKid/.claude/skills/orchestration-skill/logs/results/907b51e3.summary.md --agent codex --pid_file /Users/dogankarakaya/LocalProjects/HeroKid/.claude/skills/orchestration-skill/logs/status/907b51e3.pid
