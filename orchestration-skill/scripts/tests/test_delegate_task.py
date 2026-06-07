"""Unit tests for the orchestration command builder and icon-map parity.

Stdlib `unittest` only (the repo has no pytest). Run from the repo root:

    python3 -m unittest discover -s .claude/skills/orchestration-skill/scripts/tests -v

These tests pin the exact CLI command produced for each agent/effort/sandbox
combination so the Antigravity (`agy`) backend can be added without silently
changing how claude/gemini/codex are invoked (regression guards), and verify
that the new 🪐 icon was wired into BOTH notification surfaces.
"""

import os
import sys
import unittest

SCRIPTS_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, SCRIPTS_DIR)

from delegate_task import build_agent_command  # noqa: E402

PROMPT = "/tmp/task.prompt.txt"


def build(agent, effort="standard", sandbox=False, parent=None, timeout=1800):
    return build_agent_command(
        agent=agent,
        effort=effort,
        sandbox=sandbox,
        prompt_file=PROMPT,
        parent_session_id=parent,
        timeout=timeout,
    )


class TestAntigravityCommand(unittest.TestCase):
    def test_standard_uses_flash_high(self):
        cmd = build("antigravity", effort="standard")
        self.assertIn("agy -p", cmd)
        self.assertIn('--model "Gemini 3.5 Flash (High)"', cmd)
        self.assertIn("--add-dir", cmd)
        self.assertIn("--dangerously-skip-permissions", cmd)
        self.assertIn("--print-timeout 1800s", cmd)

    def test_high_uses_claude_opus(self):
        cmd = build("antigravity", effort="high")
        self.assertIn('--model "Claude Opus 4.6 (Thinking)"', cmd)

    def test_print_timeout_tracks_timeout_arg(self):
        # agy's own 5-min default must be raised to match the watchdog.
        cmd = build("antigravity", timeout=3600)
        self.assertIn("--print-timeout 3600s", cmd)

    def test_sandbox_flag(self):
        self.assertIn(" --sandbox", build("antigravity", sandbox=True))
        self.assertNotIn(" --sandbox", build("antigravity", sandbox=False))

    def test_no_json_output_mode(self):
        # agy has no --output-format json; emitting it would error.
        self.assertNotIn("--output-format", build("antigravity"))

    def test_resume_is_never_emitted(self):
        # Even if a parent slips through, the antigravity branch must not add a
        # resume flag — agy can't resume by session id.
        cmd = build("antigravity", parent="sess-123")
        self.assertNotIn("--resume", cmd)
        self.assertNotIn("--conversation", cmd)
        self.assertNotIn("sess-123", cmd)


class TestRegressionGuards(unittest.TestCase):
    """The refactor must not change how the existing three agents are invoked."""

    def test_claude_standard(self):
        cmd = build("claude", effort="standard")
        self.assertIn("claude -p", cmd)
        self.assertIn("--output-format json", cmd)
        self.assertIn("--model haiku", cmd)
        self.assertIn('--allowedTools "Read Edit Write Glob Grep"', cmd)

    def test_claude_high_and_sandbox(self):
        cmd = build("claude", effort="high", sandbox=True)
        self.assertIn("--model sonnet", cmd)
        self.assertIn('--sandbox --allowedTools "Read Edit Write Glob Grep Bash"', cmd)

    def test_claude_resume(self):
        self.assertIn("--resume abc", build("claude", parent="abc"))

    def test_gemini_standard(self):
        cmd = build("gemini", effort="standard")
        self.assertIn("gemini -p", cmd)
        self.assertIn("--yolo", cmd)
        self.assertIn("--model gemini-3-flash-preview", cmd)

    def test_gemini_high(self):
        self.assertIn("--model gemini-3.1-pro-preview", build("gemini", effort="high"))

    def test_codex_standard(self):
        cmd = build("codex", effort="standard")
        self.assertIn("codex exec", cmd)
        self.assertIn("--json", cmd)
        self.assertNotIn('model_reasoning_effort="high"', cmd)

    def test_codex_high(self):
        self.assertIn('-c model_reasoning_effort="high"', build("codex", effort="high"))

    def test_codex_resume(self):
        self.assertIn("codex exec resume xyz", build("codex", parent="xyz"))

    def test_unknown_agent_raises(self):
        with self.assertRaises(ValueError):
            build("bogus")


class TestIconParity(unittest.TestCase):
    """🪐 must be wired into both notification surfaces, or antigravity tasks
    silently inherit the codex fallback / hourglass."""

    def _read(self, name):
        with open(os.path.join(SCRIPTS_DIR, name), encoding="utf-8") as f:
            return f.read()

    def test_finish_task_has_planet_icon(self):
        src = self._read("finish_task.py")
        self.assertIn('"antigravity"', src)
        self.assertIn("🪐", src)

    def test_status_vis_has_planet_icon(self):
        src = self._read("status_vis.py")
        self.assertIn('"antigravity": "🪐"', src)


if __name__ == "__main__":
    unittest.main(verbosity=2)
