"""Guards the delegation roster against model drift.

The bug this exists for: MODEL_TIERS pointed antigravity at "Gemini 3.5 Flash
(High)" — a version that never existed. Every standard-effort agy delegation was
passing a dead model string, and it survived a full skill audit *and* an eval
run because nothing ever compared the roster to reality.

Model names go stale on their own schedule, not ours. `agy models` and codex's
own models_cache.json are the sources of truth, so ask them.

These tests skip rather than fail when the tool is absent or offline — a laptop
without `agy` installed shouldn't break the suite. That means a green run is not
proof the roster was checked; read the skip reasons.

    python3 -m unittest discover -s .claude/skills/orchestration-skill/scripts/tests -v
"""

import json
import os
import shutil
import subprocess
import sys
import unittest

SCRIPTS_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, SCRIPTS_DIR)

from delegate_task import MODEL_TIERS, resolve_model  # noqa: E402

CODEX_MODELS_CACHE = os.path.expanduser("~/.codex/models_cache.json")


def agy_model_slugs():
    """Slugs `agy models` currently offers, or None if it can't be asked."""
    if not shutil.which("agy"):
        return None
    try:
        result = subprocess.run(["agy", "models"], capture_output=True, text=True, timeout=30)
    except (OSError, subprocess.SubprocessError):
        return None
    if result.returncode != 0:
        return None
    slugs = set()
    for line in result.stdout.splitlines():
        # "gemini-3.8-flash-high\tGemini 3.8 Flash (High)"
        head = line.split("\t")[0].strip()
        if head and " " not in head:
            slugs.add(head)
    return slugs or None


def codex_model_slugs():
    """Model slugs from codex's local cache, or None if unavailable."""
    if not os.path.exists(CODEX_MODELS_CACHE):
        return None
    try:
        with open(CODEX_MODELS_CACHE) as f:
            data = json.load(f)
    except (json.JSONDecodeError, IOError):
        return None

    slugs = set()

    def walk(node):
        if isinstance(node, dict):
            slug = node.get("slug")
            if isinstance(slug, str):
                slugs.add(slug)
            for value in node.values():
                walk(value)
        elif isinstance(node, list):
            for item in node:
                walk(item)

    walk(data)
    return slugs or None


class TestRosterShape(unittest.TestCase):
    """Structural checks — these never skip."""

    def test_every_agent_has_every_tier(self):
        for agent, tiers in MODEL_TIERS.items():
            self.assertEqual(set(tiers), {"standard", "high"}, agent)

    def test_every_entry_is_a_model_effort_pair(self):
        for agent, tiers in MODEL_TIERS.items():
            for tier, entry in tiers.items():
                model, reasoning = entry
                self.assertTrue(model, f"{agent}/{tier} has no model")
                if agent == "antigravity":
                    # agy bakes effort into the slug, so it has no separate dial.
                    self.assertIsNone(reasoning, f"{agent}/{tier}")
                else:
                    self.assertTrue(reasoning, f"{agent}/{tier} has no effort")

    def test_tiers_actually_differ(self):
        for agent, tiers in MODEL_TIERS.items():
            self.assertNotEqual(tiers["standard"], tiers["high"], agent)

    def test_unknown_agent_raises(self):
        with self.assertRaises(ValueError):
            resolve_model("gemini", "standard")


class TestModelsExist(unittest.TestCase):
    """The drift guard proper: is every configured model real?"""

    def test_antigravity_models_are_offered_by_agy(self):
        available = agy_model_slugs()
        if available is None:
            self.skipTest("`agy models` unavailable (not installed, or offline)")
        for tier, (model, _) in MODEL_TIERS["antigravity"].items():
            self.assertIn(
                model, available,
                f"antigravity/{tier} is set to '{model}', which `agy models` does not offer. "
                f"Available: {sorted(available)}",
            )

    def test_codex_model_is_in_the_local_cache(self):
        available = codex_model_slugs()
        if available is None:
            self.skipTest(f"codex model cache unavailable at {CODEX_MODELS_CACHE}")
        for tier, (model, _) in MODEL_TIERS["codex"].items():
            self.assertIn(
                model, available,
                f"codex/{tier} is set to '{model}', absent from codex's model cache. "
                f"Available: {sorted(available)}",
            )

    def test_claude_models_are_known_aliases(self):
        # claude has no machine-readable list, so pin to the aliases its --help
        # documents. A full pinned name (claude-opus-5) is allowed through.
        known = {"haiku", "sonnet", "opus", "fable"}
        for tier, (model, _) in MODEL_TIERS["claude"].items():
            self.assertTrue(
                model in known or model.startswith("claude-"),
                f"claude/{tier} is set to '{model}', not a known alias {sorted(known)} "
                "nor a full model name starting with 'claude-'",
            )


if __name__ == "__main__":
    unittest.main(verbosity=2)
