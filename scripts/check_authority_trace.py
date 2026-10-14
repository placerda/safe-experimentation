"""Check a production trace against the independent authority state model."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from safe_benchmark.formal_authority import (
    ProductionRecognition,
    check_production_trace,
)
from safe_benchmark.trace_schema import AgentTrace


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("trace", type=Path)
    parser.add_argument(
        "recognition",
        type=Path,
        help="JSON ProductionRecognition; natural-language recognition is outside the proof",
    )
    args = parser.parse_args()
    trace = AgentTrace.model_validate_json(args.trace.read_text(encoding="utf-8"))
    decisions = ProductionRecognition.model_validate_json(args.recognition.read_text(encoding="utf-8"))
    result = check_production_trace(trace, decisions)
    print(json.dumps(result.model_dump(mode="json"), indent=2))
    return 0 if result.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
