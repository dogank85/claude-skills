"""Unit tests for the orchestration command builder and icon-map parity.

Stdlib `unittest` only (the repo has no pytest). Run from the repo root:

    python3 -m unittest discover -s .claude/skills/orchestration-skill/scripts/tests -v

These tests pin the exact CLI command produced for each agent/effort/sandbox
combination so the Antigravity (`agy`) backend can be added without silently
changing how claude/codex are invoked (regression guards), and verify
that the new 🪐 icon was wired into BOTH notification surfaces.
"""

import os
import re
import sys
import unittest

SCRIPTS_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, SCRIPTS_DIR)

from delegate_task import build_agent_command, build_augmented_prompt  # noqa: E402

PROMPT = "/tmp/task.prompt.txt"


def build(agent, effort="standard", sandbox=False, parent=None, timeout=1800, model=None):
    return build_agent_command(
        agent=agent,
        effort=effort,
        sandbox=sandbox,
        prompt_file=PROMPT,
        parent_session_id=parent,
        timeout=timeout,
        model=model,
    )


class TestAntigravityCommand(unittest.TestCase):
    def test_standard_uses_flash_high(self):
        cmd = build("antigravity", effort="standard")
        self.assertIn("agy -p", cmd)
        self.assertIn('--model "gemini-3.8-flash-high"', cmd)
        self.assertIn("--add-dir", cmd)
        self.assertIn("--dangerously-skip-permissions", cmd)
        self.assertIn("--print-timeout 1800s", cmd)

    def test_high_uses_claude_opus(self):
        cmd = build("antigravity", effort="high")
        self.assertIn('--model "claude-opus-4-6-thinking"', cmd)

    def test_uses_slugs_not_display_names(self):
        # Display names ("Gemini 3.8 Flash (High)") fail silently on a near-miss;
        # slugs are checkable against `agy models`. See test_model_roster.py.
        for effort in ("standard", "high"):
            self.assertNotIn("(", build("antigravity", effort=effort).split("--model")[1][:40])

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
        self.assertIn("--model sonnet", cmd)
        self.assertIn("--effort medium", cmd)
        self.assertIn('--allowedTools "Read Edit Write Glob Grep"', cmd)

    def test_claude_high_and_sandbox(self):
        cmd = build("claude", effort="high", sandbox=True)
        self.assertIn("--model opus", cmd)
        self.assertIn("--effort medium", cmd)
        self.assertIn('--sandbox --allowedTools "Read Edit Write Glob Grep Bash"', cmd)

    def test_claude_resume(self):
        self.assertIn("--resume abc", build("claude", parent="abc"))

    def test_codex_standard(self):
        cmd = build("codex", effort="standard")
        self.assertIn("codex exec", cmd)
        self.assertIn("--json", cmd)
        self.assertIn("-m gpt-6-astra", cmd)
        self.assertIn('-c model_reasoning_effort="low"', cmd)

    def test_codex_high(self):
        cmd = build("codex", effort="high")
        self.assertIn("-m gpt-6-astra", cmd)
        self.assertIn('-c model_reasoning_effort="medium"', cmd)

    def test_codex_effort_is_always_explicit(self):
        # Omitting it inherits the user's interactive config.toml, which once made
        # `--effort high` a downgrade from an xhigh default. Never leave it unset.
        for effort in ("standard", "high"):
            self.assertIn("model_reasoning_effort=", build("codex", effort=effort))

    def test_high_tier_is_never_weaker_than_standard(self):
        # The guard for the inversion bug: the two tiers must actually differ,
        # and differ in the intended direction for each backend.
        self.assertNotEqual(build("claude", "standard"), build("claude", "high"))
        self.assertNotEqual(build("codex", "standard"), build("codex", "high"))
        self.assertNotEqual(build("antigravity", "standard"), build("antigravity", "high"))

    def test_codex_resume(self):
        self.assertIn("codex exec resume xyz", build("codex", parent="xyz"))

    def test_unknown_agent_raises(self):
        with self.assertRaises(ValueError):
            build("bogus")

    def test_gemini_backend_removed(self):
        # The Gemini backend was retired (Code Assist free tier deauthorized);
        # it must no longer resolve to a command.
        with self.assertRaises(ValueError):
            build("gemini")


class TestModelOverride(unittest.TestCase):
    """`--model` replaces the tier's model and keeps its reasoning effort. That
    is only safe because model and effort are independent flags on every backend
    — the old code faked effort by swapping models, so a model like `fable` was
    simply unreachable."""

    def test_claude_override_keeps_tier_effort(self):
        cmd = build("claude", effort="high", model="fable")
        self.assertIn("--model fable", cmd)
        self.assertNotIn("--model opus", cmd)
        self.assertIn("--effort medium", cmd)

    def test_codex_override_keeps_tier_effort(self):
        cmd = build("codex", effort="standard", model="gpt-5.6-luna")
        self.assertIn("-m gpt-5.6-luna", cmd)
        self.assertIn('model_reasoning_effort="low"', cmd)

    def test_antigravity_override(self):
        self.assertIn('--model "gemini-3.1-pro-high"',
                      build("antigravity", model="gemini-3.1-pro-high"))

    def test_no_override_uses_the_tier(self):
        self.assertIn("--model sonnet", build("claude", effort="standard"))


class TestAugmentedPrompt(unittest.TestCase):
    """The injected steps are read by an agent with no other context, so a
    repeated step number is a contradiction it has to guess its way past."""

    SUMMARY = "/tmp/t.summary.md"
    REPORT = "/tmp/t_report.md"

    def _steps(self, text):
        return [int(n) for n in re.findall(r'^(\d+)\.', text, flags=re.MULTILINE)]

    def test_steps_unique_and_sequential_without_report(self):
        prompt = build_augmented_prompt("Do X", "claude", self.SUMMARY)
        self.assertEqual(self._steps(prompt), [1, 2, 3, 4, 5])

    def test_steps_unique_and_sequential_with_report(self):
        prompt = build_augmented_prompt("Do X", "claude", self.SUMMARY, self.REPORT)
        self.assertEqual(self._steps(prompt), [1, 2, 3, 4, 5, 6])

    def test_report_path_only_present_when_requested(self):
        self.assertIn(self.REPORT, build_augmented_prompt("Do X", "claude", self.SUMMARY, self.REPORT))
        self.assertNotIn("_report.md", build_augmented_prompt("Do X", "claude", self.SUMMARY))

    def test_summary_path_and_user_prompt_always_present(self):
        for agent in ("claude", "codex", "antigravity"):
            prompt = build_augmented_prompt("Do X", agent, self.SUMMARY)
            self.assertIn(self.SUMMARY, prompt)
            self.assertTrue(prompt.startswith("Do X"))

    def test_agent_specific_write_hint(self):
        self.assertIn("`Edit` tool", build_augmented_prompt("x", "claude", self.SUMMARY))
        self.assertIn("file editing capabilities", build_augmented_prompt("x", "codex", self.SUMMARY))
        self.assertIn("file-editing tools", build_augmented_prompt("x", "antigravity", self.SUMMARY))


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
