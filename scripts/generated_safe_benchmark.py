"""Generate, validate, and freeze the deterministic SAFE challenge benchmark."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from safe_benchmark.generated.freeze import (
    build_manifest,
    create_seed_file,
    load_seed_file,
    verify_manifest,
)
from safe_benchmark.generated.generator import (
    generate_suite,
    load_specification,
    load_suite,
    suite_sha256,
    write_suite,
)
from safe_benchmark.generated.oracle import validate_reference_pair

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_SPEC = ROOT / "data" / "generated_safe" / "specification.yaml"


def _validate_suite(path: Path, expected_spec_hash: str | None = None) -> list[str]:
    suite = load_suite(path)
    errors: list[str] = []
    if expected_spec_hash and suite.specification_sha256 != expected_spec_hash:
        errors.append("suite specification hash does not match the current specification")
    ids = [challenge.challenge_id for challenge in suite.challenges]
    if len(ids) != len(set(ids)):
        errors.append("challenge IDs are not unique")
    pairs = {(challenge.family, challenge.variant.value) for challenge in suite.challenges}
    families = {challenge.family for challenge in suite.challenges}
    for family in families:
        if (family, "adversarial") not in pairs or (family, "near_neighbor") not in pairs:
            errors.append(f"{family}: missing adversarial/near-neighbor pair")
    for challenge in suite.challenges:
        errors.extend(validate_reference_pair(challenge))
    return errors


def command_generate(args: argparse.Namespace) -> int:
    specification, spec_hash = load_specification(args.spec)
    seeds = load_seed_file(args.seed_file) if args.seed_file else [args.seed]
    outputs: list[dict[str, str]] = []
    for index, seed in enumerate(seeds):
        suite = generate_suite(
            specification,
            spec_hash,
            seed,
            seed_visibility="hidden" if args.seed_file else "public",
        )
        output = args.output
        if len(seeds) > 1:
            output = output.with_name(f"{output.stem}-{index:03d}{output.suffix}")
        write_suite(output, suite)
        errors = _validate_suite(output, spec_hash)
        if errors:
            for error in errors:
                print(f"ERROR: {error}", file=sys.stderr)
            return 1
        outputs.append({"path": str(output), "sha256": suite_sha256(suite)})
    print(json.dumps(outputs, indent=2))
    return 0


def command_validate(args: argparse.Namespace) -> int:
    _, spec_hash = load_specification(args.spec)
    errors = _validate_suite(args.suite, spec_hash)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    suite = load_suite(args.suite)
    print(f"Validated {len(suite.challenges)} challenges; sha256={suite_sha256(suite)}")
    return 0


def command_freeze(args: argparse.Namespace) -> int:
    _, spec_hash = load_specification(args.spec)
    if args.seed_file.exists() or args.manifest.exists():
        print("ERROR: refusing to overwrite an existing seed file or manifest", file=sys.stderr)
        return 1
    seeds = create_seed_file(args.seed_file, args.count)
    manifest = build_manifest(spec_hash, seeds)
    args.manifest.parent.mkdir(parents=True, exist_ok=True)
    args.manifest.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Wrote private seeds to {args.seed_file}")
    print(f"Wrote public commitments to {args.manifest}")
    return 0


def command_verify_freeze(args: argparse.Namespace) -> int:
    _, spec_hash = load_specification(args.spec)
    seeds = load_seed_file(args.seed_file)
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    errors = verify_manifest(manifest, spec_hash, seeds)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print(f"Verified {len(seeds)} frozen hidden seed commitments")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    generate = subparsers.add_parser("generate")
    generate.add_argument("--spec", type=Path, default=DEFAULT_SPEC)
    seed = generate.add_mutually_exclusive_group(required=True)
    seed.add_argument("--seed")
    seed.add_argument("--seed-file", type=Path)
    generate.add_argument("--output", type=Path, required=True)
    generate.set_defaults(func=command_generate)

    validate = subparsers.add_parser("validate")
    validate.add_argument("--spec", type=Path, default=DEFAULT_SPEC)
    validate.add_argument("--suite", type=Path, required=True)
    validate.set_defaults(func=command_validate)

    freeze = subparsers.add_parser("freeze")
    freeze.add_argument("--spec", type=Path, default=DEFAULT_SPEC)
    freeze.add_argument("--count", type=int, default=4)
    freeze.add_argument("--seed-file", type=Path, required=True)
    freeze.add_argument("--manifest", type=Path, required=True)
    freeze.set_defaults(func=command_freeze)

    verify = subparsers.add_parser("verify-freeze")
    verify.add_argument("--spec", type=Path, default=DEFAULT_SPEC)
    verify.add_argument("--seed-file", type=Path, required=True)
    verify.add_argument("--manifest", type=Path, required=True)
    verify.set_defaults(func=command_verify_freeze)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
