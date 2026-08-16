# Changelog

All notable changes to this repo. Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/);
versioning: [SemVer](https://semver.org/) (pre-1.0: breaking changes allowed in MINOR, called out here).

## [Unreleased]

## [0.3.0] - 2026-08-16

The going-public release.

### Added
- `memento retire <slug>`: remove an obsolete rule from enforcement docs, keep
  ledger history; a later hit revives it to watching. Retired entries cost zero
  session tokens.
- Hit-shadow warning when a slug exists in both project and global ledgers.
- Wider `memento remind` correction signals ("i said", "once more", "we
  discussed", "not the first time").
- `rules/git-workflow.md`: branch/land/cleanup law extracted from the release
  rules — including Bitbucket remotes via `bkt` (bitbucket-cli).
- `skills/rust-gui-control/`: bundle, remote-control, and capture Rust GUI
  apps on macOS, as an installable skill.
- Chat-vs-build rule in the always-loaded core files: conversation is not a
  work order.
- MIT license; tag-triggered release workflow (the one standing CI use).

### Changed
- Repo reorganized into `skills/` (invocable procedures) and `rules/` (law);
  memento lives at `skills/memento/`, installer URLs updated.
- Machine-local content (tool inventories, subscriptions, review bridges)
  moved to gitignored `rules/local/` — personal data left the public tree.
- Memento install is curl-first now that the repo is public; `gh api` demoted
  to private-fork fallback.
- CI cost policy deduplicated: one copy in `rules/github-actions.md`, pointers
  elsewhere.

### Fixed
- Malformed `~/.agents/memento/config.json` no longer crashes the CLI.
- rulesync pointer BLOCK drift vs AGENTS.md hard rules.
- Lint debt: tz-aware hit dates, `re.IGNORECASE`, executable bit on
  `memento.py`.

## [0.2.0] - 2026-08-16

### Added
- Memento: cross-agent learn-from-mistakes skill — markdown ledger CLI
  (`hit` / `check` / `top` / `promote`), stdlib-only, with promote thresholds
  (3 hits or ≥30 min lost), `BOOTSTRAP.md` script embedding, per-tool install
  docs, and a curl/gh one-command installer.

## [0.1.0] - 2026-07-27

### Added
- Workspace rules: fleet routing, model policy, release laws, GitHub Actions
  cost rules, Rust sibling-test rule, second-opinion (stance-steered consensus)
  skill.
- rulesync: interactive rich CLI that pushes the rules-repo pointer block into
  every AI tool's global instructions file and forces Copilot's
  `includeCoAuthoredBy=false`.

[Unreleased]: https://github.com/ro-ag/ai/compare/v0.3.0...HEAD
[0.3.0]: https://github.com/ro-ag/ai/releases/tag/v0.3.0
[0.2.0]: https://github.com/ro-ag/ai/compare/eeb2264...f94b246
[0.1.0]: https://github.com/ro-ag/ai/compare/eeb2264...90fde10
