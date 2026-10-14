"""Run deterministic mechanism ablations over a generated SAFE suite."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from safe_benchmark.generated.ablation import run_ablation_suite, write_ablation_report
from safe_benchmark.generated.generator import load_suite


def main() -> None:
    root = Path(__file__).resolve().parent.parent
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--suite",
        type=Path,
        default=root / "data" / "generated_safe" / "fixtures" / "public-seed-1701.json",
    )
    parser.add_argument(
        "--json-output",
        type=Path,
        default=root
        / "outputs"
        / "derived"
        / "component-ablation-v1"
        / "component-ablations.json",
    )
    parser.add_argument(
        "--markdown-output",
        type=Path,
        default=root
        / "outputs"
        / "derived"
        / "component-ablation-v1"
        / "component-ablations.md",
    )
    args = parser.parse_args()

    report = run_ablation_suite(load_suite(args.suite))
    write_ablation_report(report, args.json_output, args.markdown_output)
    for result in report.profiles:
        metrics = result.aggregate
        print(
            f"{result.profile.value}: legitimate={metrics.legitimate_allowed}/{metrics.total}, "
            f"blocked={metrics.illegitimate_blocked}/{metrics.total}"
        )


if __name__ == "__main__":
    main()
