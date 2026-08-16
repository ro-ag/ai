---
name: memento
description: Use when the user corrects a repeated behavior of any kind ("again?", "I told you", "how many times", "stop doing that"), when an approach fails repeatedly before a working fix is found (SSL/cert errors, build workarounds, flaky tooling), when a quality gate is skipped or ignored (coverage, cognitive complexity, code smells, lint), when discovering a project-specific way that works differently from the default — and at task start in any project, to load past lessons before choosing an approach.
---

# Memento

Agents have no long-term memory, so the rules that must never be forgotten get tattooed. The tattoos are ledgers (`MEMENTO.md`) owned by a small stdlib-only CLI that does all bookkeeping: recurrence counting, pain scoring, and automatic promotion of repeat offenders into enforced rules. Every repeated mistake burns tokens; this system makes each mistake billable once.

Works for Claude, Codex, Copilot, and Cursor — they all read the same ledgers and the same enforcement docs.

## The tool does the arithmetic — you do the judgment

Never hand-edit ledger entries, never count occurrences yourself. Call the CLI (stdlib only, no env needed):

```
python3 ~/.agents/memento/memento.py <cmd>
```

This skill ships as markdown only — the script travels in the Appendix below. If `~/.agents/memento/memento.py` is missing (first use on a machine), bootstrap: copy the Appendix code block verbatim to that path, then continue. (`uv run memento` also works inside `~/dev/ai`, where the canonical copy is developed and tested.)

## Protocol: CONSULT → LOG → PROMOTE

### 1. CONSULT (task start)

```
memento check
```

Run before choosing tools or approach in a project. ENFORCED entries are law. WATCHING entries are strong defaults — deviating from one without cause is how the mistake repeats. (In Claude Code a SessionStart hook can run this automatically — see README.)

### 2. LOG (on trigger)

Triggers — domain-agnostic, any of:

- the user corrects you, especially with repetition signals ("again", "I told you", "every time")
- an approach fails repeatedly before a fix finally works (log the fix — that is the valuable part)
- a quality gate is skipped or its findings ignored (coverage, complexity, smells, lint)
- you discover the way that actually works in this project, differing from the default

Check `memento list` for an existing slug first, then:

```
memento hit <slug> [--rule "..."] [--fix "..."] [--kind habit|trick|gate|project-way] \
                   [--scope global|project] [--cost MINUTES]
```

- Existing slug → date appended, count bumped. New slug → `--rule` required.
- `--rule`: one enforceable sentence. `--fix`: copy-pasteable command/env var/edit — "fixed the SSL issue" is useless next month.
- `--scope`: would the lesson apply in a different repo? yes → `global`, no → `project`.
- `--cost`: minutes lost this occurrence (feeds the pain ranking in `memento top`).

