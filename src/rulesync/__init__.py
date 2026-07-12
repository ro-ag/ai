"""rulesync — point every AI tool's global instructions at the rules repo.

Writes a marker-delimited pointer block into each tool's global rules file so
that Claude Code, Codex, Cursor, Antigravity, zcode, Trae, opencode and Copilot
all read /Users/rodox/dev/ai (AGENTS.md + rules/) before working. Re-running
replaces the block in place; nothing outside the markers is touched.

Also enforces one config law: Copilot's `includeCoAuthoredBy` is forced to
false (it defaults to true, which violates the no-attribution rule).
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path

REPO = Path.home() / "dev" / "ai"
BEGIN = "<!-- ai-rules-repo:begin -->"
END = "<!-- ai-rules-repo:end -->"

BLOCK = f"""{BEGIN}
# Machine-wide agent rules — read first

Before starting any work, read `{REPO}/AGENTS.md` and, when relevant,
`{REPO}/rules/` (fleet routing, releases, subagents). Those laws override
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
    confidence: str  # "confirmed" | "standard" | "best-effort"
    note: str = ""


TOOLS = [
    Tool("claude", Path.home() / ".claude" / "CLAUDE.md", "confirmed"),
    Tool("codex", Path.home() / ".codex" / "AGENTS.md", "confirmed"),
    Tool("opencode", Path.home() / ".config" / "opencode" / "AGENTS.md", "confirmed"),
    Tool("cursor", Path.home() / ".cursor" / "AGENTS.md", "standard",
         "documented global AGENTS.md location for cursor-agent"),
    Tool("zcode", Path.home() / ".zcode" / "cli" / "AGENTS.md", "best-effort",
         "codex-fork layout (rollout/); verify pickup on next zcode session"),
    Tool("agy", Path.home() / ".antigravity" / "AGENTS.md", "best-effort",
         "verify pickup; Antigravity may manage rules internally"),
    Tool("trae", Path.home() / ".trae" / "AGENTS.md", "best-effort",
         "Trae user rules are UI-managed; paste the block there once to be sure"),
    Tool("copilot", Path.home() / ".copilot" / "AGENTS.md", "best-effort",
         "copilot loads AGENTS.md 'and related files'; verify with `copilot init`"),
]

# User settings file (config.json is auto-managed and holds no user settings)
COPILOT_SETTINGS = Path.home() / ".copilot" / "settings.json"


def upsert_block(existing: str, block: str = BLOCK) -> str:
    """Insert or replace the marker-delimited block. Pure; idempotent."""
    if BEGIN in existing and END in existing:
        head, rest = existing.split(BEGIN, 1)
        _, tail = rest.split(END, 1)
        return head + block + tail
    if not existing.strip():
        return block + "\n"
    sep = "" if existing.endswith("\n\n") else "\n" if existing.endswith("\n") else "\n\n"
    return existing + sep + block + "\n"


def sync_tool(tool: Tool, dry_run: bool) -> str:
    if not tool.path.parent.is_dir():
        return "skipped (tool not installed)"
    existing = tool.path.read_text() if tool.path.exists() else ""
    updated = upsert_block(existing)
    if updated == existing:
        return "up to date"
    if not dry_run:
        tool.path.write_text(updated)
    verb = "would write" if dry_run else "wrote"
    state = "replaced block" if BEGIN in existing else ("created" if not existing else "appended block")
    return f"{verb} ({state})"


def fix_copilot_attribution(dry_run: bool) -> str:
    if not COPILOT_SETTINGS.parent.is_dir():
        return "skipped (copilot not installed)"
    cfg: dict = {}
    if COPILOT_SETTINGS.exists():
        try:
            cfg = json.loads(COPILOT_SETTINGS.read_text())
        except json.JSONDecodeError:
            return "MANUAL: settings.json unparseable — set includeCoAuthoredBy=false yourself"
    if cfg.get("includeCoAuthoredBy") is False:
        return "already false"
    cfg["includeCoAuthoredBy"] = False
    if not dry_run:
        COPILOT_SETTINGS.write_text(json.dumps(cfg, indent=2) + "\n")
    return "would set false" if dry_run else "set false"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="rulesync", description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="report only, change nothing")
    args = parser.parse_args(argv)

    width = max(len(t.name) for t in TOOLS)
    for tool in TOOLS:
        result = sync_tool(tool, args.dry_run)
        line = f"{tool.name:<{width}}  {result}  [{tool.confidence}]"
        if tool.note and "skipped" not in result:
            line += f" — {tool.note}"
        print(line)
    print(f"{'copilot-attribution':<{width}}  {fix_copilot_attribution(args.dry_run)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
