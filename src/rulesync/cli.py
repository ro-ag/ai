"""rulesync CLI — rich guided flow: status → select → preview → confirm → apply."""

from __future__ import annotations

import argparse
import sys

from rich import box
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Confirm, Prompt
from rich.table import Table
from rich.theme import Theme

from .core import (
    PlannedChange,
    apply_plan,
    build_block,
    default_tools,
    make_plan,
    repo_root,
)

THEME = Theme(
    {
        "accent": "bold cyan",
        "ok": "green",
        "pending": "yellow",
        "err": "bold red",
        "muted": "grey58",
    }
)

# action -> (label shown in tables, theme style)
ACTION_STYLE: dict[str, tuple[str, str]] = {
    "up to date": ("synced", "ok"),
    "create": ("create", "pending"),
    "append block": ("append block", "pending"),
    "replace block": ("replace block", "pending"),
    "set false": ("set includeCoAuthoredBy=false", "pending"),
    "skip": ("not installed", "muted"),
    "manual": ("MANUAL", "err"),
}


def _interactive_session() -> bool:
    return sys.stdin.isatty() and sys.stdout.isatty()


def parse_selection(
    raw: str, actionable_rows: dict[int, PlannedChange]
) -> list[PlannedChange] | None:
    """Turn user input into a plan list. None means invalid — re-prompt."""
    answer = raw.strip().lower()
    if answer in {"", "a", "all"}:
        return list(actionable_rows.values())
    if answer in {"n", "none"}:
        return []
    try:
        numbers = [int(part) for part in answer.replace(",", " ").split()]
    except ValueError:
        return None
    if not numbers or any(n not in actionable_rows for n in numbers):
        return None
    return [actionable_rows[n] for n in dict.fromkeys(numbers)]


def render_header(console: Console, repo, mode: str) -> None:
    console.print(
        Panel.fit(
            f"[accent]rulesync[/] [muted]·[/] {repo}\n[muted]mode:[/] {mode}",
            title="⚡ rules repo pointer",
            title_align="left",
            border_style="accent",
            box=box.ROUNDED,
        )
    )


def render_status(
    console: Console, plans: list[PlannedChange]
) -> dict[int, PlannedChange]:
    table = Table(
        box=box.ROUNDED,
        border_style="muted",
        header_style="accent",
        padding=(0, 1),
    )
    table.add_column("#", justify="right", style="muted")
    table.add_column("tool", style="accent")
    table.add_column("state")
    table.add_column("confidence", style="muted")
    table.add_column("path", style="muted", overflow="fold")
    table.add_column("note", style="muted", max_width=44)

    rows: dict[int, PlannedChange] = {}
    for planned in plans:
        label, style = ACTION_STYLE[planned.action]
        number = ""
        if planned.actionable:
            number = str(len(rows) + 1)
            rows[len(rows) + 1] = planned
        table.add_row(
            number,
            planned.tool.name,
            f"[{style}]{label}[/]",
            planned.tool.confidence,
            str(planned.tool.path),
            planned.detail or planned.tool.note,
        )
    console.print(table)
    return rows


def render_preview(
    console: Console, block: str, selected: list[PlannedChange]
) -> None:
    if any(planned.tool.kind == "rules" for planned in selected):
        console.print(
            Panel(
                Markdown(block),
                title="pointer block",
                border_style="muted",
                box=box.ROUNDED,
            )
        )
    lines = "\n".join(
        f"[accent]{planned.tool.name}[/] → [pending]{ACTION_STYLE[planned.action][0]}[/]"
        for planned in selected
    )
    console.print(
        Panel(
            lines,
            title=f"pending changes ({len(selected)})",
            border_style="pending",
            box=box.ROUNDED,
        )
    )


