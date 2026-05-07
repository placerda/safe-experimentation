"""Rich UI components for the SAFE demo."""
from __future__ import annotations

from typing import Iterable, List

from rich.align import Align
from rich.console import Console, Group
from rich.panel import Panel
from rich.text import Text

from .scenario import Principle, Scenario

PRINCIPLE_META = {
    "scope":       ("🛡️  Scope",             "magenta"),
    "anchored":    ("⚓ Anchored Decisions",  "blue"),
    "flow":        ("🔀 Flow Integrity",      "yellow"),
    "escalation":  ("📣 Escalation",          "red"),
}

BASELINE_STYLE = "red"
SAFE_STYLE = "green"
CUSTOMER_STYLE = "cyan"


def make_console() -> Console:
    return Console(highlight=False)


def header_panel(scenario: Scenario) -> Panel:
    legend = Text()
    for i, key in enumerate(["scope", "anchored", "flow", "escalation"]):
        label, color = PRINCIPLE_META[key]
        legend.append(label, style=f"bold {color}")
        if i < 3:
            legend.append("   ")
    body = Group(
        Align.center(Text(scenario.title, style="bold white")),
        Align.center(Text(scenario.subtitle, style="dim")),
        Text(""),
        Align.center(legend),
    )
    return Panel(body, border_style="white", title="SAFE Framework — Live Demo",
                 title_align="left", padding=(1, 2))


def customer_panel(name: str, message: str, turn_no: int, total: int) -> Panel:
    return Panel(
        Text(message, style="white"),
        title=f"[bold cyan]{name}[/]   [dim]turn {turn_no}/{total}[/]",
        title_align="left",
        border_style=CUSTOMER_STYLE,
        padding=(0, 2),
    )


def _badges(principles: Iterable[Principle]) -> Text:
    line = Text()
    items = list(principles)
    for i, p in enumerate(items):
        label, color = PRINCIPLE_META[p]
        line.append(f" {label} ", style=f"bold white on {color}")
        if i < len(items) - 1:
            line.append("  ")
    return line


def baseline_panel(label: str, reply: str) -> Panel:
    body = Group(
        Text(reply, style="white"),
        Text(""),
        Text(" ⚠ no SAFE checks ", style="bold white on red"),
    )
    return Panel(
        body,
        title=f"[bold red]{label}[/]   [dim](task-completion only)[/]",
        title_align="left",
        border_style=BASELINE_STYLE,
        padding=(1, 2),
    )


def safe_panel(label: str, reply: str, principles: List[Principle]) -> Panel:
    badges = _badges(principles) if principles else Text(" — ", style="dim")
    body = Group(
        Text(reply, style="white"),
        Text(""),
        badges,
    )
    return Panel(
        body,
        title=f"[bold green]{label}[/]   [dim](SAFE-aware)[/]",
        title_align="left",
        border_style=SAFE_STYLE,
        padding=(1, 2),
    )


def explanations_panel(explanations: dict[Principle, str]) -> Panel:
    if not explanations:
        body: Group = Group(Text("No SAFE principle triggered this turn.", style="dim"))
    else:
        lines: list[Text] = []
        for p, text in explanations.items():
            label, color = PRINCIPLE_META[p]
            line = Text()
            line.append(f"{label}  ", style=f"bold {color}")
            line.append(text, style="white")
            lines.append(line)
        body = Group(*lines)
    return Panel(body, title="[bold]Why this matters[/]", title_align="left",
                 border_style="grey50", padding=(0, 2))


def closing_panel(scenario: Scenario) -> Panel:
    baseline = Text()
    baseline.append("Baseline outcome\n", style="bold red")
    baseline.append(scenario.closing.baseline, style="white")

    safe = Text()
    safe.append("\n\nSAFE-aware outcome\n", style="bold green")
    safe.append(scenario.closing.safe, style="white")

    body = Group(baseline, safe)
    return Panel(body, title="[bold]Outcome contrast[/]", border_style="white",
                 padding=(1, 2))
