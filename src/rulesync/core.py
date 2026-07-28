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
- When CI exists or is requested, keep it cheap: lint/unit on Linux only,
  Windows gated to PRs + `main`, macOS UI tests gated to approved PRs /
  `main` / nightly / releases. Cancel superseded PR runs, filter paths,
  cache dependencies, and gate expensive jobs behind Linux checks (`needs:`).
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
