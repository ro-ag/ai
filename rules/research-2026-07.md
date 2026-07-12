# Research digest — multi-vendor agent setups (2026-07-11)

Deep-research run: 107 agents, 5 search angles, 3-vote adversarial verification per claim. Findings below survived verification (vote counts noted). Full sources inline.

## What the evidence says about rules files

1. **Rules files help, but mostly via priming, not content** ([arXiv 2604.11088](https://arxiv.org/abs/2604.11088), 5,000+ Claude Code runs). Random community rule files improved performance exactly as much as expert-curated ones (+13.8pp over no-rules baseline). Lesson: don't over-polish rule prose for raw performance. (3-0)
2. **Guardrails beat guidance** (same study, per-rule ablations). Every individually beneficial rule was a NEGATIVE constraint: "do not refactor unrelated code" **+20.0pp**, "do not install new dependencies" +8.6pp, "do not modify unrelated files" +5.7pp. Every individually harmful rule was a positive directive: "follow code style" **−14.3pp**, "read test files" −14.3pp, "handle edge cases" −11.4pp, "preserve backward compatibility" −8.6pp (polarity split p=0.029). Lesson: write what agents must NOT do; delete style/edge-case directives. → Applied to our CLAUDE.md/AGENTS.md same day. (3-0)
3. **AGENTS.md is a cost/latency lever, not a proven quality lever** ([arXiv 2601.20404](https://arxiv.org/abs/2601.20404), 124 paired PR tasks, Codex): −28.6% median runtime, −16.6% median output tokens; quality gain not demonstrated. Keep it for efficiency — that's still money. (3-0 ×3)

## Cross-vendor orchestration landscape

4. **Our bridge pattern is the ToS-compliant standard**: spawning each vendor's official CLI binary under its own subscription auth, exactly like a human in a terminal — never OAuth-token extraction (account-ban territory). Independently documented in [all-agents-mcp](https://github.com/Dokkabei97/all-agents-mcp); PAL clink and claw-orchestrator use the same pattern. Validates rules/fleet.md bridges. (3-0)
5. **Skills-based direct CLI invocation is displacing MCP bridge servers** — all-agents-mcp lived 4 weeks, was archived, and its author merged it into Claude Code Skills, calling direct CLI + skills "the more practical and mainstream approach". Our second-opinion skill sits on the winning side of this shift. (2-1 / 3-0)
6. **Agent Skills = the cross-vendor packaging standard** ([agentskills.io](https://agentskills.io), open standard by Anthropic, 40+ clients incl. Codex, Gemini CLI, Cursor, Copilot, opencode). One skill format now serves our entire fleet — skills we write here can target all vendors. Source catalogs before hand-writing: [VoltAgent/awesome-agent-skills](https://github.com/VoltAgent/awesome-agent-skills) (~27.9k★, 1,497+ skills), [anthropics/skills](https://github.com/anthropics/skills), [microsoft/skills](https://github.com/microsoft/skills) (175), [trailofbits/skills](https://github.com/trailofbits/skills) (21 security-audit skills). (3-0 ×2)

## Orchestrator tools worth evaluating

| Tool | Stars | What | Fit |
|---|---|---|---|
| [PAL MCP Server](https://github.com/BeehiveInnovations/pal-mcp-server) (ex-Zen) | 11.7k | `clink` CLI-to-CLI bridge + `consensus` multi-model second opinions with stance steering (supportive/critical/neutral), codereview/precommit/debug tools | Maintained upgrade path for our hand-rolled bridges + second-opinion skill |
| [Claude Code Router](https://github.com/musistudio/claude-code-router) | 35.7k | Local gateway: one endpoint routes Claude Code/Codex/ZCode to any provider | Partial fit (no Cursor/Antigravity/Trae); interesting for GLM routing — ZCode is a named client |
| [claw-orchestrator](https://github.com/Enderfga/claw-orchestrator) | 525 | Persistent sessions over claude/codex/gemini/agy/cursor-agent/opencode (6 of our 8 vendors), multi-agent councils in git worktrees, plan→execute voting | Closest match to our exact stack; young (watch) |
| [ai-cli-mcp](https://github.com/mkXultra/ai-cli-mcp) | ~20 | Async fan-out: detached CLI processes + task registry (wait/peek/result) | Reference implementation only; runs CLIs with safety bypassed |

Caveat from verification: **no council/consensus tool has published output-quality benchmarks.** Multi-opinion review is plausible, unproven — treat as insurance, not magic.

## Cost routing

7. **Break-even routing gate** ([Triage, arXiv 2604.07494](https://arxiv.org/abs/2604.07494) — framework unvalidated, gate analytically sound): routing a task to a cheap tier pays off only if the cheap tier's expected pass rate on such tasks exceeds the inter-tier cost ratio. For us: send work to GLM/opencode only when expected pass rate beats their cost ratio vs premium (~20%-order for extreme tiers); combined with the escalation rule (mediocre → re-run smarter), this bounds waste in both directions. (3-0 ×3)
8. **No credible measured evidence exists on subscription-stacking economics or quota-management tooling.** Our fleet.md routing rests on first principles, and that's currently the state of the art. (verified absence)

## Refresh

Re-run this research ~quarterly or when adopting an orchestrator. Next candidates to trial hands-on: PAL `consensus` vs our second-opinion skill; claw councils for parallel builds.
