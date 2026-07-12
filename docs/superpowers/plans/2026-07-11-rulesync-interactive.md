# rulesync v2 — Interactive Rich CLI Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn `rulesync` into a rich-powered guided CLI (status table → select → preview → confirm → apply) and fix every finding from the 2026-07-11 review.

**Architecture:** Split the single module into `core.py` (pure plan/apply logic, no UI) and `cli.py` (rich rendering + argparse). Planning never writes; applying writes atomically per tool with per-tool error isolation. Docs drift fixed in its own commit.

**Tech Stack:** Python ≥3.12, `rich>=13` (only runtime dep, user-approved), pytest, uv, hatchling.

## Global Constraints

- Never use `Co-Authored-By` or any AI attribution in commits/PRs.
- Work happens on branch `feat/rulesync-interactive` (already created).
- Conventional-prefix commit titles.
- `requires-python = ">=3.12"`; runtime deps exactly `["rich>=13"]`.
- Keep `CLAUDE.md` ≤ ~50 lines.
- Spec: `docs/superpowers/specs/2026-07-11-rulesync-interactive-design.md`.
- All test runs via `uv run pytest -q` from `/Users/rodox/dev/ai`.

---

### Task 1: Documentation reconciliation

**Files:**
- Modify: `CLAUDE.md`, `AGENTS.md`, `README.md`, `.claude/skills/second-opinion/SKILL.md`, `rules/fleet.md`, `docs/superpowers/specs/2026-07-11-rulesync-interactive-design.md`

**Interfaces:** none (docs only). Later tasks rely on AGENTS.md keeping the sync-note line referencing `src/rulesync/core.py`.

- [ ] **Step 1: CLAUDE.md — add tooling.md to the rule-files index**

In the "Rule files" list, after the `rules/fleet.md` line, insert:

```markdown
- `rules/tooling.md` — scouted ecosystem tools (optimizers, token trackers, linters)
```

- [ ] **Step 2: CLAUDE.md — broaden attribution example to match AGENTS.md**

Replace:
```markdown
- No AI attribution anywhere, ever: no `Co-Authored-By`, no "Generated with Claude" in commits, PRs, or release notes.
```
with:
```markdown
- No AI attribution anywhere, ever: no `Co-Authored-By`, no "Generated with …" in commits, PRs, or release notes.
```

- [ ] **Step 3: AGENTS.md — full-strength branch + release rules, add BLOCK sync note**

Replace line 9 (branch rule):
```markdown
- Always create a working branch before starting work. Never commit directly to `main`/`master`. Branches land via PR + squash merge, branch deleted at merge — never leave any branch but `main` in local or remote.
```
with:
```markdown
- Always create a working branch before starting work. Never commit directly to `main`/`master`. Branches land via PR + squash merge (`gh pr merge --squash --delete-branch`) — never leave any branch but `main` in local or remote after merging.
```

Replace line 12 (release rule):
```markdown
- Releases publish via GitHub Actions on tag push ONLY — never locally (no local `cargo publish`, `npm publish`, `twine upload`). Tag + changelog + README consistent and tests passing before the release push.
```
with:
```markdown
- Releases publish via GitHub Actions on tag push ONLY — never locally (no local `cargo publish`, `npm publish`, `twine upload`, no hand-run `gh release create`). Tag + changelog + README consistent and tests passing before the release push.
```

In the "## Workspace" section, append this bullet:
```markdown
- When hard rules change: re-run `uv run rulesync`, and keep the pointer BLOCK in `src/rulesync/core.py` in step — it is the condensed "hard minimum" copy of these rules.
```

- [ ] **Step 4: SKILL.md — stance-specific example commands**

In `.claude/skills/second-opinion/SKILL.md`, replace the bash block:
```bash
   codex exec "STANCE. $(cat .reviews/<dir>/brief.md)" < /dev/null > .reviews/<dir>/codex.md
   cursor-agent -p "STANCE. $(cat .reviews/<dir>/brief.md)" --model grok-4.5-high --trust --output-format text > .reviews/<dir>/grok.md
   agy --print "STANCE. $(cat .reviews/<dir>/brief.md)" > .reviews/<dir>/gemini.md
```
with:
```bash
   codex exec "Argue against this; find the flaws. $(cat .reviews/<dir>/brief.md)" < /dev/null > .reviews/<dir>/codex.md
   cursor-agent -p "Steelman the strongest case for this. $(cat .reviews/<dir>/brief.md)" --model grok-4.5-high --trust --output-format text > .reviews/<dir>/grok.md
   agy --print "Weigh both sides, then commit to a verdict. $(cat .reviews/<dir>/brief.md)" > .reviews/<dir>/gemini.md
```

