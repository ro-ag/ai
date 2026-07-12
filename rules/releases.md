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

## Package registries (npm, PyPI, crates.io, Homebrew…)

- Publish from CI on tag push — never from a laptop. Reproducible builds, no local credentials.
- Prefer OIDC "trusted publishing" (PyPI, npm provenance, crates.io tokens scoped per-repo) over long-lived tokens in secrets.
- The GitHub release and the registry publish come from the same tag — one version, one source of truth.
- Dry-run first when the ecosystem supports it (`npm publish --dry-run`, `cargo publish --dry-run`, `twine check`).

## Hotfixes

Branch from the released tag (`hotfix/vX.Y.Z+1`), fix, PATCH bump, same flow, merge back to `main`.

## What never goes out

- Secrets, `.env` files, tokens, local paths in release artifacts.
- Attribution lines ("Generated with Claude", `Co-Authored-By`) in commits, tags, or notes.
- A release from a dirty tree or with skipped tests, no matter how small the change.
