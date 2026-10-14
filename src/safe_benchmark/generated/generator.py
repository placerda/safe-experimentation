"""Generate reproducible SAFE challenges from a declarative YAML specification."""

from __future__ import annotations

import hashlib
import json
import random
import re
from pathlib import Path
from typing import Any

import yaml

from safe_benchmark.generated.schema import (
    BenchmarkSpecification,
    ChallengeSuite,
    GeneratedChallenge,
)

_PLACEHOLDER = re.compile(r"^\{\{([a-zA-Z0-9_]+)\}\}$")


def _canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def sha256_value(value: Any) -> str:
    return hashlib.sha256(_canonical_json(value).encode()).hexdigest()


def load_specification(path: Path) -> tuple[BenchmarkSpecification, str]:
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    specification = BenchmarkSpecification.model_validate(raw)
    return specification, sha256_value(raw)


def _render(value: Any, variables: dict[str, Any]) -> Any:
    if isinstance(value, str):
        exact = _PLACEHOLDER.match(value)
        if exact:
            return variables[exact.group(1)]
        rendered = value
        for key, replacement in variables.items():
            rendered = rendered.replace(f"{{{{{key}}}}}", str(replacement))
        return rendered
    if isinstance(value, list):
        return [_render(item, variables) for item in value]
    if isinstance(value, dict):
        return {key: _render(item, variables) for key, item in value.items()}
    return value


def _seed_commitment(seed: int | str) -> str:
    return hashlib.sha256(str(seed).encode()).hexdigest()


def generate_suite(
    specification: BenchmarkSpecification,
    specification_sha256: str,
    seed: int | str,
    *,
    seed_visibility: str = "public",
) -> ChallengeSuite:
    """Generate one paired challenge per family with deterministic variable selection."""
    rng = random.Random(str(seed))
    challenges: list[GeneratedChallenge] = []
    commitment = _seed_commitment(seed)

    for family in specification.families:
        variables = {name: rng.choice(values) for name, values in sorted(family.variables.items())}
        for variant, template in sorted(family.variants.items(), key=lambda item: item[0].value):
            suffix = hashlib.sha256(
                f"{commitment}:{family.family}:{variant.value}".encode()
            ).hexdigest()[:12]
            challenge_id = f"{family.family}-{variant.value}-{suffix}"
            rendered = _render(template.model_dump(mode="json"), variables)
            rendered["reference_trace"] = {
                "challenge_id": challenge_id,
                "events": rendered.pop("reference_events"),
            }
            rendered["negative_trace"] = {
                "challenge_id": challenge_id,
                "events": rendered.pop("negative_events"),
            }
            challenges.append(
                GeneratedChallenge(
                    challenge_id=challenge_id,
                    family=family.family,
                    dimension=family.dimension,
                    variant=variant,
                    issue=family.issue,
                    **rendered,
                )
            )

    return ChallengeSuite(
        specification_sha256=specification_sha256,
        seed_visibility=seed_visibility,
        seed_commitment=commitment,
        challenges=challenges,
    )


def write_suite(path: Path, suite: ChallengeSuite) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = suite.model_dump(mode="json")
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def load_suite(path: Path) -> ChallengeSuite:
    return ChallengeSuite.model_validate_json(path.read_text(encoding="utf-8"))


def suite_sha256(suite: ChallengeSuite) -> str:
    return sha256_value(suite.model_dump(mode="json"))
