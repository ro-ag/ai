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
