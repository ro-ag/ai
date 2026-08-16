"""Tests for memento.py — run: uv run pytest skills/memento/"""

import io
import os
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from memento import memento


class MementoTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        base = Path(self.tmp.name)
        self.home = base / "home"
        self.ai = base / "ai"
        self.proj = base / "proj"
        (self.proj / ".git").mkdir(parents=True)
        self.ai.mkdir()
        (self.ai / "AGENTS.md").write_text("# Agent rules\n\n## Hard rules\n\n- existing rule\n")
        (self.ai / "CLAUDE.md").write_text("# Claude rules\n")
        os.environ["MEMENTO_HOME"] = str(self.home)
        os.environ["MEMENTO_AI_DIR"] = str(self.ai)

    def tearDown(self):
        self.tmp.cleanup()
        for k in ("MEMENTO_HOME", "MEMENTO_AI_DIR"):
            os.environ.pop(k, None)

    def run_cmd(self, *argv):
        out = io.StringIO()
        with redirect_stdout(out):
            memento.main([*argv, "--project", str(self.proj)])
        return out.getvalue()

    def test_hit_creates_bumps_and_roundtrips(self):
        self.run_cmd("hit", "uv-not-python", "--rule", "Use uv run, never bare python",
                     "--fix", "uv run main.py", "--scope", "project", "--kind", "habit")
        self.run_cmd("hit", "uv-not-python")
        entries = memento.parse(self.proj / "MEMENTO.md")
        e = entries["uv-not-python"]
        self.assertEqual(len(e["hits"]), 2)
        self.assertEqual(e["rule"], "Use uv run, never bare python")
        self.assertEqual(e["fix"], "uv run main.py")
        self.assertEqual(e["kind"], "habit")
        self.assertEqual(e["status"], "watching")

    def test_promote_alert_on_third_hit(self):
        self.run_cmd("hit", "s", "--rule", "r", "--scope", "project")
        self.assertNotIn("PROMOTE", self.run_cmd("hit", "s"))
        self.assertIn("PROMOTE", self.run_cmd("hit", "s"))

    def test_cost_trigger_alerts_immediately(self):
        out = self.run_cmd("hit", "ssl-trick", "--rule", "r", "--scope", "global", "--cost", "45")
        self.assertIn("PROMOTE", out)

    def test_promote_global_writes_both_docs_idempotently(self):
        self.run_cmd("hit", "g", "--rule", "Global rule text", "--scope", "global")
        out = self.run_cmd("promote", "g")
        self.assertIn("rule added to", out)
        for doc in ("AGENTS.md", "CLAUDE.md"):
            text = (self.ai / doc).read_text()
            self.assertIn("- Global rule text (memento: g)", text)
            self.assertIn(memento.SECTION, text)
        self.assertIn("- existing rule", (self.ai / "AGENTS.md").read_text())
        self.assertIn("already in", self.run_cmd("promote", "g"))
        self.assertEqual((self.ai / "AGENTS.md").read_text().count("(memento: g)"), 1)
        e = memento.parse(memento.global_ledger())["g"]
        self.assertTrue(e["status"].startswith("enforced ->"))

    def test_promote_project_creates_agents_md(self):
        self.run_cmd("hit", "p", "--rule", "Project rule", "--scope", "project")
        self.run_cmd("promote", "p")
        self.assertIn("- Project rule (memento: p)", (self.proj / "AGENTS.md").read_text())

    def test_similar_slug_warning(self):
        self.run_cmd("hit", "uv-not-python", "--rule", "r", "--scope", "project")
        out = self.run_cmd("hit", "python-venv", "--rule", "r2", "--scope", "project")
        self.assertIn("similar existing slugs", out)
        self.assertIn("uv-not-python", out)

    def test_check_sections(self):
        self.run_cmd("hit", "a", "--rule", "Rule A", "--scope", "project")
        self.run_cmd("hit", "b", "--rule", "Rule B", "--scope", "global")
        self.run_cmd("promote", "b")
        out = self.run_cmd("check")
        self.assertIn("ENFORCED", out)
        self.assertIn("Rule B", out)
        self.assertIn("WATCHING", out)
        self.assertIn("Rule A (hits: 1)", out)

    def test_top_ranks_by_hits(self):
        self.run_cmd("hit", "often", "--rule", "r", "--scope", "project")
        self.run_cmd("hit", "often")
        self.run_cmd("hit", "rare", "--rule", "r", "--scope", "project")
        out = self.run_cmd("top")
        self.assertLess(out.index("often"), out.index("rare"))

    def test_ai_dir_falls_back_to_config_then_ledger_dir(self):
        import json
        os.environ.pop("MEMENTO_AI_DIR")
        self.assertEqual(memento.ai_dir(), self.home)
        self.home.mkdir(parents=True, exist_ok=True)
        (self.home / "config.json").write_text(json.dumps({"rules_dir": str(self.ai)}))
        self.assertEqual(memento.ai_dir(), self.ai)
        os.environ["MEMENTO_AI_DIR"] = str(self.tmp.name)
        self.assertEqual(memento.ai_dir(), Path(self.tmp.name))

    def test_ai_dir_survives_malformed_config(self):
        os.environ.pop("MEMENTO_AI_DIR")
        self.home.mkdir(parents=True, exist_ok=True)
        for bad in ("{not json", '["list", "not", "dict"]'):
            (self.home / "config.json").write_text(bad)
            self.assertEqual(memento.ai_dir(), self.home)

    def test_remind_matches_correction_signals(self):
        import json
        from unittest.mock import patch
        for prompt, expect in (("again?? use uv not python", True),
                               ("we discussed this yesterday", True),
                               ("please add a login page", False)):
            out = io.StringIO()
            with patch("sys.stdin", io.StringIO(json.dumps({"prompt": prompt}))), redirect_stdout(out):
                memento.main(["remind"])
            self.assertEqual("memento" in out.getvalue(), expect, prompt)

    def test_retire_removes_rule_keeps_history_excludes_from_check(self):
        self.run_cmd("hit", "old", "--rule", "Old rule text", "--scope", "global")
        self.run_cmd("promote", "old")
        out = self.run_cmd("retire", "old")
        self.assertIn("retired", out)
        for doc in ("AGENTS.md", "CLAUDE.md"):
            self.assertNotIn("(memento: old)", (self.ai / doc).read_text())
        self.assertIn("- existing rule", (self.ai / "AGENTS.md").read_text())
        self.assertNotIn("Old rule text", self.run_cmd("check"))
        self.assertIn("old", self.run_cmd("list"))
        e = memento.parse(memento.global_ledger())["old"]
        self.assertEqual(e["status"], "retired")
        self.assertEqual(len(e["hits"]), 1)

    def test_retire_watching_entry_needs_no_docs(self):
        self.run_cmd("hit", "w", "--rule", "r", "--scope", "project")
        out = self.run_cmd("retire", "w")
        self.assertIn("retired", out)
        self.assertNotIn("rule removed", out)

    def test_hit_revives_retired_entry(self):
        self.run_cmd("hit", "z", "--rule", "Rule Z", "--scope", "project")
        self.run_cmd("retire", "z")
        out = self.run_cmd("hit", "z")
        self.assertIn("revived", out)
        e = memento.parse(self.proj / "MEMENTO.md")["z"]
        self.assertEqual(e["status"], "watching")
        self.assertIn("Rule Z", self.run_cmd("check"))

    def test_hit_warns_when_slug_in_both_ledgers(self):
        self.run_cmd("hit", "dup", "--rule", "r", "--scope", "global")
        entries = {"dup": memento.new_entry("dup") | {"scope": "project", "rule": "r"}}
        memento.save(self.proj / "MEMENTO.md", entries, "project")
        out = self.run_cmd("hit", "dup")
        self.assertIn("both ledgers", out)
        self.assertIn("project shadows global", out)

    def test_bootstrap_appendix_matches_script(self):
        boot = (Path(__file__).parent / "BOOTSTRAP.md").read_text()
        appendix = boot.split("<!-- appendix-start -->\n```python\n", 1)[1]
        appendix = appendix.split("```\n<!-- appendix-end -->", 1)[0]
        script = (Path(__file__).parent / "memento.py").read_text()
        self.assertEqual(appendix, script, "BOOTSTRAP.md appendix out of sync with memento.py")
        skill = (Path(__file__).parent / "SKILL.md").read_text()
        self.assertNotIn("```python", skill, "SKILL.md must stay slim — script lives in BOOTSTRAP.md")


if __name__ == "__main__":
    unittest.main()