- [ ] **Step 5: fleet.md — drop unverified benchmark number**

Replace line 87:
```markdown
- **Caveat: hallucination rate spiked (~54% on AA-Omniscience) and community trust concerns.** Fleet role: fast second opinion and tool-heavy agentic runs — never sole authority on facts or architecture.
```
with:
```markdown
- **Caveat: elevated hallucination rate and community trust concerns (no verified benchmark figure).** Fleet role: fast second opinion and tool-heavy agentic runs — never sole authority on facts or architecture.
```

- [ ] **Step 6: README.md — document interactive rulesync**

Replace the `uv run rulesync` table row's purpose cell text with:
```markdown
Sync the "read this repo first" pointer block into every AI tool's global instructions file (claude, codex, cursor, zcode, agy, trae, opencode, copilot) and force Copilot's `includeCoAuthoredBy` to false. Interactive by default: status table → pick tools → preview → confirm. `--dry-run` previews, `--yes` applies without prompts, `--tool NAME` targets specific tools. Idempotent; re-run after changing hard rules.
```

- [ ] **Step 7: Spec — align BLOCK wording**

In the spec file, replace:
```markdown
- `core.py` `BLOCK` body = verbatim copy of AGENTS.md "hard minimum" bullet
  list; both AGENTS.md and CLAUDE.md sync notes mention the third copy in
  `rulesync` so future edits update all three.
```
with:
```markdown
- `core.py` BLOCK stays the condensed "hard minimum" of the AGENTS.md hard
  rules; AGENTS.md gains a note telling editors to keep the BLOCK in step and
  re-run `uv run rulesync` after hard-rule changes.
```

- [ ] **Step 8: Verify and commit**

Run: `wc -l CLAUDE.md` — Expected: ≤ 50.
Run: `git add -A && git commit -m "docs: reconcile CLAUDE/AGENTS hard rules, index tooling.md, fix skill stances"`

---

### Task 2: core.py — plan/apply logic with marker validation

**Files:**
- Create: `src/rulesync/core.py`
- Create: `tests/test_core.py`
- Rewrite: `src/rulesync/__init__.py`
- Delete: `tests/test_rulesync.py`

**Interfaces:**
- Produces (Task 3 consumes): `BEGIN`, `END`, `MarkerError`, `Confidence`, `Kind`, `Action`, `ACTIONABLE`, `Tool(name, path, confidence, note="", kind="rules")` frozen dataclass, `PlannedChange(tool, action, new_content=None, detail="")` frozen dataclass with `.actionable` property, `repo_root() -> Path`, `build_block(repo: Path) -> str`, `default_tools(home: Path | None = None) -> list[Tool]`, `make_plan(tool: Tool, block: str) -> PlannedChange`, `apply_plan(planned: PlannedChange) -> None`.

- [ ] **Step 1: Write failing tests**

Create `tests/test_core.py`:

```python
import json
import os
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_core.py -q`
Expected: collection error — `ModuleNotFoundError: No module named 'rulesync.core'`.

- [ ] **Step 3: Implement core.py**

Create `src/rulesync/core.py`:

