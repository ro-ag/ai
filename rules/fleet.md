# Tool fleet — subscriptions and routing

Verified on this machine 2026-07-11. Goal: each tool does what it's best at; premium quotas (Claude, Codex) never burn on grunt work.

## Inventory

| Tool | Sub | CLI | Role |
|---|---|---|---|
| Claude Code | Max | `claude` | **Main brain.** Orchestration, design, hard implementation, reviews. Skills/subagents per this repo. |
| Codex CLI 0.142.5 | ChatGPT (logged in) | `codex` | Second opinion on hard bugs; parallel long autonomous runs; gnarly algorithmic work. |
| Antigravity 1.1.1 | Google Pro | `agy` | Huge-context repo sweeps, multimodal (design→code, screenshots), browser-verified frontend loops. |
| Gemini CLI 0.46.0 | Google Pro | `gemini` | Quick terminal one-shots; don't burn agent sessions on trivia. |
| Cursor | Pro | `cursor` | Interactive IDE: tab completion, visual multi-file review, human-steered edits. |
| zcode (GLM 5.2) | coding plan | ZCode.app / `~/.zcode/cli` | **Grunt volume.** Mass refactors, docstrings, test boilerplate, log analysis. Cheapest tokens. |
| opencode 1.17.7 | OpenCode Go | `opencode` | Terminal glue; parallel worker fleet; model-agnostic experiments. |
| Trae | Pro | `trae` | Overflow agent when others rate-limit; SOLO mode for small scoped features. |
| Copilot CLI 1.0.68 | GitHub | `copilot` | Ambient: editor autocomplete + independent PR review pass on GitHub. |

## Routing matrix

| Task | Primary | Fallback / second pass |
|---|---|---|
| Architecture, design, hard bugs | Claude Code | Codex (independent second opinion) |
| Big feature build | Claude Code (subagent-driven) | Cursor (interactive steer) |
| Mass mechanical edits, boilerplate | zcode GLM | opencode workers |
| Frontend with visual verification | Antigravity | Claude Code + Chrome MCP |
| Whole-repo analysis, giant context | Antigravity / Gemini (1M ctx) | Claude with subagent fan-out |
| Quick shell/API question | gemini or copilot CLI | — |
| PR review | Claude `/code-review` | + Copilot PR review (two independent reviewers) |
| Long unattended run | Codex cloud tasks | Claude background agents |

## Quota strategy

1. Grunt work NEVER touches Claude/Codex quotas — GLM and opencode first, always.
2. Rate-limited mid-task? Rotate to the tier-mate in the matrix, don't wait.
3. Second opinions are cheap insurance: a hard bug gets Claude AND Codex independently before any big rewrite.
4. Measure Claude spend with ccusage (see rules/tooling.md) before optimizing further.

## Cross-tool consistency

- `AGENTS.md` at repo root carries the shared hard rules — Codex, Cursor, Copilot, Antigravity, Trae, and opencode all read the AGENTS.md standard. Claude Code reads `CLAUDE.md`. **Both must stay in sync.**
- Same git law everywhere: branch-first, no AI attribution, no autonomous releases, consult if no repo/remote.
- This repo is the single source of truth for all fleet rules.