def prompt_selection(
    console: Console, actionable_rows: dict[int, PlannedChange]
) -> list[PlannedChange]:
    while True:
        raw = Prompt.ask(
            "Sync which? [accent]a[/]ll · [accent]n[/]one · row numbers (e.g. 1,3)",
            default="a",
            console=console,
        )
        selected = parse_selection(raw, actionable_rows)
        if selected is not None:
            return selected
        valid = ", ".join(str(n) for n in actionable_rows)
        console.print(f"[err]invalid selection[/] — pick from: {valid}, 'a', or 'n'")


def apply_selected(
    console: Console, selected: list[PlannedChange]
) -> list[tuple[PlannedChange, str | None]]:
    results: list[tuple[PlannedChange, str | None]] = []
    with Progress(
        SpinnerColumn(style="accent"),
        TextColumn("[progress.description]{task.description}"),
        console=console,
        transient=True,
    ) as progress:
        for planned in selected:
            task = progress.add_task(f"writing {planned.tool.name}…", total=None)
            try:
                apply_plan(planned)
                results.append((planned, None))
            except OSError as exc:
                results.append((planned, str(exc)))
            progress.remove_task(task)
    return results


def render_results(
    console: Console, results: list[tuple[PlannedChange, str | None]]
) -> int:
    table = Table(box=box.ROUNDED, border_style="muted", header_style="accent")
    table.add_column("tool", style="accent")
    table.add_column("result")
    errors = 0
    for planned, error in results:
        if error is None:
            table.add_row(
                planned.tool.name, f"[ok]wrote ({ACTION_STYLE[planned.action][0]})[/]"
            )
        else:
            errors += 1
            table.add_row(planned.tool.name, f"[err]{error}[/]")
    console.print(table)
    applied = len(results) - errors
    style = "err" if errors else "ok"
    console.print(
        Panel.fit(
            f"[{style}]{applied} applied · {errors} error(s)[/]",
            border_style=style,
            box=box.ROUNDED,
        )
    )
    return 1 if errors else 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="rulesync", description=__doc__)
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="show status and pending changes; write nothing",
    )
    parser.add_argument(
        "--yes",
        "-y",
        action="store_true",
        help="apply all pending changes without prompting",
    )
    parser.add_argument(
        "--tool",
        action="append",
        metavar="NAME",
        help="limit to the named tool; repeatable",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    console = Console(theme=THEME)

    repo = repo_root()
    block = build_block(repo)
    tools = default_tools()

    if args.tool:
        known = {tool.name for tool in tools}
        unknown = sorted(set(args.tool) - known)
        if unknown:
            console.print(
                f"[err]unknown tool(s): {', '.join(unknown)}[/] — "
                f"known: {', '.join(sorted(known))}"
            )
            return 2
        wanted = set(args.tool)
        tools = [tool for tool in tools if tool.name in wanted]

    interactive = _interactive_session() and not args.yes and not args.dry_run
    dry_run = args.dry_run or (not args.yes and not interactive)
    mode = "dry-run" if dry_run else ("apply all" if args.yes else "interactive")

    render_header(console, repo, mode)
    plans = [make_plan(tool, block) for tool in tools]
    actionable_rows = render_status(console, plans)

    if not actionable_rows:
        console.print("[ok]✓ everything synced — nothing to do[/]")
        return 0

    if dry_run:
        render_preview(console, block, list(actionable_rows.values()))
        console.print(
            f"[muted]{len(actionable_rows)} pending change(s); "
            f"re-run without --dry-run to apply[/]"
        )
        return 0

    if args.yes:
        selected = list(actionable_rows.values())
        render_preview(console, block, selected)
    else:
        selected = prompt_selection(console, actionable_rows)
        if not selected:
            console.print("[muted]nothing selected — aborted[/]")
            return 0
        render_preview(console, block, selected)
        if not Confirm.ask(
            f"Apply {len(selected)} change(s)?", default=True, console=console
        ):
            console.print("[muted]aborted[/]")
            return 0

    results = apply_selected(console, selected)
    return render_results(console, results)


if __name__ == "__main__":
    sys.exit(main())
