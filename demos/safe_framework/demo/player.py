"""Turn-by-turn playback controller for the SAFE demo."""
from __future__ import annotations

import time
from typing import Optional

from rich.columns import Columns
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from . import ui
from .scenario import Scenario


def _wait_for_enter(console: Console, prompt: str = "Press Enter to continue…") -> None:
    console.print()
    console.print(Text(prompt, style="dim italic"))
    try:
        input()
    except EOFError:
        pass


def _typing_pause(seconds: float = 0.35) -> None:
    time.sleep(seconds)


def play(scenario: Scenario, console: Optional[Console] = None,
         animate: bool = True) -> None:
    console = console or ui.make_console()
    console.clear()
    console.print(ui.header_panel(scenario))
    console.print()

    total = len(scenario.turns)
    for idx, turn in enumerate(scenario.turns, start=1):
        console.print(ui.customer_panel(scenario.customer_name, turn.customer,
                                        idx, total))
        console.print()

        if animate:
            with console.status("[dim]agents thinking…[/]", spinner="dots"):
                _typing_pause(0.7)

        cols = Columns(
            [
                ui.baseline_panel(scenario.baseline_label, turn.baseline.reply),
                ui.safe_panel(scenario.safe_label, turn.safe.reply,
                              turn.safe.principles),
            ],
            equal=True,
            expand=True,
        )
        console.print(cols)
        console.print()
        console.print(ui.explanations_panel(turn.safe.explanations))

        if idx < total:
            _wait_for_enter(console)
            console.print()
            console.rule(style="grey30")
            console.print()

    console.print()
    console.rule("[bold]End of conversation[/]", style="white")
    console.print()
    console.print(ui.closing_panel(scenario))
    console.print()
    console.print(Panel(
        Text("Thanks for watching. The SAFE framework keeps agents safe by "
             "constraining Scope, Anchoring decisions in evidence, enforcing "
             "Flow Integrity, and Escalating when needed.",
             style="white"),
        border_style="white",
        padding=(1, 2),
    ))
