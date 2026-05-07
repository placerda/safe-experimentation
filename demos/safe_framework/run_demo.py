"""Entry point for the SAFE Framework demo.

Run with:
    python demos/safe_framework/run_demo.py
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from demo import ui  # noqa: E402
from demo.menu import discover_scenarios, pick_scenario, post_run_choice  # noqa: E402
from demo.player import play  # noqa: E402
from demo.scenario import load_scenario  # noqa: E402


def _run_single(path: Path, animate: bool) -> int:
    scenario = load_scenario(path)
    try:
        play(scenario, animate=animate)
    except KeyboardInterrupt:
        print()
        return 130
    return 0


def _run_interactive(scenarios_dir: Path, animate: bool) -> int:
    console = ui.make_console()
    options = discover_scenarios(scenarios_dir)
    if not options:
        console.print(f"[red]No scenarios found in {scenarios_dir}[/]")
        return 1

    try:
        choice = pick_scenario(options, console)
        while choice is not None:
            play(choice.scenario, console=console, animate=animate)
            choice = post_run_choice(options, console)
        console.print()
        console.print("[dim]Goodbye.[/]")
    except KeyboardInterrupt:
        print()
        return 130
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="SAFE Framework demo")
    parser.add_argument(
        "--scenario",
        type=Path,
        default=None,
        help="Run a single scenario YAML and exit (skips the menu).",
    )
    parser.add_argument(
        "--scenarios-dir",
        type=Path,
        default=ROOT / "scenarios",
        help="Directory to discover scenarios from (default: ./scenarios).",
    )
    parser.add_argument(
        "--no-animate",
        action="store_true",
        help="Disable thinking spinner / typing pauses.",
    )
    args = parser.parse_args()

    animate = not args.no_animate
    if args.scenario is not None:
        return _run_single(args.scenario, animate=animate)
    return _run_interactive(args.scenarios_dir, animate=animate)


if __name__ == "__main__":
    raise SystemExit(main())
