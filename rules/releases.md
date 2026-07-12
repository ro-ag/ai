# Release rules

Agents NEVER release autonomously. Every release starts with an explicit user request in the current session. "Fix this bug" does not imply "and release it".

## Preconditions (all required)

1. Clean working tree (`git status`), on the release branch (default: `main`).
2. Tests pass — run the project's test command and show real output. No green claim without evidence.
3. Runtime changes verified end-to-end (`/verify` skill or manually driving the affected flow), not just typecheck.
4. `CHANGELOG.md` updated (Keep a Changelog format) as part of the release commit.

## Versioning

- Semver: MAJOR = breaking, MINOR = feature, PATCH = fix.
- Pre-1.0: breaking changes allowed in MINOR, but must be called out explicitly in the changelog.

## Flow

1. Bump version in the project manifest + update `CHANGELOG.md`.
2. Commit: `release: vX.Y.Z` — no attribution trailers, ever.
3. Annotated tag: `git tag -a vX.Y.Z -m "vX.Y.Z"`.
4. Confirm with the user, then: `git push && git push --tags`.
5. GitHub release: `gh release create vX.Y.Z --title "vX.Y.Z" --notes-file <notes>` — notes taken from the changelog section. No AI attribution in notes.

## CI cost policy (GitHub Actions on private repos)

Actions minutes are paid on private repos (2,000/mo free tier; macOS runners burn a 10× multiplier). Therefore:

- **No workflows unless the user explicitly asks.** Default quality gates are local: tests + `/verify` + `/code-review` + Copilot PR review (Copilot review is subscription-included, not Actions minutes).
- When a workflow is justified, triggers are merge/tag only: `on: push: branches: [main]` and `on: push: tags: ['v*']`. Never `pull_request` or per-push on feature branches.
- Workflow hygiene: `ubuntu-latest` runners only (never macOS unless the build requires it), `timeout-minutes` set low, `concurrency` with `cancel-in-progress`, path filters to skip doc-only changes.
- Heavy/regular CI need later → self-hosted runner on this Mac (free minutes, fine for own private repos) before paying for hosted minutes.

## Package registries (npm, PyPI, crates.io, Homebrew…)

- Publish from CI on tag push — never from a laptop. Reproducible builds, no local credentials. This is the one standing Actions use, and it satisfies the cost policy: tags only happen on explicit release requests, so runs are rare and short.
- Prefer OIDC "trusted publishing" (PyPI, npm provenance, crates.io tokens scoped per-repo) over long-lived tokens in secrets.
- The GitHub release and the registry publish come from the same tag — one version, one source of truth.
- Dry-run first when the ecosystem supports it (`npm publish --dry-run`, `cargo publish --dry-run`, `twine check`).

## Hotfixes

Branch from the released tag (`hotfix/vX.Y.Z+1`), fix, PATCH bump, same flow, merge back to `main`.

## What never goes out

- Secrets, `.env` files, tokens, local paths in release artifacts.
- Attribution lines ("Generated with Claude", `Co-Authored-By`) in commits, tags, or notes.
- A release from a dirty tree or with skipped tests, no matter how small the change.
