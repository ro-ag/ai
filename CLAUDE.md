# AI Workspace

Workspace for agent documentation, helpers, and small tools. These rules exist to get the best results from agents without wasting tokens.

Posture: **quality first** — use the best model for work that matters; save tokens by avoiding waste (repeated work, bloated context), not by downgrading quality. **Never use haiku, anywhere, for anything.** Reasoning effort stays at default unless the task needs deep reasoning.

## Rule files (read on demand — do not preload)

- `rules/git-workflow.md` — branch, land, and clean up; the detail behind the git hard rules
- `rules/subagents.md` — read BEFORE delegating work to any subagent
- `rules/releases.md` — read BEFORE any release, tag, or publish action
- `rules/github-actions.md` — read BEFORE creating, editing, or auditing any CI workflow
- `rules/local/` — machine-local, gitignored: `agents.md` (agent/skill/MCP inventory), `fleet.md` (subscriptions and task routing), `second-opinion.md` (cross-vendor review bridges)
- `skills/` — invocable procedures (memento, rust-gui-control), installed into each tool's skill dir; rules constrain, skills execute
- `AGENTS.md` — mirrors the hard rules for the non-Claude tools in the fleet; keep in sync with this file

## Token discipline

- Delegate broad searches and investigation to subagents; keep the main context for decisions. Default to read-only explorer/locator subagents that return conclusions, not file dumps.
- If exploration would take more than ~3 file reads or ~5 tool calls, delegate it instead of doing it inline.
- Batch independent tool calls in a single message so they run in parallel.
- Read only the line ranges you need from large files; never re-read files already in context.
- Keep this file under ~50 lines. Details belong in `rules/`, loaded on demand.

## Chat vs build

- Detect intent before acting: a question, an opinion request, thinking out loud, or a stream of ideas is a conversation, not a work order. Answer, discuss, wait. No branching, editing, or scaffolding until the user asks for the change or the idea is fully shaped.
- Rushing to code mid-discussion buries the user's next thought under diffs. Stay in the conversation while ideas keep coming; build when direction is confirmed.

## Hard rules

- Do not refactor code unrelated to the task. Do not modify unrelated files. Do not install new dependencies without explicit approval.
- No AI attribution anywhere, ever: no `Co-Authored-By`, no "Generated with …" in commits, PRs, or release notes.
- Always create a working branch before starting work. Never commit directly to `main`/`master`. Branches land via PR + squash merge: `gh pr merge --squash --delete-branch`. Never leave any branch but `main` in local or remote after merging.
- If the working directory has no git repository or no associated remote: stop and ask the user how to proceed before making changes.
- Never release, tag, push, or publish without an explicit user request in the current session.
- Releases publish via GitHub Actions on tag push ONLY — never locally (`cargo publish`, `npm publish`, `twine upload`, hand-run `gh release create`). Tag + changelog + README consistent, tests passing, before the release push.
- GitHub Actions only when explicitly asked, and only triggered on merge to `main` / release tags — never per-push or per-PR. Quality gates run locally before merge. When CI exists or is requested, enforce the cost rules in `rules/github-actions.md` (Linux-first, gated Windows/macOS, concurrency cancellation, path filters, caches, staged jobs).
- Each project lives in its own subdirectory. Add a project-level CLAUDE.md only when its rules differ from these.

## Memento — learn from mistakes

- Task start: `python3 ~/.agents/memento/memento.py check` and respect it. User correction / hard-won fix / ignored quality gate → `memento hit`; PROMOTE alert or "always/never" → `memento promote`. Protocol: `skills/memento/SKILL.md`.

## Language rules

- **Rust:** do not combine sources with tests — never put `#[cfg(test)] mod tests` blocks inside a source file. Go-style siblings: `module.rs` + `module_test.rs`, wired from the parent (`lib.rs`/`mod.rs`) with `#[cfg(test)] mod module_test;`.

## Memento-enforced

Rules promoted from the memento ledger. Details/fix: `memento show <slug>`.
- In uv-managed projects use uv run / uv add only — never bare python or pip; stdlib-only scripts (e.g. memento.py) run with plain python3 (memento: uv-not-python)
- Never ignore SonarQube gate findings — coverage, cognitive complexity, and code smells must be fixed before calling work done (memento: quality-gates-ignored)
- Visual-design agent prompts must carry measurable acceptance criteria (e.g. 'diff obvious in 2s side-by-side', 'gradient sweep >=50 levels'), never soft adjectives like 'restrained' or 'subtle polish' — those produce invisible changes the owner rejects (memento: design-agent-needs-measurable-boldness)
- Unsigned macOS debug binaries re-prompt keychain ACLs on every rebuild and block callers inside SecKeychainFindGenericPassword (masquerades as daemon/IPC hang) — sign dev binaries with a stable codesigning identity (memento: macos-dev-keychain-prompt-loop)
- A Tauri app binary built with plain cargo build --release keeps the dev context (loads devUrl, white window offline) — production binaries must be built through 'tauri build', including --no-bundle (memento: tauri-release-needs-cli-build)
- A merge is not landed until the main-branch CI run is green — check gh run list / pr checks after every squash-merge instead of reporting success from local gates alone (memento: verify-ci-after-merge)
- Never keep a live continuously-written binary DB (e.g. .ptrack/ptrack.redb) tracked in git — it permanently dirties the tree, breaks gh pr merge checkouts, ff pulls, and stash pops; and when untracking it, back the file up first because the merge checkout can delete the on-disk copy (memento: git-tracked-live-db)
- macOS login keychain that cannot auto-unlock returns errSecAuthFailed (-25293) on every write with NO permission prompt — masquerades as app-level 'native credential store unavailable'; it is not a signing or app bug (memento: macos-login-keychain-auth-failed)
- First keychain access from a freshly-linked signed macOS binary can take 1-5s (security server evaluates the whole binary's code signature); keychain-touching requests need generous deadlines or a startup warm-up, and 2s test deadlines on such paths are flaky by design (memento: keychain-first-access-signature-eval)
- On this machine ~/.cargo/config.toml sets build.target-dir=~/.cargo/shared-target for every project, so an agent worktree's cargo build relinks the SAME pam binary the main checkout is executing (AMFI stale-signature kills, 'daemon not ready' hangs, directory-lock stalls); every parallel worktree agent and every local test loop must set its own CARGO_TARGET_DIR (memento: shared-target-agent-worktree-relink)
- The first exec of a freshly linked large macOS binary (100 MB debug pam) stalls in _dyld_start for 5-30+ s (one-time per-inode executable assessment, worse under build load); every later launch is sub-second. Test harnesses that spawn a just-built binary must warm-exec it once (e.g. --version) OUTSIDE their readiness/deadline clocks instead of widening timeouts (memento: macos-first-exec-assessment-stall)

