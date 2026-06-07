---
description: Generate a structured conversation summary for AI agent handoff and context preservation
---

# CONVERSATION SUMMARY FOR AI AGENT HANDOFF

## PURPOSE
Generate a structured progress report that enables seamless context preservation across AI agent workflows. This summary will be shared with future AI agents to maintain project continuity, avoid redundant work, and enable immediate productive collaboration.

## OUTPUT REQUIREMENTS
- Use clear markdown formatting with proper headings and bullet points
- Be concise but complete - include only actionable and decision-relevant information
- Focus on what future agents NEED to know, not exhaustive transcripts
- Include specific file paths, command examples, and technical details where relevant

---

## YOUR TASK

Analyze our entire conversation and generate the following structured summary:

## 1. THE INITIAL GOAL

**Primary Problem:**
- What was the main issue, challenge, or question we were addressing?

**Objective:**
- What specific outcome were we trying to achieve?

**Context & Constraints:**
- Important background information that shaped our approach
- Any limitations, requirements, or dependencies
- Relevant project/codebase context

---

## 2. WHAT HAS BEEN ACHIEVED

### Completed Actions
- [Concrete steps taken, implementations completed]
- [Files created/modified with paths: `path/to/file.ext`]
- [Commands executed, configurations applied]

### Key Decisions Made
- [Important choices and rationale behind them]
- [Approaches selected and why alternatives were rejected]
- [Trade-offs decided and their implications]

### Solutions Implemented
- [Working solutions with technical details]
- [Fixes applied and problems resolved]
- [Systems/workflows established]

### Knowledge Gained
- [Important discoveries about the codebase/problem domain]
- [Insights that inform future work]
- [Lessons learned or "gotchas" to avoid]

### Technical Changes
- [Modified files: `path/to/file.ext:line_number`]
- [New dependencies or tools introduced]
- [Configuration changes]

---

## 3. WHAT CAN BE ACHIEVED NEXT

### Immediate Next Steps (Ready to Execute)
- [Clear, actionable tasks that can be started immediately]
- [Specific commands to run or files to modify]

### Future Possibilities
- [Longer-term opportunities for improvement]
- [Feature enhancements or optimizations to consider]
- [Refactoring or architectural changes worth exploring]

### Known Blockers & Dependencies
- [Obstacles that need resolution before proceeding]
- [External dependencies or waiting on decisions]
- [Technical limitations or missing information]

### Critical Context for Future Agents
- [Specific warnings or gotchas to be aware of]
- [Important patterns or conventions to follow]
- [Things that were tried but didn't work (to avoid repetition)]
- [Any ongoing concerns or monitoring needed]

---

## HANDOFF METADATA
- **Session Date:** [today's date]
- **Primary Agent:** Claude Code
- **Project/Codebase:** [current project name]
- **Working Directory:** [current working directory]
- **Key Files Modified:** [Count and list primary files from conversation]

---

**FORMAT INSTRUCTIONS:**
- Use markdown formatting throughout
- Keep bullet points concise but informative
- Include code snippets or command examples where helpful
- Prioritize actionable information over narrative
- This summary should enable another AI agent to continue work immediately without re-discovering context