The CLI warns about similar existing slugs (reuse, don't duplicate) and prints a PROMOTE alert when a threshold is crossed (3 hits, or ≥30 min lost in one hit).

### 3. PROMOTE (automatic enforcement)

When the CLI prints a PROMOTE alert, or the user says "always" / "never":

```
memento promote <slug>
```

Writes the rule bullet into a dedicated `## Memento-enforced` section (never touches other sections): global scope → `~/dev/ai/AGENTS.md` + `CLAUDE.md`; project scope → the project's `AGENTS.md` (created if missing) + `CLAUDE.md` if present. The ledger entry keeps the history and the detailed fix; the enforcement doc gets only the rule.

## Scoring

`memento top` ranks all lessons by hits + total cost with last-hit date — the rate-of-issues view. No database needed; the ledger is the data.

## Common mistakes

| Mistake | Fix |
|---|---|
| Lesson only stated in the chat reply | Chat dies with the session. `memento hit` or it didn't happen. |
| Hand-editing MEMENTO.md / counting yourself | The CLI owns bookkeeping. Judgment (rule text, fix, scope) is yours; arithmetic is not. |
| Logging straight into CLAUDE.md/AGENTS.md | Those are enforcement docs, not history. `hit` first; `promote` when earned. |
| New slug per occurrence | `memento list` first; recurrence = same slug. Duplicates break the rate tracking. |
| Vague fix ("fixed certs") | Record the exact command/env var/edit that worked. |
| Skipping `memento check` at task start | That is precisely how mistakes repeat. |
| Promoting on first occurrence | One-offs pollute enforcement docs. Thresholds exist; user "always/never" overrides them. |

## Appendix — memento.py (bootstrap copy)

Canonical: `~/dev/ai/memento/memento.py`. This block must stay byte-identical (guarded by `memento_test.py`).

<!-- appendix-start -->
```python
#!/usr/bin/env python3
"""Memento — cross-agent mistake ledger.

Log repeated mistakes ("hits"), track recurrence and cost, and promote repeat
offenders into enforced rules in AGENTS.md / CLAUDE.md. Stdlib only.

Ledgers (markdown, owned by this script — do not hand-edit entry fields):
  global : ~/.agents/memento/MEMENTO.md   (override dir: MEMENTO_HOME)
  project: <git root>/MEMENTO.md

Enforcement docs for global-scope rules live in the AI workspace repo
(default ~/dev/ai, override: MEMENTO_AI_DIR).

Canonical copy: ~/dev/ai/memento/memento.py — the appendix in the sibling
SKILL.md must stay byte-identical (memento_test.py guards this). The skill
ships as markdown only; the runtime copy lives at ~/.agents/memento/memento.py,
bootstrapped from the appendix when missing.
"""

import argparse
import datetime
import json
import os
import re
import sys
from pathlib import Path

THRESHOLD = 3          # hits that trigger a promote alert
COST_TRIGGER = 30      # minutes lost in one hit that trigger a promote alert
SIGNALS = re.compile(r"again|told you|how many times|every time|stop doing|as always", re.I)
KINDS = ("habit", "trick", "gate", "project-way")
SECTION = "## Memento-enforced"
FIELDS = ("kind", "scope", "rule", "fix", "hits", "cost", "status")


def global_ledger() -> Path:
    return Path(os.environ.get("MEMENTO_HOME", "~/.agents/memento")).expanduser() / "MEMENTO.md"


def ai_dir() -> Path:
    return Path(os.environ.get("MEMENTO_AI_DIR", "~/dev/ai")).expanduser()


def project_root(start: str | None) -> Path | None:
    p = Path(start or ".").resolve()
    for d in (p, *p.parents):
        if (d / ".git").exists():
            return d
    return None


def new_entry(slug: str) -> dict:
    return {"slug": slug, "kind": "habit", "scope": "project", "rule": "",
            "fix": "", "hits": [], "cost": 0, "status": "watching"}


def parse(path: Path) -> dict:
    entries: dict[str, dict] = {}
    cur = None
    if not path.exists():
        return entries
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("## "):
            cur = new_entry(line[3:].strip())
            entries[cur["slug"]] = cur
        elif cur is not None and line.startswith("- ") and ": " in line:
            key, val = line[2:].split(": ", 1)
            key, val = key.strip(), val.strip()
            if key == "hits":
                cur["hits"] = [d.strip() for d in val.split(",") if d.strip()]
            elif key == "cost":
                cur["cost"] = int(val or 0)
            elif key in FIELDS:
                cur[key] = val
    return entries


def render(entries: dict, label: str) -> str:
    out = [f"# Memento ledger ({label})", "",
           "Managed by memento.py — log with `memento hit`, do not hand-edit entry fields.", ""]
    for e in entries.values():
        out += [f"## {e['slug']}"]
        out += [f"- {k}: {e[k]}" for k in ("kind", "scope", "rule", "fix")]
        out += [f"- hits: {', '.join(e['hits'])}",
                f"- cost: {e['cost']}",
                f"- status: {e['status']}", ""]
    return "\n".join(out) + "\n"


def save(path: Path, entries: dict, label: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render(entries, label), encoding="utf-8")


def ledgers(project: str | None) -> list[tuple[str, Path]]:
    out = []
    root = project_root(project)
    if root and root / "MEMENTO.md" != global_ledger():
        out.append(("project", root / "MEMENTO.md"))
    out.append(("global", global_ledger()))
    return out


def find(slug: str, project: str | None):
    for label, path in ledgers(project):
        entries = parse(path)
        if slug in entries:
            return label, path, entries
    return None


def merged(project: str | None) -> list[tuple[str, dict]]:
    return [(label, e) for label, path in ledgers(project) for e in parse(path).values()]


def similar(slug: str, project: str | None) -> list[str]:
    words = set(slug.split("-"))
    return [e["slug"] for _, e in merged(project)
            if e["slug"] != slug and words & set(e["slug"].split("-"))]


def append_rule(doc: Path, slug: str, rule: str) -> bool:
    """Idempotently add the rule bullet to doc's Memento-enforced section."""
    marker = f"(memento: {slug})"
    if doc.exists():
        lines = doc.read_text(encoding="utf-8").splitlines()
    else:
        lines = ["# Agent rules", ""]
    if any(marker in ln for ln in lines):
        return False
    if SECTION not in lines:
        lines += ["", SECTION, "",
                  "Rules promoted from the memento ledger. Details/fix: `memento show <slug>`.", ""]
    i = lines.index(SECTION) + 1
    while i < len(lines) and not lines[i].startswith("## "):
        i += 1
    while i > 0 and lines[i - 1] == "":
        i -= 1
    lines.insert(i, f"- {rule} {marker}")
    doc.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return True


def cmd_hit(args) -> None:
    hit_cost = args.cost or 0
    found = find(args.slug, args.project)
    if found is None:
        sim = similar(args.slug, args.project)
        if sim:
            print(f"note: similar existing slugs: {', '.join(sim)} — reuse one if it is the same lesson")
        if not args.rule:
            sys.exit(f"new entry '{args.slug}' needs --rule (one enforceable sentence)")
        avail = dict(ledgers(args.project))
        scope = args.scope or ("project" if "project" in avail else "global")
        if scope not in avail:
            sys.exit(f"scope '{scope}' unavailable here (no git project root found)")
        path = avail[scope]
        entries = parse(path)
        entries[args.slug] = new_entry(args.slug) | {"scope": scope, "kind": args.kind or "habit"}
        found = (scope, path, entries)
    label, path, entries = found
    e = entries[args.slug]
    e["hits"].append(datetime.date.today().isoformat())
    e["cost"] += hit_cost
    if args.rule:
        e["rule"] = args.rule
    if args.fix:
        e["fix"] = args.fix
    if args.kind:
        e["kind"] = args.kind
    save(path, entries, label)
    n = len(e["hits"])
    print(f"{e['slug']}: hit #{n} logged in {label} ledger ({path})")
    if e["status"] == "watching" and (n >= THRESHOLD or hit_cost >= COST_TRIGGER):
        why = f"{n} hits" if n >= THRESHOLD else f"cost {hit_cost}min"
        print(f"PROMOTE ({why}): run `memento promote {e['slug']}`")


def cmd_check(args) -> None:
    rows = merged(args.project)
    if not rows:
        print("memento: no lessons recorded yet")
        return
    enforced = [(l, e) for l, e in rows if e["status"] != "watching"]
    watching = [(l, e) for l, e in rows if e["status"] == "watching"]
    if enforced:
        print("ENFORCED (law):")
        for label, e in enforced:
            fix = f"  [fix: {e['fix']}]" if e["fix"] else ""
            print(f"- ({label}) {e['rule']}{fix}")
    if watching:
        print("WATCHING (strong defaults — deviating repeats the mistake):")
        for label, e in watching:
            fix = f"  [fix: {e['fix']}]" if e["fix"] else ""
            print(f"- ({label}) {e['rule']} (hits: {len(e['hits'])}){fix}")


def cmd_top(args) -> None:
    rows = sorted(merged(args.project),
                  key=lambda r: (len(r[1]["hits"]), r[1]["cost"]), reverse=True)
    if not rows:
        print("memento: no lessons recorded yet")
        return
    print(f"{'slug':30} {'hits':>4} {'cost':>5} {'last hit':10} {'scope':7} status")
    for label, e in rows:
        last = e["hits"][-1] if e["hits"] else "-"
        print(f"{e['slug']:30} {len(e['hits']):>4} {e['cost']:>4}m {last:10} {label:7} {e['status']}")


def cmd_list(args) -> None:
    for label, e in merged(args.project):
        print(f"{e['slug']} ({label}): {e['rule']}")


def cmd_show(args) -> None:
    found = find(args.slug, args.project)
    if found is None:
        sys.exit(f"unknown slug: {args.slug}")
    _, _, entries = found
    e = entries[args.slug]
    for k in ("slug", "kind", "scope", "rule", "fix", "cost", "status"):
        print(f"{k}: {e[k]}")
    print(f"hits ({len(e['hits'])}): {', '.join(e['hits'])}")


def cmd_promote(args) -> None:
    found = find(args.slug, args.project)
    if found is None:
        sys.exit(f"unknown slug: {args.slug}")
    label, path, entries = found
    e = entries[args.slug]
    base = ai_dir() if e["scope"] == "global" else project_root(args.project)
    if base is None:
        sys.exit("no project root found for project-scope promote")
    targets = [base / "AGENTS.md"]
    if (base / "CLAUDE.md").exists():
        targets.append(base / "CLAUDE.md")
    for t in targets:
        added = append_rule(t, e["slug"], e["rule"])
        print(f"{'rule added to' if added else 'already in'} {t}")
    e["status"] = f"enforced -> {targets[0]}"
    save(path, entries, label)
    print(f"{e['slug']}: status enforced")


def cmd_remind(args) -> None:
    """UserPromptSubmit hook: stdin = hook JSON; nudge if the prompt smells like a repeated correction."""
    try:
        prompt = json.load(sys.stdin).get("prompt", "")
    except (json.JSONDecodeError, UnicodeDecodeError):
        prompt = ""
    if SIGNALS.search(prompt):
        print("memento: possible repeated correction — log it with `memento hit <slug>` (memento skill)")


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(prog="memento", description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("hit", help="log an occurrence (creates the entry on first hit)")
    p.add_argument("slug")
    p.add_argument("--rule", help="one enforceable sentence (required for new entries)")
    p.add_argument("--fix", help="copy-pasteable command/env var/edit that works")
    p.add_argument("--kind", choices=KINDS)
    p.add_argument("--scope", choices=("global", "project"))
    p.add_argument("--cost", type=int, help="minutes lost this occurrence")
    p.set_defaults(fn=cmd_hit)

    for name, fn, help_ in (("check", cmd_check, "CONSULT output for task start"),
                            ("top", cmd_top, "entries ranked by hits + cost"),
                            ("list", cmd_list, "one line per entry"),
                            ("remind", cmd_remind, "hook helper: nudge on correction signals (stdin JSON)")):
        p = sub.add_parser(name, help=help_)
        p.set_defaults(fn=fn)

    for name, fn, help_ in (("show", cmd_show, "full entry with fix details"),
                            ("promote", cmd_promote, "enforce: write rule into AGENTS.md/CLAUDE.md")):
        p = sub.add_parser(name, help=help_)
        p.add_argument("slug")
        p.set_defaults(fn=fn)

    for p in sub.choices.values():
        p.add_argument("--project", help="path inside the project (default: cwd)")

    args = ap.parse_args(argv)
    args.fn(args)


if __name__ == "__main__":
    main()
```
<!-- appendix-end -->