```python
"""rulesync core — compute and apply pointer-block changes. No UI here.

`make_plan` never touches disk contents; `apply_plan` writes one planned
change atomically. Copilot's `includeCoAuthoredBy` is forced to false (it
defaults to true, which violates the no-attribution rule).

Keep BLOCK in step with the hard rules in AGENTS.md (condensed copy).
"""

from __future__ import annotations

import json
import os
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

BEGIN = "<!-- ai-rules-repo:begin -->"
END = "<!-- ai-rules-repo:end -->"

Confidence = Literal["confirmed", "standard", "best-effort"]
Kind = Literal["rules", "attribution"]
Action = Literal[
    "create",
    "append block",
    "replace block",
    "set false",
    "up to date",
    "skip",
    "manual",
]

ACTIONABLE: frozenset[str] = frozenset(
    {"create", "append block", "replace block", "set false"}
)


class MarkerError(ValueError):
    """File's marker block is unbalanced or misordered — refuse to touch it."""


def repo_root() -> Path:
    return Path(os.environ.get("RULESYNC_REPO") or Path.home() / "dev" / "ai")


def build_block(repo: Path) -> str:
    return f"""{BEGIN}
# Machine-wide agent rules — read first

Before starting any work, read `{repo}/AGENTS.md` and, when relevant,
`{repo}/rules/` (fleet routing, releases, subagents). Those laws override
tool defaults. Hard minimum if the repo is unavailable:

- NEVER add AI attribution (`Co-Authored-By`, "Generated with ...") to
  commits, PRs, or release notes.
- Always create a working branch before starting work; land via PR + squash;
  never leave any branch but `main` in local or remote after merging.
- Never release, tag, publish, or enable CI workflows without an explicit
  user request. If there is no git repo or remote, stop and ask.
- Releases publish via GitHub Actions on tag push ONLY — never local
  `cargo publish` / `npm publish` / `twine upload`. Tests pass and tag,
  changelog, README are consistent before the release push.
- Do not refactor unrelated code, modify unrelated files, or install new
  dependencies without approval.
{END}"""


@dataclass(frozen=True)
class Tool:
    name: str
    path: Path
    confidence: Confidence
    note: str = ""
    kind: Kind = "rules"


def default_tools(home: Path | None = None) -> list[Tool]:
    h = home or Path.home()
    return [
        Tool("claude", h / ".claude" / "CLAUDE.md", "confirmed"),
        Tool("codex", h / ".codex" / "AGENTS.md", "confirmed"),
        Tool("opencode", h / ".config" / "opencode" / "AGENTS.md", "confirmed"),
        Tool("cursor", h / ".cursor" / "AGENTS.md", "standard",
             "documented global AGENTS.md location for cursor-agent"),
        Tool("zcode", h / ".zcode" / "cli" / "AGENTS.md", "best-effort",
             "codex-fork layout (rollout/); verify pickup on next zcode session"),
        Tool("agy", h / ".antigravity" / "AGENTS.md", "best-effort",
             "verify pickup; Antigravity may manage rules internally"),
        Tool("trae", h / ".trae" / "AGENTS.md", "best-effort",
             "Trae user rules are UI-managed; paste the block there once to be sure"),
        Tool("copilot", h / ".copilot" / "AGENTS.md", "best-effort",
             "copilot loads AGENTS.md 'and related files'; verify with `copilot init`"),
        Tool("copilot-attribution", h / ".copilot" / "settings.json", "confirmed",
             "forces includeCoAuthoredBy=false", kind="attribution"),
    ]


@dataclass(frozen=True)
class PlannedChange:
    tool: Tool
    action: Action
    new_content: str | None = None
    detail: str = ""

    @property
    def actionable(self) -> bool:
        return self.action in ACTIONABLE


def validate_markers(text: str) -> None:
    begins, ends = text.count(BEGIN), text.count(END)
    if begins == 0 and ends == 0:
        return
    if begins != 1 or ends != 1:
        raise MarkerError(
            f"expected one begin + one end marker, found {begins} begin / {ends} end"
        )
    if text.index(BEGIN) > text.index(END):
        raise MarkerError("end marker appears before begin marker")


def upsert_block(existing: str, block: str) -> str:
    """Insert or replace the marker-delimited block. Pure; idempotent.

    Raises MarkerError when existing markers are unbalanced or misordered.
    """
    validate_markers(existing)
    if BEGIN in existing:
        head, rest = existing.split(BEGIN, 1)
        _, tail = rest.split(END, 1)
        return head + block + tail
    if not existing.strip():
        return block + "\n"
    sep = "" if existing.endswith("\n\n") else "\n" if existing.endswith("\n") else "\n\n"
    return existing + sep + block + "\n"


def _read_or_empty(path: Path) -> str:
    try:
        return path.read_text()
    except FileNotFoundError:
        return ""


def _plan_rules(tool: Tool, block: str) -> PlannedChange:
    if not tool.path.parent.is_dir():
        return PlannedChange(tool, "skip", detail="tool not installed")
    existing = _read_or_empty(tool.path)
    try:
        updated = upsert_block(existing, block)
    except MarkerError as exc:
        return PlannedChange(tool, "manual", detail=str(exc))
    if updated == existing:
        return PlannedChange(tool, "up to date")
    if BEGIN in existing:
        action: Action = "replace block"
    elif existing.strip():
        action = "append block"
    else:
        action = "create"
    return PlannedChange(tool, action, new_content=updated)


def _plan_attribution(tool: Tool) -> PlannedChange:
    if not tool.path.parent.is_dir():
        return PlannedChange(tool, "skip", detail="copilot not installed")
    raw = _read_or_empty(tool.path)
    cfg: dict = {}
    if raw:
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            return PlannedChange(
                tool, "manual",
                detail="settings.json unparseable — set includeCoAuthoredBy=false yourself",
            )
        if not isinstance(parsed, dict):
            return PlannedChange(
                tool, "manual",
                detail="settings.json is not a JSON object — fix it by hand",
            )
        cfg = parsed
    if cfg.get("includeCoAuthoredBy") is False:
        return PlannedChange(tool, "up to date")
    cfg["includeCoAuthoredBy"] = False
    return PlannedChange(
        tool, "set false", new_content=json.dumps(cfg, indent=2) + "\n"
    )


def make_plan(tool: Tool, block: str) -> PlannedChange:
    if tool.kind == "attribution":
        return _plan_attribution(tool)
    return _plan_rules(tool, block)


def _atomic_write(path: Path, content: str) -> None:
    fd, tmp = tempfile.mkstemp(
        dir=path.parent, prefix=f".{path.name}.", suffix=".rulesync.tmp"
    )
    try:
        with os.fdopen(fd, "w") as handle:
            handle.write(content)
        os.replace(tmp, path)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def apply_plan(planned: PlannedChange) -> None:
    if planned.new_content is None:
        raise ValueError(f"nothing to apply for {planned.tool.name}")
    _atomic_write(planned.tool.path, planned.new_content)
```

