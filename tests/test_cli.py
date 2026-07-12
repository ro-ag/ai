import json
from pathlib import Path

import pytest

from rulesync import cli
from rulesync.core import BEGIN


@pytest.fixture
def fake_home(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("RULESYNC_REPO", str(tmp_path / "dev" / "ai"))
    (tmp_path / ".claude").mkdir()
    (tmp_path / ".copilot").mkdir()
    return tmp_path


def claude_file(home: Path) -> Path:
    return home / ".claude" / "CLAUDE.md"


def copilot_settings(home: Path) -> Path:
    return home / ".copilot" / "settings.json"


def test_dry_run_writes_nothing(fake_home):
    assert cli.main(["--dry-run"]) == 0
    assert not claude_file(fake_home).exists()
    assert not copilot_settings(fake_home).exists()


def test_yes_applies_everything(fake_home):
    assert cli.main(["--yes"]) == 0
    assert BEGIN in claude_file(fake_home).read_text()
    cfg = json.loads(copilot_settings(fake_home).read_text())
    assert cfg["includeCoAuthoredBy"] is False


def test_second_run_reports_synced(fake_home):
    cli.main(["--yes"])
    before = claude_file(fake_home).read_text()
    assert cli.main(["--yes"]) == 0
    assert claude_file(fake_home).read_text() == before


def test_tool_filter_limits_targets(fake_home):
    assert cli.main(["--yes", "--tool", "claude"]) == 0
    assert claude_file(fake_home).exists()
    assert not copilot_settings(fake_home).exists()


def test_unknown_tool_exits_2(fake_home):
    assert cli.main(["--tool", "nope"]) == 2


def test_non_tty_without_yes_behaves_as_dry_run(fake_home, monkeypatch):
    monkeypatch.setattr(cli, "_interactive_session", lambda: False)
    assert cli.main([]) == 0
    assert not claude_file(fake_home).exists()


def test_interactive_select_all_and_confirm(fake_home, monkeypatch):
    monkeypatch.setattr(cli, "_interactive_session", lambda: True)
    monkeypatch.setattr(cli.Prompt, "ask", staticmethod(lambda *a, **k: "a"))
    monkeypatch.setattr(cli.Confirm, "ask", staticmethod(lambda *a, **k: True))
    assert cli.main([]) == 0
    assert BEGIN in claude_file(fake_home).read_text()


def test_interactive_decline_writes_nothing(fake_home, monkeypatch):
    monkeypatch.setattr(cli, "_interactive_session", lambda: True)
    monkeypatch.setattr(cli.Prompt, "ask", staticmethod(lambda *a, **k: "a"))
    monkeypatch.setattr(cli.Confirm, "ask", staticmethod(lambda *a, **k: False))
    assert cli.main([]) == 0
    assert not claude_file(fake_home).exists()


def test_apply_error_isolated_and_exit_1(fake_home, monkeypatch):
    real_apply = cli.apply_plan

    def flaky(planned):
        if planned.tool.name == "copilot-attribution":
            raise OSError("disk on fire")
        real_apply(planned)

    monkeypatch.setattr(cli, "apply_plan", flaky)
    assert cli.main(["--yes"]) == 1
    assert claude_file(fake_home).exists()          # other tool still synced
    assert not copilot_settings(fake_home).exists()  # failed one untouched


def test_parse_selection_variants():
    plans = {1: "p1", 2: "p2", 3: "p3"}
    assert cli.parse_selection("a", plans) == ["p1", "p2", "p3"]
    assert cli.parse_selection("", plans) == ["p1", "p2", "p3"]
    assert cli.parse_selection("n", plans) == []
    assert cli.parse_selection("1,3", plans) == ["p1", "p3"]
    assert cli.parse_selection("3 1", plans) == ["p3", "p1"]
    assert cli.parse_selection("2,2", plans) == ["p2"]
    assert cli.parse_selection("7", plans) is None
    assert cli.parse_selection("x", plans) is None
