# GitHub Actions — cost rules

Private repos pay for runner minutes (2,000/mo free tier), billed roughly
**Linux 1x, Windows 2x, macOS 10x**. Every rule below follows from that.

## Default posture (hard rule)

- Never add or enable a workflow unless the user explicitly asked.
- Workflows trigger on merge to `main` or on release tags only — never on
  every push or PR update. Quality gates run locally (tests, lint, review)
  before merge instead.
- When the user does ask for CI (or a repo already has workflows), enforce
  everything below.
- Heavy or regular CI need → a self-hosted runner (free minutes, fine for own
  private repos) before paying for hosted minutes.

## Runner placement

- Lint, format/type checks, and platform-independent unit tests run on
  `ubuntu-latest` only. If a test calls no OS-specific API, it is portable —
  do not put it in a matrix.
- Windows jobs run on `pull_request` and pushes to `main` only. If a workflow
  also fires on other branches, gate the job:
  `if: github.event_name == 'pull_request' || github.ref == 'refs/heads/main'`
- macOS-only jobs (AppKit, UI tests, Xcode builds) run only on: push to
  `main`, nightly `schedule`, release tags/events, or a PR carrying an
  explicit approval signal (e.g. a `run-macos` label). Prefer the repo's
  existing approval mechanism if it has one.

## Waste elimination

- **Concurrency:** every PR-triggered workflow cancels superseded runs:
  `concurrency: { group: ${{ github.workflow }}-${{ github.ref }}, cancel-in-progress: true }`.
  Keep `cancel-in-progress: false` on `main`/release workflows so a release is
  never killed.
- **Path filters:** skip CI on irrelevant changes (`paths-ignore: ['**/*.md', 'docs/**']`,
  or scoped `paths:` in monorepos). Never filter release or nightly workflows —
  those must always run.
- **Timeouts:** every job sets `timeout-minutes` low enough that a hung job
  cannot burn an hour of minutes.
- **Caches:** every setup step caches dependencies — `setup-node` (`cache: npm`),
  `setup-python` (`cache: pip`/`poetry`), `setup-go` (on by default v5+),
  `setup-java` (`cache: maven`/`gradle`); `actions/cache` keyed on the lockfile
  for anything else.

## Staging

- Expensive runners never start before cheap validation passes: Windows/macOS
  jobs declare `needs:` on the Linux lint/unit jobs. `needs:` already skips on
  failure — no redundant `if: success()`.

## Auditing an existing workflow

Make the minimal diff that enforces these rules. Do not refactor unrelated
jobs, rename things, or reformat the file.