- [ ] **Step 4: Rewrite `src/rulesync/__init__.py`**

Replace the entire file with:

```python
"""rulesync — point every AI tool's global instructions at the rules repo."""

__version__ = "0.2.0"
```

- [ ] **Step 5: Delete the old test file**

Run: `git rm tests/test_rulesync.py`

- [ ] **Step 6: Run tests to verify they pass**

Run: `uv run pytest tests/test_core.py -q`
Expected: `30 passed` (parametrized validate cases expand to 5 items).

Note: `test_apply_raises_oserror_when_parent_vanishes` covers the TOCTOU
class: `mkstemp` raises `FileNotFoundError` (an `OSError`) when the parent
disappears between plan and apply.

- [ ] **Step 7: Commit**

```bash
git add -A
git commit -m "feat: rulesync core with marker validation, atomic writes, plan/apply split"
```

---

### Task 3: cli.py — rich guided flow

**Files:**
- Create: `src/rulesync/cli.py`
- Create: `tests/test_cli.py`
- Modify: `pyproject.toml`

**Interfaces:**
- Consumes from Task 2: everything listed in Task 2 "Produces".
- Produces: `rulesync.cli.main(argv: list[str] | None = None) -> int`; console script `rulesync = "rulesync.cli:main"`. Test seam: `cli._interactive_session() -> bool` (module function tests monkeypatch).

- [ ] **Step 1: Add rich dependency and update entry point + version**

Run: `uv add "rich>=13"`
Expected: `pyproject.toml` gains `dependencies = ["rich>=13"]`, `uv.lock` updated.

Then edit `pyproject.toml`: change `version = "0.1.0"` to `version = "0.2.0"` and the script line to:

```toml
[project.scripts]
rulesync = "rulesync.cli:main"
```

- [ ] **Step 2: Write failing tests**

Create `tests/test_cli.py`:

```python
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
```

- [ ] **Step 3: Run tests to verify they fail**

Run: `uv run pytest tests/test_cli.py -q`
Expected: collection error — `ModuleNotFoundError: No module named 'rulesync.cli'`.

- [ ] **Step 4: Implement cli.py**

Create `src/rulesync/cli.py`:

