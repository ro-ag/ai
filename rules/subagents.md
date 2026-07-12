# Working with subagents

How to delegate so the main context stays small and cheap. Full inventory of what exists: `rules/agents.md`.

## Decision table

| Task | Use |
|---|---|
| "Where is X defined / what calls Y / map this dir" | `caveman:cavecrew-investigator` — read-only locator, compressed output (~60% fewer tokens than Explore) |
| Bounded 1-2 file edit (typo, rename, single-function rewrite) | `caveman:cavecrew-builder` — refuses 3+ file scope by design |
| Review a diff, branch, or file | `caveman:cavecrew-reviewer`, or `/code-review` skill for the working diff |
| Broad read-only exploration, many files/conventions | `Explore` — state breadth explicitly: "medium" or "very thorough" |
| Design an implementation plan | `Plan` |
| Multi-step research, uncertain searches | `general-purpose` |
| Questions about Claude Code / Agent SDK / Claude API | `claude-code-guide` |
| Simplify recently changed code | `code-simplifier:code-simplifier` |
| Anything else | `claude` (catch-all) |

## Rules

1. **Self-contained prompts.** Subagents see none of the conversation. Include file paths, context, constraints, and the expected output format.
2. **Ask for terse, structured returns** (tables, `file:line` lists). The agent's final message is the only thing the main context pays for.
3. **Parallelize.** Independent tasks → launch all agents in ONE message so they run concurrently.
4. **Continue, don't respawn.** Use SendMessage with the agent's ID to follow up with context intact; a new Agent call starts from zero.
5. **Don't duplicate delegated work.** Once a search is delegated, wait for the result instead of also searching inline.
6. **Model override — quality first.** Default: omit, inherit the session model. **NEVER use haiku — no exceptions**, not even for mechanical fan-out; grunt volume belongs to the GLM/opencode fleet instead (`rules/fleet.md`). Never downgrade analysis, review, or planning agents.
7. **Reasoning effort:** leave at default. Pass `effort: 'high'` only when the task genuinely needs deep reasoning — hard debugging, architecture, adversarial verification. **Never `xhigh`/`max` by default** — they cause over-reasoning loops and cost without quality gains; reserve for explicit user request.
8. **Worktree isolation** only when agents mutate files in parallel — it costs setup time and disk.
9. **Workflow tool** (multi-agent orchestration, can spawn dozens of agents) only on explicit user opt-in: "use a workflow" / "ultracode". Division of labor: **subagents** for simple parallel fan-out (analyze N files), **workflows** for deterministic multi-stage programs needing checkpoints.
10. **Post-mortem loop.** When an agent fails or misbehaves: ask it what went wrong and how to prevent it, then fold the insight into these rules or the relevant skill. Rules are living documents.

## Token economics

A subagent burns its own context window and returns one summary — the main thread pays only for the prompt and the result. Exploration is the biggest context killer in long sessions: push it down into agents early, before the main context bloats, not after.

Posture is **quality first**: savings come from not repeating work and keeping the main context lean — never from downgrading model quality on work that matters.
