"""Tests for cancel_task's process-tree termination.

The bug these guard against is severe: cancel_task used to call
`os.killpg(os.getpgid(pid), SIGTERM)`, but the delegation wrapper is launched
with a plain `nohup ... &` (no setsid), so it inherits the *orchestrator's*
process group — cancelling a task could SIGTERM the Claude Code session that
started it. The replacement walks the process tree explicitly and spares the
wrapper, so finish_task.py still runs.

Stdlib `unittest` only. Run from the repo root:

    python3 -m unittest discover -s .claude/skills/orchestration-skill/scripts/tests -v
"""

import os
import signal
import subprocess
import sys
import time
import unittest

SCRIPTS_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, SCRIPTS_DIR)

from cancel_task import collect_descendants, is_pid_alive, terminate_tree  # noqa: E402


def wait_until(predicate, timeout=5.0, interval=0.05):
    deadline = time.time() + timeout
    while time.time() < deadline:
        if predicate():
            return True
        time.sleep(interval)
    return predicate()


class TestProcessGroupHazardRemoved(unittest.TestCase):
    """Source guard, in the style of TestIconParity: the dangerous call must
    not come back, however the file is later refactored."""

    def test_no_killpg(self):
        with open(os.path.join(SCRIPTS_DIR, "cancel_task.py"), encoding="utf-8") as f:
            src = f.read()
        self.assertNotIn("killpg", src)
        self.assertNotIn("getpgid", src)


class TestCollectDescendants(unittest.TestCase):
    def setUp(self):
        # A two-level tree that mirrors the wrapper's shape: a bash parent whose
        # child sleeps. Nothing here touches the orchestrator's own group.
        self.parent = subprocess.Popen(
            ["bash", "-c", "sleep 30 & wait"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        self.addCleanup(self._cleanup)
        self.assertTrue(
            wait_until(lambda: len(collect_descendants(self.parent.pid)) >= 1),
            "child process never appeared",
        )

    def _cleanup(self):
        for pid in collect_descendants(self.parent.pid):
            try:
                os.kill(pid, signal.SIGKILL)
            except OSError:
                pass
        try:
            self.parent.kill()
        except OSError:
            pass
        self.parent.wait(timeout=5)

    def test_finds_the_sleeping_child(self):
        descendants = collect_descendants(self.parent.pid)
        self.assertGreaterEqual(len(descendants), 1)
        self.assertNotIn(self.parent.pid, descendants)

    def test_childless_pid_returns_empty(self):
        # A `sleep` spawns nothing, so it has no descendants.
        proc = subprocess.Popen(["sleep", "30"])
        self.addCleanup(proc.wait)
        self.addCleanup(proc.kill)
        self.assertEqual(collect_descendants(proc.pid), [])

    def test_terminate_tree_spares_the_wrapper(self):
        killed = terminate_tree(self.parent.pid)
        self.assertGreaterEqual(len(killed), 1)
        self.assertTrue(
            wait_until(lambda: all(not is_pid_alive(p) for p in killed)),
            "descendants survived SIGTERM",
        )
        # The wrapper itself must live long enough to run finish_task.py. It is
        # in `wait`, so it exits on its own once the child dies — the guarantee
        # under test is that terminate_tree did not signal it directly.
        self.assertNotIn(self.parent.pid, killed)


if __name__ == "__main__":
    unittest.main(verbosity=2)
