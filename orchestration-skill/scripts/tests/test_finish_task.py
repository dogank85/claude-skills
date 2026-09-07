"""Tests for finish_task's status labelling and notification fields.

Two bugs are guarded here:

1. `icon`/`agent_display`/`preview` used to be bound inside the macOS-notification
   `try`, while the ntfy and channel pushes read them afterwards — one osascript
   failure silently took out both notifications the user actually sees.
2. A cancelled task exits 143, the same code a watchdog timeout produces, so it
   would have been relabelled FAILED. cancel_task.py writes CANCELLED first and
   finish_task must honour it.

Stdlib `unittest` only. Run from the repo root:

    python3 -m unittest discover -s .claude/skills/orchestration-skill/scripts/tests -v
"""

import json
import os
import subprocess
import sys
import tempfile
import unittest

SCRIPTS_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, SCRIPTS_DIR)

from finish_task import notification_fields  # noqa: E402

FINISH_TASK = os.path.join(SCRIPTS_DIR, "finish_task.py")


class TestNotificationFields(unittest.TestCase):
    def test_each_agent_gets_its_icon_and_sound(self):
        expected = {"claude": ("🤖", "Tink"), "codex": ("🔶", "Glass"), "antigravity": ("🪐", "Submarine")}
        for agent, (icon, sound) in expected.items():
            got_icon, got_sound, display, title, preview = notification_fields(agent, "t1", 0, "# Done\nbody")
            self.assertEqual((got_icon, got_sound), (icon, sound), agent)
            self.assertEqual(display, agent.capitalize())
            self.assertIn("t1", title)
            self.assertTrue(preview)

    def test_unknown_agent_falls_back(self):
        icon, sound, display, title, preview = notification_fields("mystery", "t1", 0, "")
        self.assertEqual((icon, sound), ("🔶", "Pop"))
        self.assertEqual(preview, "Task finished successfully.")

    def test_status_word_tracks_exit_code(self):
        self.assertIn("Complete", notification_fields("claude", "t1", 0, "")[3])
        self.assertIn("Failed", notification_fields("claude", "t1", 1, "")[3])

    def test_preview_is_first_line_and_capped(self):
        self.assertEqual(notification_fields("claude", "t1", 0, "first\nsecond")[4], "first")
        long_preview = notification_fields("claude", "t1", 0, "x" * 300)[4]
        self.assertEqual(len(long_preview), 100)
        self.assertTrue(long_preview.endswith("..."))

    def test_all_fields_populated_without_a_summary(self):
        # Steps 5 and 6 read every one of these; none may be empty or unbound.
        for field in notification_fields("claude", "t1", 143, ""):
            self.assertTrue(field)


class TestStatusLabelling(unittest.TestCase):
    def _run(self, on_disk_status, exit_code):
        with tempfile.TemporaryDirectory() as tmp:
            status_file = os.path.join(tmp, "t1.status.json")
            log_file = os.path.join(tmp, "t1.log")
            summary_file = os.path.join(tmp, "t1.summary.md")
            with open(status_file, 'w') as f:
                json.dump({"task_id": "t1", "status": on_disk_status, "agent": "claude"}, f)
            with open(log_file, 'w') as f:
                f.write('{"session_id":"sess-abc","result":"ok"}\n')
            open(summary_file, 'w').close()

            subprocess.run(
                [sys.executable, FINISH_TASK,
                 "--task_id", "t1", "--log_file", log_file,
                 "--status_file", status_file, "--summary_file", summary_file,
                 "--agent", "claude", "--exit_code", str(exit_code), "--timeout", "1800"],
                capture_output=True, timeout=60, cwd=tmp,
            )
            with open(status_file) as f:
                status = json.load(f)
            with open(summary_file) as f:
                summary = f.read()
            return status, summary

    def test_cancelled_survives_the_143_exit(self):
        status, _ = self._run("CANCELLED", 143)
        self.assertEqual(status["status"], "CANCELLED")

    def test_running_plus_143_is_a_timeout_failure(self):
        status, _ = self._run("RUNNING", 143)
        self.assertEqual(status["status"], "FAILED")
        self.assertIn("timeout", status["error"])

    def test_clean_exit_completes(self):
        status, _ = self._run("RUNNING", 0)
        self.assertEqual(status["status"], "COMPLETED")

    def test_session_id_recorded_even_when_cancelled(self):
        status, _ = self._run("CANCELLED", 143)
        self.assertEqual(status["session_id"], "sess-abc")

    def test_empty_summary_gets_the_log_fallback(self):
        _, summary = self._run("CANCELLED", 143)
        self.assertIn("Agent failed to write summary", summary)


if __name__ == "__main__":
    unittest.main(verbosity=2)
