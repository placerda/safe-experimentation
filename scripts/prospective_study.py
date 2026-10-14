"""Freeze, validate, prepare, and analyze the prospective SAFE-Guard study."""

from __future__ import annotations

import argparse
import json
import secrets
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from safe_benchmark.generated.generator import generate_suite, load_specification, write_suite
from safe_benchmark.generated.prospective import (
    analyze_results,
    build_freeze_manifest,
    build_run_plan,
    load_config,
    planned_cost_surface,
    validate_freeze,
)

ROOT = Path(__file__).resolve().parent.parent
CONFIG = ROOT / "configs" / "prospective-study.yaml"
SPEC = ROOT / "data" / "generated_safe" / "specification.yaml"
MANIFEST = ROOT / "data" / "generated_safe" / "prospective-freeze-manifest.json"
PRIVATE = ROOT / "data" / "generated_safe" / "private" / "prospective-seeds.json"
HIDDEN = ROOT / "data" / "generated_safe" / "hidden" / "prospective-suite.json"
PLAN = ROOT / "data" / "generated_safe" / "hidden" / "prospective-run-plan.json"


def freeze(_: argparse.Namespace) -> int:
    if MANIFEST.exists() or PRIVATE.exists():
        raise SystemExit("refusing to overwrite the prospective seed file or freeze manifest")
    config, _ = load_config(CONFIG)
    seeds = {
        config.generation_seed_role: secrets.token_hex(32),
        config.arm_order_seed_role: secrets.token_hex(32),
    }
    PRIVATE.parent.mkdir(parents=True, exist_ok=True)
    PRIVATE.write_text(json.dumps({"seeds": seeds}, indent=2) + "\n", encoding="utf-8")
    manifest = build_freeze_manifest(
        root=ROOT,
        config_path=CONFIG,
        specification_path=SPEC,
        seeds=seeds,
    )
    MANIFEST.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Frozen {len(seeds)} hidden seed commitments in {MANIFEST}")
    return 0


def validate(args: argparse.Namespace) -> int:
    errors = validate_freeze(
        root=ROOT,
        config_path=CONFIG,
        specification_path=SPEC,
        manifest_path=MANIFEST,
        private_seed_path=PRIVATE if args.with_private_seeds else None,
    )
    config, _ = load_config(CONFIG)
    surface = planned_cost_surface(config)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print(json.dumps({"valid": True, **surface}, indent=2))
    print("No model endpoint was contacted.")
    return 0


def prepare(_: argparse.Namespace) -> int:
    errors = validate_freeze(
        root=ROOT,
        config_path=CONFIG,
        specification_path=SPEC,
        manifest_path=MANIFEST,
        private_seed_path=PRIVATE,
    )
    if errors:
        raise SystemExit("\n".join(errors))
    config, _ = load_config(CONFIG)
    seeds = json.loads(PRIVATE.read_text(encoding="utf-8"))["seeds"]
    specification, spec_hash = load_specification(SPEC)
    suite = generate_suite(
        specification,
        spec_hash,
        seeds[config.generation_seed_role],
        seed_visibility="hidden",
    )
    write_suite(HIDDEN, suite)
    plan = build_run_plan(config, HIDDEN, seeds[config.arm_order_seed_role])
    PLAN.write_text(json.dumps(plan, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Prepared {plan['task_count']} hidden tasks and {plan['trajectory_count']} jobs")
    print("No model endpoint was contacted.")
    return 0


def analyze(args: argparse.Namespace) -> int:
    config, _ = load_config(CONFIG)
    rows = json.loads(args.results.read_text(encoding="utf-8"))
    report = analyze_results(config, rows)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Wrote frozen paired analysis to {args.output}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("freeze").set_defaults(func=freeze)
    validate_parser = commands.add_parser("validate")
    validate_parser.add_argument("--with-private-seeds", action="store_true")
    validate_parser.set_defaults(func=validate)
    commands.add_parser("prepare-hidden").set_defaults(func=prepare)
    analyze_parser = commands.add_parser("analyze")
    analyze_parser.add_argument("--results", type=Path, required=True)
    analyze_parser.add_argument("--output", type=Path, required=True)
    analyze_parser.set_defaults(func=analyze)
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
