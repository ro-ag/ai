# AI Workspace

Workspace for agent documentation, helpers, and small tools. These rules exist to get the best results from agents without wasting tokens.

Posture: **quality first** — use the best model for work that matters; save tokens by avoiding waste (repeated work, bloated context), not by downgrading quality. **Never use haiku, anywhere, for anything.** Reasoning effort stays at default unless the task needs deep reasoning.

## Rule files (read on demand — do not preload)

- `rules/subagents.md` — read BEFORE delegating work to any subagent
- `rules/releases.md` — read BEFORE any release, tag, or publish action
- `rules/agents.md` — inventory of agents, skills, and MCP servers on this machine
- `rules/fleet.md` — multi-tool subscriptions (Codex, Cursor, GLM…) and task routing
- `rules/research-2026-07.md` — verified evidence base behind these rules
- `AGENTS.md` — mirrors the hard rules for the non-Claude tools in the fleet; keep in sync with this file

## Token discipline

- Delegate broad searches and investigation to subagents; keep the main context for decisions. Default code locator: `caveman:cavecrew-investigator` (compressed output).
- If exploration would take more than ~3 file reads or ~5 tool calls, delegate it instead of doing it inline.
- Batch independent tool calls in a single message so they run in parallel.
- Read only the line ranges you need from large files; never re-read files already in context.
- Keep this file under ~50 lines. Details belong in `rules/`, loaded on demand.

## Hard rules

- Do not refactor code unrelated to the task. Do not modify unrelated files. Do not install new dependencies without explicit approval. (Measured: these three guardrails are the highest-value rules in controlled studies — `rules/research-2026-07.md`.)
- No AI attribution anywhere, ever: no `Co-Authored-By`, no "Generated with Claude" in commits, PRs, or release notes.
- Always create a working branch before starting work. Never commit directly to `main`. Branches land via PR + squash merge: `gh pr merge --squash --delete-branch`.
- If the working directory has no git repository or no associated remote: stop and ask the user how to proceed before making changes.
- Never release, tag, push, or publish without an explicit user request in the current session.
- GitHub Actions only when explicitly asked, and only triggered on merge to `main` / release tags — never per-push or per-PR. Quality gates run locally before merge.
- Each project lives in its own subdirectory. Add a project-level CLAUDE.md only when its rules differ from these.
