"""Interactive scenario picker for the SAFE demo."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

from rich.align import Align
from rich.console import Console, Group
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table
from rich.text import Text

from .scenario import Scenario, load_scenario


@dataclass(frozen=True)
class ScenarioOption:
    key: str
    path: Path
    scenario: Scenario


def discover_scenarios(scenarios_dir: Path) -> List[ScenarioOption]:
    options: List[ScenarioOption] = []
    for i, yaml_path in enumerate(sorted(scenarios_dir.glob("*.yaml")), start=1):
        scenario = load_scenario(yaml_path)
        options.append(ScenarioOption(key=str(i), path=yaml_path, scenario=scenario))
    return options


def _intro_panel() -> Panel:
    body = Group(
        Align.center(Text("SAFE Framework — Live Demo", style="bold white")),
        Align.center(Text(
            "Side-by-side Baseline vs SAFE-aware agent on the same conversation.",
            style="dim",
        )),
        Text(""),
        Align.center(Text(
            "🛡️  Scope     ⚓ Anchored Decisions     🔀 Flow Integrity     📣 Escalation",
            style="bold",
        )),
    )
    return Panel(body, border_style="white", padding=(1, 2))


def _menu_table(options: List[ScenarioOption]) -> Table:
    table = Table(
        show_header=True,
        header_style="bold white",
        border_style="grey50",
        title="Choose a scenario",
        title_style="bold",
        title_justify="left",
    )
    table.add_column("#", style="bold cyan", width=3, justify="right")
    table.add_column("Scenario", style="bold white")
    table.add_column("Description", style="white")
    table.add_column("Turns", style="dim", justify="right")
    for opt in options:
        table.add_row(
            opt.key,
            opt.scenario.title,
            opt.scenario.subtitle,
            str(len(opt.scenario.turns)),
        )
    table.add_row("q", "[bold red]Quit[/]", "Exit the demo.", "")
    return table


def pick_scenario(
    options: List[ScenarioOption],
    console: Console,
    *,
    show_intro: bool = True,
    prompt_text: str = "Pick a scenario",
) -> Optional[ScenarioOption]:
    """Show the menu and return the chosen scenario, or None to quit."""
    console.clear()
    if show_intro:
        console.print(_intro_panel())
        console.print()
    console.print(_menu_table(options))
    console.print()

    valid = [opt.key for opt in options] + ["q", "Q"]
    choice = Prompt.ask(
        f"[bold]{prompt_text}[/]",
        choices=valid,
        show_choices=False,
        default=options[0].key if options else "q",
        console=console,
    )
    if choice.lower() == "q":
        return None
    for opt in options:
        if opt.key == choice:
            return opt
    return None


def post_run_choice(
    options: List[ScenarioOption],
    console: Console,
) -> Optional[ScenarioOption]:
    """After a scenario finishes, offer another scenario or quit."""
    console.print()
    console.print("[dim italic]Press Enter to return to the menu…[/]")
    try:
        input()
    except EOFError:
        pass
    return pick_scenario(
        options,
        console,
        show_intro=False,
        prompt_text="Pick another scenario or 'q' to quit",
    )
