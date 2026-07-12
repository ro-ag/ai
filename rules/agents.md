# Agent, skill, and MCP inventory — this machine

Snapshot: 2026-07-11. Refresh when plugins change (`ls ~/.claude/plugins/cache/*`) or when the session's agent list differs from this file.

## Subagents (Agent tool types)

| Agent | Purpose | Tools |
|---|---|---|
| `caveman:cavecrew-investigator` | Read-only code locator: "where is X", "what calls Y", dir maps. Compressed output, ~60% cheaper than Explore. Won't suggest fixes. | Read, Grep, Glob, Bash |
| `caveman:cavecrew-builder` | Surgical 1-2 file edits: typos, single-function rewrites, renames. Hard-refuses 3+ file scope. | Read, Edit, Write, Grep, Glob |
| `caveman:cavecrew-reviewer` | Diff/branch/file review. One line per finding, severity-tagged, no praise. | Read, Grep, Bash |
| `Explore` | Broad read-only fan-out search. Specify breadth: "medium" / "very thorough". Locates code, doesn't audit it. | read-only set |
| `Plan` | Software architect: implementation plans, critical files, trade-offs. | read-only set |
| `general-purpose` | Multi-step research, uncertain searches, complex tasks. | all |
| `claude` | Catch-all when nothing more specific fits. | all |
| `claude-code-guide` | Questions about Claude Code, Agent SDK, Claude API, Claude in Slack. | Bash, Read, WebFetch, WebSearch |
| `code-simplifier:code-simplifier` | Simplify/refine recently modified code, preserving behavior. | all |
| `statusline-setup` | Configure Claude Code status line. | Read, Edit |

## Plugins installed

- **caveman** — token-compression suite: `/caveman` (terse mode: lite/full/ultra), `/caveman-commit`, `/caveman-review`, `/caveman-compress` (compress memory files), `/caveman-stats` (real token usage), cavecrew subagents above.
- **superpowers** — process skills: brainstorming, test-driven-development, systematic-debugging, writing-plans, executing-plans, subagent-driven-development, dispatching-parallel-agents, using-git-worktrees, requesting/receiving-code-review, verification-before-completion, writing-skills.
- **claude-code-setup** — `claude-automation-recommender`: analyzes a codebase, recommends hooks/agents/skills/MCP. Run it once real projects exist here.
- **code-review** — `/code-review` for PRs and working diffs (levels low→max; `ultra` = paid multi-agent cloud review).
- **code-simplifier**, **frontend-design**, **github**, **chrome-devtools-mcp**, **clangd-lsp**, **swift-lsp**.

## Key built-in skills

- `/verify` — exercise a change end-to-end before committing nontrivial work.
- `/simplify` — reuse/simplification pass on changed code (no bug hunting).
- `/code-review` — bug hunting on the current diff.
- `/fewer-permission-prompts` — build an allowlist in `.claude/settings.json`.
- `deep-research` — fan-out web research with cited report.
- anthropic-skills: docx, xlsx, pptx, pdf, mcp-builder, skill-creator, theme-factory, schedule.

## MCP servers connected

- **Figma** (read designs, generate designs, Code Connect) + **Canva** (design/export/brand templates)
- **Gmail**, **Google Calendar**
- **Claude Browser** (in-app), **claude-in-chrome** (real Chrome, logged-in sessions), **Control Chrome**, **chrome-devtools** (debugging/performance), **computer-use** (native desktop apps)
- **Hugging Face** (hub search, papers, spaces; user `r0d0x`)
- **shadcn/ui** (components, blocks, themes), **mermaid** (diagram validation), **PowerPoint**, **pdf-viewer**
- **TurboTax**, **scheduled-tasks**, **mcp-registry** (find more connectors)

## Choosing between browser surfaces

1. Dedicated MCP for the app (Gmail, Calendar, Figma…) — fastest, most precise.
2. `claude-in-chrome` — needs your real logged-in sessions.
3. Claude Browser — default for general web work.
4. `computer-use` — native desktop apps only.
