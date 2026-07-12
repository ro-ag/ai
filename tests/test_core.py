import json
from pathlib import Path

import pytest

from rulesync.core import (
    BEGIN,
    END,
    MarkerError,
    Tool,
    apply_plan,
    build_block,
    default_tools,
    make_plan,
    repo_root,
    upsert_block,
    validate_markers,
)

BLOCK = build_block(Path("/repo"))


def rules_tool(tmp_path: Path, name: str = "claude") -> Tool:
    return Tool(name, tmp_path / name / "rules.md", "confirmed")


def attribution_tool(tmp_path: Path) -> Tool:
    return Tool(
        "copilot-attribution",
        tmp_path / ".copilot" / "settings.json",
        "confirmed",
        kind="attribution",
    )


# --- upsert_block / validate_markers -------------------------------------

def test_upsert_into_empty_returns_block():
    assert upsert_block("", BLOCK) == BLOCK + "\n"


def test_upsert_appends_after_content_with_blank_line():
    result = upsert_block("existing\n", BLOCK)
    assert result == "existing\n\n" + BLOCK + "\n"


def test_upsert_appends_when_no_trailing_newline():
    result = upsert_block("existing", BLOCK)
    assert result == "existing\n\n" + BLOCK + "\n"


def test_upsert_replaces_block_preserving_head_and_tail():
    original = "head\n\n" + BLOCK + "\ntail\n"
    updated = upsert_block(original, build_block(Path("/elsewhere")))
    assert updated.startswith("head\n\n")
    assert updated.endswith("\ntail\n")
    assert "/elsewhere" in updated
    assert "/repo" not in updated


def test_upsert_is_idempotent():
    once = upsert_block("notes\n", BLOCK)
    assert upsert_block(once, BLOCK) == once


@pytest.mark.parametrize(
    "text",
    [
        BEGIN,                          # lone begin
        END,                            # lone end
        BEGIN + "x" + BEGIN + END,      # duplicate begin
        BEGIN + END + "x" + END,        # duplicate end
        END + "middle" + BEGIN,         # reversed order
    ],
)
def test_validate_markers_rejects_bad_files(text):
    with pytest.raises(MarkerError):
        validate_markers(text)


def test_validate_markers_accepts_clean_and_absent():
    validate_markers("")
    validate_markers("no markers at all\n")
    validate_markers("head\n" + BLOCK + "\ntail\n")


# --- plan for rules files -------------------------------------------------

def test_plan_skips_when_tool_not_installed(tmp_path):
    plan = make_plan(rules_tool(tmp_path), BLOCK)
    assert plan.action == "skip"
    assert not plan.actionable


def test_plan_create_when_file_missing(tmp_path):
    tool = rules_tool(tmp_path)
    tool.path.parent.mkdir()
    plan = make_plan(tool, BLOCK)
    assert plan.action == "create"
    assert plan.new_content == BLOCK + "\n"


def test_plan_append_when_file_has_content(tmp_path):
    tool = rules_tool(tmp_path)
    tool.path.parent.mkdir()
    tool.path.write_text("user notes\n")
    plan = make_plan(tool, BLOCK)
    assert plan.action == "append block"
    assert plan.new_content.startswith("user notes\n")


def test_plan_replace_when_block_stale(tmp_path):
    tool = rules_tool(tmp_path)
    tool.path.parent.mkdir()
    tool.path.write_text("head\n" + build_block(Path("/old")) + "\ntail\n")
    plan = make_plan(tool, BLOCK)
    assert plan.action == "replace block"
    assert "/old" not in plan.new_content


def test_plan_up_to_date_after_apply(tmp_path):
    tool = rules_tool(tmp_path)
    tool.path.parent.mkdir()
    apply_plan(make_plan(tool, BLOCK))
    assert make_plan(tool, BLOCK).action == "up to date"


