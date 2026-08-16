# Agent rules — all AI tools

Shared rules for every AI coding tool on this machine (Codex, Cursor, Copilot, Antigravity, Trae, opencode, zcode/GLM). Claude Code reads `CLAUDE.md`, which mirrors these. Keep the two in sync.

## Hard rules

- Do not refactor code unrelated to the task. Do not modify unrelated files. Do not install new dependencies without explicit approval.
- No AI attribution, ever: no `Co-Authored-By`, no "Generated with …" in commits, PRs, or release notes.
- Always create a working branch before starting work. Never commit directly to `main`/`master`. Branches land via PR + squash merge (`gh pr merge --squash --delete-branch`) — never leave any branch but `main` in local or remote after merging.
- If the working directory has no git repository or no associated remote: stop and ask the user before making changes.
- Never release, tag, push, or publish without an explicit user request in the current session.
- Releases publish via GitHub Actions on tag push ONLY — never locally (no local `cargo publish`, `npm publish`, `twine upload`, no hand-run `gh release create`). Tag + changelog + README consistent and tests passing before the release push.
- GitHub Actions cost money on private repos: never add or enable a workflow unless explicitly asked. When one exists, it triggers on merge to `main` or on release tags only — never on every push or PR update. Quality gates run locally (tests, lint, review) before merge instead. When CI exists or is requested, enforce the cost rules in `rules/github-actions.md`: lint/unit on Linux only, Windows gated to PRs + `main`, macOS UI/AppKit gated to approved PRs / `main` / nightly / releases, cancel superseded PR runs, path filters, dependency caches, expensive jobs `needs:` cheap Linux gates.

## Language rules

- **Rust:** do not combine sources with tests — never put `#[cfg(test)] mod tests` blocks inside a source file. Go-style siblings: `module.rs` + `module_test.rs`, wired from the parent (`lib.rs`/`mod.rs`) with `#[cfg(test)] mod module_test;`.

## Memento — learn from mistakes (all tools)

- Repeated-mistake ledger + enforcement. CLI: `python3 ~/.agents/memento/memento.py` (`uv run memento` inside this repo). Full protocol: `memento/SKILL.md`.
- Task start: run `memento check` and respect its output. On any user correction, hard-won fix, or ignored quality gate: `memento hit <slug> --rule "..." --fix "..."`. On a PROMOTE alert or user "always/never": `memento promote <slug>`.

## Workspace

- Purpose: agent documentation, helpers, and small tools. Each project in its own subdirectory.
- Release process: `rules/releases.md`. CI cost rules: `rules/github-actions.md`. Machine-local (gitignored): `rules/local/` — tool fleet, inventories, review bridges.
- Posture: quality first — save tokens by avoiding waste, not by downgrading model quality on work that matters.
- When hard rules change: re-run `uv run rulesync`, and keep the pointer BLOCK in `src/rulesync/core.py` in step — it is the condensed "hard minimum" copy of these rules.

## Memento-enforced

Rules promoted from the memento ledger. Details/fix: `memento show <slug>`.
- In uv-managed projects use uv run / uv add only — never bare python or pip (memento: uv-not-python)
- Never ignore SonarQube gate findings — coverage, cognitive complexity, and code smells must be fixed before calling work done (memento: quality-gates-ignored)

