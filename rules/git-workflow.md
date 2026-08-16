# Git workflow

Applies to ALL work, not just releases. The condensed version lives in the
hard rules of `CLAUDE.md` / `AGENTS.md`; this is the detail.

## Branch flow

- Always create a working branch before starting work; never commit directly
  to `main`. Branches carry conventional prefixes: `feat/`, `fix/`, `chore/`,
  `docs/` — prefixes feed changelogs later.
- Land via **PR + squash merge**: `gh pr create` → local gates pass (tests,
  `/verify`, `/code-review`; Copilot reviews the PR free) →
  `gh pr merge --squash --delete-branch`.
- One PR = one squashed conventional commit on `main`. History reads like a
  changelog; any revert is a single commit.
- **Never leave branches other than `main` in local OR remote once merged.**
  `gh pr merge --squash --delete-branch` + `git fetch --prune` every time;
  `git branch -a` must show only `main` after landing. A branch that outlives
  a few days gets rebased on `main`.
- No git repository or no remote in the working directory → stop and consult
  the user before making changes.
- No AI attribution anywhere: commits, PR descriptions, release notes.

## Bitbucket remotes

Same law, different tooling: `gh` → `bkt`
([bitbucket-cli](https://github.com/avivsinai/bitbucket-cli), works on Cloud
and Data Center). Install if missing:
`brew install avivsinai/tap/bitbucket-cli`
(or `go install github.com/avivsinai/bitbucket-cli/cmd/bkt@latest`).
Auth once per host: `bkt auth login <url>` (`--kind cloud --web` for
bitbucket.org); headless/CI via `BKT_HOST` / `BKT_USERNAME` / `BKT_TOKEN`.

- Land: `bkt pr create --title "<conventional title>"` → gates pass →
  `bkt pr merge <id> --strategy squash`. Source branch closes on merge by
  default — the only-`main` hygiene holds; still `git fetch --prune` locally.
- Gate on CI before merging: `bkt pr checks <id> --wait`.
- Merge strategies are server-configured; if squash is unavailable, ask the
  user for the repo's strategy — never silently fast-forward.
- Scripting: use `--json` (+ `--jq`), never parse text output.
