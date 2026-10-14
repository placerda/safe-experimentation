"""Seed freezing and commitment verification for hidden challenge suites."""

from __future__ import annotations

import hashlib
import json
import secrets
from pathlib import Path
from typing import Any


def seed_commitment(seed: str) -> str:
    return hashlib.sha256(seed.encode()).hexdigest()


def create_seed_file(path: Path, count: int) -> list[str]:
    if count < 1:
        raise ValueError("count must be positive")
    seeds = [secrets.token_hex(32) for _ in range(count)]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"seeds": seeds}, indent=2) + "\n", encoding="utf-8")
    return seeds


def load_seed_file(path: Path) -> list[str]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    seeds = raw.get("seeds")
    if not isinstance(seeds, list) or not seeds or not all(isinstance(seed, str) for seed in seeds):
        raise ValueError("seed file must contain a non-empty string list named 'seeds'")
    return seeds


def build_manifest(specification_sha256: str, seeds: list[str]) -> dict[str, Any]:
    return {
        "manifest_version": "1",
        "specification_sha256": specification_sha256,
        "seed_count": len(seeds),
        "seed_commitments": [seed_commitment(seed) for seed in seeds],
    }


def verify_manifest(manifest: dict[str, Any], specification_sha256: str, seeds: list[str]) -> list[str]:
    expected = build_manifest(specification_sha256, seeds)
    return [
        f"{key}: expected {expected[key]!r}, observed {manifest.get(key)!r}"
        for key in expected
        if manifest.get(key) != expected[key]
    ]
