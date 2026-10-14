"""Deterministic, specification-generated SAFE challenge benchmark."""

from safe_benchmark.generated.generator import generate_suite, load_specification
from safe_benchmark.generated.oracle import evaluate_candidate
from safe_benchmark.generated.schema import ChallengeSuite, OracleResult

__all__ = [
    "ChallengeSuite",
    "OracleResult",
    "evaluate_candidate",
    "generate_suite",
    "load_specification",
]