```python
"""rulesync CLI — rich guided flow: status → select → preview → confirm → apply."""

from __future__ import annotations

import argparse
import sys

from rich import box
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Confirm, Prompt
from rich.table import Table
from rich.theme import Theme

from .core import (
    PlannedChange,
    apply_plan,
    build_block,
    default_tools,
    make_plan,
    repo_root,
)

THEME = Theme(
    {
        "accent": "bold cyan",
        "ok": "green",
        "pending": "yellow",
        "err": "bold red",
        "muted": "grey58",
    }
)

# action -> (label shown in tables, theme style)
ACTION_STYLE: dict[str, tuple[str, str]] = {
    "up to date": ("synced", "ok"),
    "create": ("create", "pending"),
    "append block": ("append block", "pending"),
    "replace block": ("replace block", "pending"),
    "set false": ("set includeCoAuthoredBy=false", "pending"),
    "skip": ("not installed", "muted"),
    "manual": ("MANUAL", "err"),
}


def _interactive_session() -> bool:
    return sys.stdin.isatty() and sys.stdout.isatty()


def parse_selection(
    raw: str, actionable_rows: dict[int, PlannedChange]
) -> list[PlannedChange] | None:
    """Turn user input into a plan list. None means invalid — re-prompt."""
    answer = raw.strip().lower()
    if answer in {"", "a", "all"}:
        return list(actionable_rows.values())
    if answer in {"n", "none"}:
        return []
    try:
        numbers = [int(part) for part in answer.replace(",", " ").split()]
    except ValueError:
        return None
    if not numbers or any(n not in actionable_rows for n in numbers):
        return None
    return [actionable_rows[n] for n in dict.fromkeys(numbers)]


def render_header(console: Console, repo, mode: str) -> None:
    console.print(
        Panel.fit(
            f"[accent]rulesync[/] [muted]·[/] {repo}\n[muted]mode:[/] {mode}",
            title="⚡ rules repo pointer",
            title_align="left",
            border_style="accent",
            box=box.ROUNDED,
        )
    )


def render_status(
    console: Console, plans: list[PlannedChange]
) -> dict[int, PlannedChange]:
    table = Table(
        box=box.ROUNDED,
        border_style="muted",
        header_style="accent",
        padding=(0, 1),
    )
    table.add_column("#", justify="right", style="muted")
    table.add_column("tool", style="accent")
    table.add_column("state")
    table.add_column("confidence", style="muted")
    table.add_column("path", style="muted", overflow="fold")
    table.add_column("note", style="muted", max_width=44)

    rows: dict[int, PlannedChange] = {}
    for planned in plans:
        label, style = ACTION_STYLE[planned.action]
        number = ""
        if planned.actionable:
            number = str(len(rows) + 1)
            rows[len(rows) + 1] = planned
        table.add_row(
            number,
            planned.tool.name,
            f"[{style}]{label}[/]",
            planned.tool.confidence,
            str(planned.tool.path),
            planned.detail or planned.tool.note,
        )
    console.print(table)
    return rows


def render_preview(
    console: Console, block: str, selected: list[PlannedChange]
) -> None:
    if any(planned.tool.kind == "rules" for planned in selected):
        console.print(
            Panel(
                Markdown(block),
                title="pointer block",
                border_style="muted",
                box=box.ROUNDED,
            )
        )
    lines = "\n".join(
        f"[accent]{planned.tool.name}[/] → [pending]{ACTION_STYLE[planned.action][0]}[/]"
        for planned in selected
    )
    console.print(
        Panel(
            lines,
            title=f"pending changes ({len(selected)})",
            border_style="pending",
            box=box.ROUNDED,
        )
    )


def prompt_selection(
    console: Console, actionable_rows: dict[int, PlannedChange]
) -> list[PlannedChange]:
    while True:
        raw = Prompt.ask(
            "Sync which? [accent]a[/]ll · [accent]n[/]one · row numbers (e.g. 1,3)",
            default="a",
            console=console,
        )
        selected = parse_selection(raw, actionable_rows)
        if selected is not None:
            return selected
        valid = ", ".join(str(n) for n in actionable_rows)
        console.print(f"[err]invalid selection[/] — pick from: {valid}, 'a', or 'n'")


def apply_selected(
    console: Console, selected: list[PlannedChange]
) -> list[tuple[PlannedChange, str | None]]:
    results: list[tuple[PlannedChange, str | None]] = []
    with Progress(
        SpinnerColumn(style="accent"),
        TextColumn("[progress.description]{task.description}"),
        console=console,
        transient=True,
    ) as progress:
        for planned in selected:
            task = progress.add_task(f"writing {planned.tool.name}…", total=None)
            try:
                apply_plan(planned)
                results.append((planned, None))
            except OSError as exc:
                results.append((planned, str(exc)))
            progress.remove_task(task)
    return results


def render_results(
    console: Console, results: list[tuple[PlannedChange, str | None]]
) -> int:
    table = Table(box=box.ROUNDED, border_style="muted", header_style="accent")
    table.add_column("tool", style="accent")
    table.add_column("result")
    errors = 0
    for planned, error in results:
        if error is None:
            table.add_row(
                planned.tool.name, f"[ok]wrote ({ACTION_STYLE[planned.action][0]})[/]"
            )
        else:
            errors += 1
            table.add_row(planned.tool.name, f"[err]{error}[/]")
    console.print(table)
    applied = len(results) - errors
    style = "err" if errors else "ok"
    console.print(
        Panel.fit(
            f"[{style}]{applied} applied · {errors} error(s)[/]",
            border_style=style,
            box=box.ROUNDED,
        )
    )
    return 1 if errors else 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="rulesync", description=__doc__)
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="show status and pending changes; write nothing",
    )
    parser.add_argument(
        "--yes",
        "-y",
        action="store_true",
        help="apply all pending changes without prompting",
    )
    parser.add_argument(
        "--tool",
        action="append",
        metavar="NAME",
        help="limit to the named tool; repeatable",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    console = Console(theme=THEME)

    repo = repo_root()
    block = build_block(repo)
    tools = default_tools()

    if args.tool:
        known = {tool.name for tool in tools}
        unknown = sorted(set(args.tool) - known)
        if unknown:
            console.print(
                f"[err]unknown tool(s): {', '.join(unknown)}[/] — "
                f"known: {', '.join(sorted(known))}"
            )
            return 2
        wanted = set(args.tool)
        tools = [tool for tool in tools if tool.name in wanted]

    interactive = _interactive_session() and not args.yes and not args.dry_run
    dry_run = args.dry_run or (not args.yes and not interactive)
    mode = "dry-run" if dry_run else ("apply all" if args.yes else "interactive")

    render_header(console, repo, mode)
    plans = [make_plan(tool, block) for tool in tools]
    actionable_rows = render_status(console, plans)

    if not actionable_rows:
        console.print("[ok]✓ everything synced — nothing to do[/]")
        return 0

    if dry_run:
        render_preview(console, block, list(actionable_rows.values()))
        console.print(
            f"[muted]{len(actionable_rows)} pending change(s); "
            f"re-run without --dry-run to apply[/]"
        )
        return 0

    if args.yes:
        selected = list(actionable_rows.values())
        render_preview(console, block, selected)
    else:
        selected = prompt_selection(console, actionable_rows)
        if not selected:
            console.print("[muted]nothing selected — aborted[/]")
            return 0
        render_preview(console, block, selected)
        if not Confirm.ask(
            f"Apply {len(selected)} change(s)?", default=True, console=console
        ):
            console.print("[muted]aborted[/]")
            return 0

    results = apply_selected(console, selected)
    return render_results(console, results)


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 5: Run the full suite**

Run: `uv run pytest -q`
Expected: all tests pass (core + cli).

- [ ] **Step 6: Commit**

```bash
git add -A
git commit -m "feat: rich interactive CLI for rulesync (status, select, preview, confirm, apply)"
```

---

### Task 4: Verification, live smoke, PR

**Files:**
- None new. Verification + PR only.

- [ ] **Step 1: Full test suite + lint**

Run: `uv run pytest -q` — Expected: all pass.
Run: `uvx ruff check .` — Expected: `All checks passed!`

- [ ] **Step 2: Live smoke (read-only)**

Run: `uv run rulesync --dry-run`
Expected: rounded header panel, status table listing 9 rows (8 tools + copilot-attribution), pointer-block panel if anything pending, exit 0. Real tool files must NOT change (verify with `git -C ~ status` not applicable — instead confirm mode line says dry-run and command exits 0).

Run: `uv run rulesync --tool nope; echo "exit=$?"`
Expected: `exit=2`, red unknown-tool message.

- [ ] **Step 3: Push branch and open PR**

```bash
git push -u origin feat/rulesync-interactive
gh pr create --title "feat: interactive rich CLI for rulesync + review fixes" --body "$(cat <<'EOF'
## What

- rulesync v2: guided interactive flow on rich — status table → select → preview → confirm → apply; `--dry-run`, `--yes`, `--tool NAME` for scripting. Core/UI split (`core.py` / `cli.py`).
- Review fixes: marker validation (corrupt/misordered markers → MANUAL, file untouched), atomic writes, per-tool error isolation, TOCTOU-safe reads, `RULESYNC_REPO` override, `Literal` types.
- Docs: CLAUDE.md ↔ AGENTS.md hard-rule reconciliation, `rules/tooling.md` indexed, stance-specific second-opinion examples, unverified Grok benchmark figure dropped, README updated.

## Tests

- `tests/test_core.py`: marker validation matrix, create/append/replace/idempotent, copilot settings paths, atomic-write behavior, OSError propagation.
- `tests/test_cli.py`: flag matrix, non-TTY safe default, interactive select/confirm/decline via monkeypatched prompts, per-tool error isolation exit code.
EOF
)"
```

No AI attribution in the PR body. Squash-merge only on explicit user go:
`gh pr merge --squash --delete-branch`.
