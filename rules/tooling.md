# Ecosystem tools — scouted 2026-07-11

Candidate tools for better agent results + less token waste. Nothing gets installed without an explicit user request; status tracks where each stands.

## Shortlist (verified, with sources)

| Tool | Category | What it does | Install | Status |
|---|---|---|---|---|
| [SkillOpt](https://github.com/microsoft/SkillOpt) | Skill optimizer | Trains/auto-improves skill docs: optimizer model turns scored rollouts into add/delete/replace edits, accepted only if held-out validation improves. Native Claude Code backend (`claude_code_exec`); MS reports +19.1 pts avg accuracy. Emits compact `best_skill.md` (300–2K tokens). v0.2.0 adds `skillopt-sleep` nightly self-evolution. | `uv tool install skillopt` | **adopted** (sleep, manual cycle — see below) |
| [ccusage](https://github.com/ryoppippi/ccusage) | Token tracking | Daily/monthly/session/5h-block token+cost reports from local JSONL; live dashboard. 17.1k stars, very active. | `npx ccusage@latest` | evaluate |
| [promptfoo — test-agent-skills](https://www.promptfoo.dev/docs/guides/test-agent-skills/) | Skill eval harness | Regression-tests SKILL.md files via headless Claude Code runs; `skill-used` assertion proves a skill actually triggers instead of dead-weighting context. | `npx promptfoo@latest` | evaluate |
| [claudelint](https://github.com/pdugan20/claudelint) | Config linter | 114 rules: CLAUDE.md size/bloat, circular imports, dangerous skill commands, hooks/MCP/agent config. Auto-fix plugin. Pre-1.0. | `npm i claude-code-lint` | evaluate |
| [cclint](https://github.com/carlrannaberg/cclint) | Config linter | Validates agent/command frontmatter, settings.json hooks, CLAUDE.md structure. Smaller than claudelint. | `npm i -g @carlrannaberg/cclint` | backup option |
| [claude-plugins-community](https://github.com/anthropics/claude-plugins-community) | Marketplace | Official Anthropic community marketplace, security-scanned. | `claude plugin marketplace add anthropics/claude-plugins-community` | evaluate |
| [skills-optimizer](https://github.com/claude-world/skills-optimizer) | Skill compression | LLM-verified semantic compression of `.claude/` skills (claims 6:1, verify-compress-reverify loop). 6 stars — niche, inspect before use. | git clone | watch |
| [Claude Code Usage Monitor](https://github.com/Maciek-roboblog/Claude-Code-Usage-Monitor) | Token tracking | Real-time monitor with predictions/warnings. Unverified depth — ccusage first. | pip/uv | watch |

Skipped on purpose: DSPy (generic prompt optimization — SkillOpt covers the skill niche with a real Claude Code harness), tonsofskills/ccpi mega-marketplace (unvetted, 2,810 skills — official marketplace is the safer source).

## Adoption order (quality-first, waste-reduction)

1. **ccusage** — measure before optimizing. Find where tokens actually go per session/model.
2. **claudelint** — catch CLAUDE.md bloat and misconfig that silently burns input tokens every session.
3. **SkillOpt** — once we have custom skills worth training; improves quality AND compresses at the same time.
4. **promptfoo** — regression harness when this repo's rules/skills are stable enough to protect.

## SkillOpt-Sleep — installed and verified 2026-07-11

Nightly self-evolution for Claude Code: harvests session transcripts → mines recurring tasks → replays offline → proposes bounded skill/memory edits **behind a held-out validation gate**, staged for human review. Preview software; interfaces may change.

Installed via `uv tool install skillopt` (binaries: `skillopt-sleep`, `skillopt-train`, `skillopt-eval`). Verified on this machine:
- Deterministic keyless proof PASSed (consolidation improves held-out score; gate blocks harmful edits).
- Real dry-run: harvested 110 sessions → mined 40 recurring tasks → gate correctly **rejected** the night's proposal (no checkable correctness signal in docs-only sessions). Expected per docs: gains only where tasks recur with verifiable outcomes.

Usage (from the project dir):
- `skillopt-sleep dry-run` — report only, changes nothing
- `skillopt-sleep run` → `status` → `adopt` — full cycle, human adopts staged proposal
- `skillopt-sleep schedule` / `unschedule` — nightly cron (NOT enabled; needs explicit user decision — burns replay quota nightly)

Policy: proposals are never auto-adopted; review staged diffs before `adopt`. Revisit `skillopt-train` (full optimizer loop) when we have a skill with a scoreable task set — their protocol uses an API optimizer model, so check auth needs then.

## PAL consensus — trialed and decided 2026-07-11

**Skip installing PAL; its best idea adopted instead.** Findings from hands-on evaluation:
- PAL `consensus` consults model APIs → needs API keys (GEMINI/OPENAI/XAI). This machine is subscription-only, zero keys — consensus would open a pay-per-token channel, against the quota strategy.
- PAL `clink` (the keyless CLI bridge) ships with `--yolo` / `--dangerously-bypass-approvals-and-sandbox` defaults — violates our hard rules out of the box. And it duplicates our bridges.
- **Adopted: stance steering** (critical / supportive / neutral reviewers) into the `second-opinion` skill. Live 3-vendor trial ran on subscriptions at zero marginal cost: Codex (critical) + Grok (neutral) + Gemini-via-agy (supportive) → unanimous verdict, three distinct failure modes surfaced. Pattern works without PAL.
- Revisit PAL only if we ever hold API keys or need its threaded multi-tool workflows.

## Skills policy (3-vendor consensus, unanimous)

Hybrid: **"must never" → always-loaded law files (AGENTS.md/CLAUDE.md); "when X, do these steps" → skill; reference/rationale → plain markdown in rules/.** Never wholesale-convert docs to skills — always-on constraints can't live in on-demand packages, and reference docs churn too fast for skill ceremony. Next skill candidate when needed: the release ritual (`rules/releases.md` flow).

## Orchestrators + skills catalogs (deep-research 2026-07-11)

Cross-vendor orchestrators (PAL MCP, Claude Code Router, claw-orchestrator) and skills catalogs (VoltAgent, anthropics/skills, trailofbits security skills) — full evaluated table with fit notes lives in `rules/research-2026-07.md`. Skills format is now a cross-vendor standard: skills written here serve the whole fleet.

Refresh this scout when adopting anything or ~quarterly. Sources verified 2026-07-11 via web (MS Research blog, GitHub, PyPI, ccusage.com).
