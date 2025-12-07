#!/bin/bash
claude -p "Say hello and sleep for 5 seconds

IMPORTANT INSTRUCTIONS FOR HEADLESS EXECUTION:
1. Perform the requested task.
2. When finished, you MUST write a concise summary of your work to this EXISTING file: /Users/dogankarakaya/LocalProjects/HeroKid/.claude/skills/orchestration-skill/logs/results/test_task_07.summary.md
   IMPORTANT: Use the `Edit` tool (or `bash` with `echo`) to write to it. The `Write` tool might fail if it tries to read first.
3. The summary file should be in Markdown format.
4. Do not ask for confirmation. Just do it.
" --output-format json > /Users/dogankarakaya/LocalProjects/HeroKid/.claude/skills/orchestration-skill/logs/raw/test_task_07.log 2>&1
python3 scripts/finish_task.py --task_id test_task_07 --log_file /Users/dogankarakaya/LocalProjects/HeroKid/.claude/skills/orchestration-skill/logs/raw/test_task_07.log --status_file /Users/dogankarakaya/LocalProjects/HeroKid/.claude/skills/orchestration-skill/logs/status/test_task_07.status.json --summary_file /Users/dogankarakaya/LocalProjects/HeroKid/.claude/skills/orchestration-skill/logs/results/test_task_07.summary.md --agent claude
