# rulesync v2 — interactive rich CLI + review fixes

Date: 2026-07-11. Status: approved (design discussed in session; guided-flow shape chosen by user).

## Goal

Turn `rulesync` from a print-only script into a polished interactive CLI built on
`rich`: status table → tool selection → preview → confirm → apply → results.
Fold in every code fix from the 2026-07-11 project review. Fix the reported
documentation drift in the same branch.

Visual quality is an explicit requirement ("killer good looking UI"): themed,
color-coded, panelled output — not bare prints.

## Non-goals

- No textual/full-TUI framework; `rich` only (user-approved dependency).
- No persistent menu loop; single guided pass per invocation.
- No new tools in `TOOLS`; same eight targets + copilot attribution law.
- No behavior change to what gets written (same marker block semantics).

## Package layout

```
src/rulesync/
  __init__.py   — re-exports (__version__, main) only
  core.py       — data + logic, no UI: Tool, TOOLS, BLOCK, MarkerError,
                  upsert_block(), plan_tool(), apply_tool(),
                  plan_copilot_attribution(), apply_copilot_attribution()
  cli.py        — rich UI + argparse; entry point main()
tests/
  test_core.py  — logic tests (replaces test_rulesync.py)
  test_cli.py   — flag paths + interactive smoke (monkeypatched prompts)
```

`pyproject.toml`: `dependencies = ["rich>=13"]`; script `rulesync = "rulesync.cli:main"`.

Core is plan/apply split so the UI can preview without writing: `plan_*`
returns a `PlannedChange` (tool, action, new_content, error) and `apply_*`
executes one plan atomically.

## UX flow (no args, TTY)

1. **Header** — `Panel`: bold "rulesync" title, subtitle = repo path + mode.
2. **Status table** — rounded-box `Table`; columns: `#`, tool (bold cyan),
   state, path (dim), confidence badge, note (dim, truncated).
   State colors: green `synced` · yellow `stale block` / `no block` ·
   red `MANUAL: bad markers` / errors · dim `not installed`.
   Copilot attribution appears as its own final row (state: `already false` /
   `will set false` / `MANUAL: unparseable`); it is selectable like any tool
   row and included in the `a` (all) selection when actionable.
3. **Select** — `Prompt.ask` with choices: `a` (all needing sync), `n` (none),
   or comma-separated row numbers. Default `a`. Rows that are `synced`,
   `not installed`, or `MANUAL` are not selectable; selecting them re-prompts.
4. **Preview** — one `Panel` showing the marker block (rendered as
   `Markdown`), then a compact list: `tool → create | append block | replace block`.
5. **Confirm** — `Confirm.ask("Apply N changes?")`; decline exits 0, "aborted".
6. **Apply** — transient `Progress` spinner per tool; failures don't stop the
   loop (per-tool isolation).
7. **Results** — table: tool → `wrote (replaced block)` etc. or red error text;
   closing one-line summary panel: `N applied · N skipped · N errors`.

## Flags / non-interactive

- `--dry-run` — header + status table + preview only; no prompts, no writes.
- `--yes` — no prompts; apply to everything needing sync (CI/scripting).
- `--tool NAME` (repeatable) — restrict table and flow to named tools; combines
  with the interactive flow (still prompts) or with `--yes`/`--dry-run`;
  unknown name = error exit 2.
- Non-TTY stdin without `--yes` → behaves as `--dry-run` (safe default).
- Exit codes: 0 success/aborted/nothing-to-do, 1 any apply error, 2 bad usage.
- `NO_COLOR` and non-TTY degrade gracefully (rich handles; no custom escapes).

## Review fixes folded in (traceability)

| Review finding | Fix |
|---|---|
| 🔴 `upsert_block` corrupts/crashes on unbalanced or misordered markers | validate: exactly one `BEGIN`, one `END`, `BEGIN` before `END`; else raise `MarkerError` → state `MANUAL: bad markers`, file never touched |
| 🟡 non-atomic `write_text` | write `.<name>.rulesync.tmp` in same dir, `os.replace()` |
| 🟡 TOCTOU `exists()`→`read_text()` | read inside `try/except FileNotFoundError` → treat as empty |
| 🟡 one tool's IO error kills whole run | per-tool `try/except OSError` in apply loop; error recorded in results row |
| 🔵 hard-coded repo path | `RULESYNC_REPO` env var overrides `~/dev/ai` |
| 🔵 `confidence: str` | `Literal["confirmed", "standard", "best-effort"]` |
| (killed) `json.dumps` non-serializable | no change — `cfg` always comes from `json.loads` |

## Docs fixes (same branch, own commit)

- `CLAUDE.md`: add `rules/tooling.md` to the rule-files index; keep file ≤ ~50 lines.
- Reconcile the four CLAUDE.md ↔ AGENTS.md hard-rule divergences. AGENTS.md
  carries full strength: add the `gh release create` ban and the exact
  `gh pr merge --squash --delete-branch` command; align attribution wording
  (`"Generated with Claude"` example in both). CLAUDE.md keeps the Actions
  cost warning it already has; AGENTS.md keeps its pre-existing-workflow caveat
  — content must not conflict, exact phrasing may differ where scope differs.
- `core.py` BLOCK stays the condensed "hard minimum" of the AGENTS.md hard
  rules; AGENTS.md gains a note telling editors to keep the BLOCK in step and
  re-run `uv run rulesync` after hard-rule changes.
- `.claude/skills/second-opinion/SKILL.md`: make the three example commands
  stance-specific (critical / steelman / neutral) matching the procedure text.
- `rules/fleet.md:87`: unsourced "~54% on AA-Omniscience" → keep the caution,
  drop the unverified number (no fabricated citations).

## Testing

- `test_core.py`: marker validation (duplicate BEGIN, duplicate END, END
  before BEGIN, lone BEGIN, lone END), idempotency (plan on synced file =
  no-op), create/append/replace paths, separator handling, copilot paths
  (dir absent / file absent / unparseable / already false / set false),
  atomic-write behavior (tmp file gone after apply), per-tool error isolation
  (unwritable dir → error result, loop continues). Uses `tmp_path` +
  monkeypatched `Path.home()` / `RULESYNC_REPO`.
- `test_cli.py`: `--dry-run` writes nothing; `--yes` applies without prompts;
  `--tool` filters and rejects unknown names; interactive smoke with
  monkeypatched `Prompt.ask` / `Confirm.ask`; non-TTY defaults to dry-run.
- All via `uv run pytest`. TDD: tests written per-feature before implementation.

## Workflow

Branch `feat/rulesync-interactive` (created). Commits: (1) docs fixes,
(2) core + cli + tests, (3) spec/plan docs as needed. `uv add rich`.
PR + squash merge, conventional title, no AI attribution anywhere.