def test_plan_manual_on_corrupt_markers(tmp_path):
    tool = rules_tool(tmp_path)
    tool.path.parent.mkdir()
    corrupt = "a\n" + END + "\nb\n" + BEGIN + "\nc\n"
    tool.path.write_text(corrupt)
    plan = make_plan(tool, BLOCK)
    assert plan.action == "manual"
    assert plan.new_content is None
    assert tool.path.read_text() == corrupt  # untouched


# --- apply ----------------------------------------------------------------

def test_apply_writes_content_and_leaves_no_tmp_files(tmp_path):
    tool = rules_tool(tmp_path)
    tool.path.parent.mkdir()
    apply_plan(make_plan(tool, BLOCK))
    assert tool.path.read_text() == BLOCK + "\n"
    leftovers = [p for p in tool.path.parent.iterdir() if p != tool.path]
    assert leftovers == []


def test_apply_rejects_plan_without_content(tmp_path):
    plan = make_plan(rules_tool(tmp_path), BLOCK)  # skip plan
    with pytest.raises(ValueError):
        apply_plan(plan)


def test_apply_raises_oserror_when_parent_vanishes(tmp_path):
    tool = rules_tool(tmp_path)
    tool.path.parent.mkdir()
    plan = make_plan(tool, BLOCK)
    tool.path.parent.rmdir()
    with pytest.raises(OSError):
        apply_plan(plan)


# --- copilot attribution ----------------------------------------------------

def test_attribution_skip_when_not_installed(tmp_path):
    assert make_plan(attribution_tool(tmp_path), BLOCK).action == "skip"


def test_attribution_sets_false_when_file_missing(tmp_path):
    tool = attribution_tool(tmp_path)
    tool.path.parent.mkdir()
    plan = make_plan(tool, BLOCK)
    assert plan.action == "set false"
    assert json.loads(plan.new_content) == {"includeCoAuthoredBy": False}


def test_attribution_preserves_other_settings(tmp_path):
    tool = attribution_tool(tmp_path)
    tool.path.parent.mkdir()
    tool.path.write_text('{"theme": "dark", "includeCoAuthoredBy": true}\n')
    plan = make_plan(tool, BLOCK)
    cfg = json.loads(plan.new_content)
    assert cfg == {"theme": "dark", "includeCoAuthoredBy": False}


def test_attribution_up_to_date_when_already_false(tmp_path):
    tool = attribution_tool(tmp_path)
    tool.path.parent.mkdir()
    tool.path.write_text('{"includeCoAuthoredBy": false}')
    assert make_plan(tool, BLOCK).action == "up to date"


def test_attribution_manual_on_unparseable_json(tmp_path):
    tool = attribution_tool(tmp_path)
    tool.path.parent.mkdir()
    tool.path.write_text("{nope")
    assert make_plan(tool, BLOCK).action == "manual"


def test_attribution_manual_on_non_object_json(tmp_path):
    tool = attribution_tool(tmp_path)
    tool.path.parent.mkdir()
    tool.path.write_text("[1, 2]")
    assert make_plan(tool, BLOCK).action == "manual"


# --- config ---------------------------------------------------------------

def test_repo_root_honors_env_override(monkeypatch, tmp_path):
    monkeypatch.setenv("RULESYNC_REPO", str(tmp_path / "elsewhere"))
    assert repo_root() == tmp_path / "elsewhere"


def test_repo_root_defaults_to_home_dev_ai(monkeypatch):
    monkeypatch.delenv("RULESYNC_REPO", raising=False)
    assert repo_root() == Path.home() / "dev" / "ai"


def test_default_tools_paths_under_given_home(tmp_path):
    tools = default_tools(home=tmp_path)
    assert len(tools) == 9
    assert all(str(t.path).startswith(str(tmp_path)) for t in tools)
    kinds = {t.name: t.kind for t in tools}
    assert kinds["copilot-attribution"] == "attribution"
    assert kinds["claude"] == "rules"


def test_build_block_embeds_repo_and_markers():
    block = build_block(Path("/somewhere/repo"))
    assert block.startswith(BEGIN)
    assert block.endswith(END)
    assert "/somewhere/repo/AGENTS.md" in block
