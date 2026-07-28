# AI Workspace

Workspace for agent documentation, helpers, and small tools. These rules exist to get the best results from agents without wasting tokens.

Posture: **quality first** — use the best model for work that matters; save tokens by avoiding waste (repeated work, bloated context), not by downgrading quality. **Never use haiku, anywhere, for anything.** Reasoning effort stays at default unless the task needs deep reasoning.

## Rule files (read on demand — do not preload)

- `rules/subagents.md` — read BEFORE delegating work to any subagent
- `rules/releases.md` — read BEFORE any release, tag, or publish action
- `rules/agents.md` — inventory of agents, skills, and MCP servers on this machine
- `rules/fleet.md` — multi-tool subscriptions (Codex, Cursor, GLM…) and task routing
- `rules/second-opinion.md` — cross-vendor review via Codex / Grok / Gemini bridges
- `rules/github-actions.md` — read BEFORE creating, editing, or auditing any CI workflow
- `AGENTS.md` — mirrors the hard rules for the non-Claude tools in the fleet; keep in sync with this file

## Token discipline

- Delegate broad searches and investigation to subagents; keep the main context for decisions. Default code locator: `caveman:cavecrew-investigator` (compressed output).
- If exploration would take more than ~3 file reads or ~5 tool calls, delegate it instead of doing it inline.
- Batch independent tool calls in a single message so they run in parallel.
- Read only the line ranges you need from large files; never re-read files already in context.
- Keep this file under ~50 lines. Details belong in `rules/`, loaded on demand.

## Hard rules

- Do not refactor code unrelated to the task. Do not modify unrelated files. Do not install new dependencies without explicit approval.
- No AI attribution anywhere, ever: no `Co-Authored-By`, no "Generated with …" in commits, PRs, or release notes.
- Always create a working branch before starting work. Never commit directly to `main`. Branches land via PR + squash merge: `gh pr merge --squash --delete-branch`. Never leave any branch but `main` in local or remote after merging.
- If the working directory has no git repository or no associated remote: stop and ask the user how to proceed before making changes.
- Never release, tag, push, or publish without an explicit user request in the current session.
- Releases publish via GitHub Actions on tag push ONLY — never locally (`cargo publish`, `npm publish`, `twine upload`, hand-run `gh release create`). Tag + changelog + README consistent, tests passing, before the release push.
- GitHub Actions only when explicitly asked, and only triggered on merge to `main` / release tags — never per-push or per-PR. Quality gates run locally before merge. When CI exists or is requested, enforce the cost rules in `rules/github-actions.md` (Linux-first, gated Windows/macOS, concurrency cancellation, path filters, caches, staged jobs).
- Each project lives in its own subdirectory. Add a project-level CLAUDE.md only when its rules differ from these.

## Language rules

- **Rust:** do not combine sources with tests — never put `#[cfg(test)] mod tests` blocks inside a source file. Go-style siblings: `module.rs` + `module_test.rs`, wired from the parent (`lib.rs`/`mod.rs`) with `#[cfg(test)] mod module_test;`.
