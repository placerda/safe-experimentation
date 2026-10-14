"""Execute or resume the frozen generated SAFE live-agent run plan."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from safe_benchmark.generated.live_runtime import (
    DeterministicSmokeAgent,
    InfrastructureFailure,
    atomic_write_json,
    create_azure_agent,
    job_is_runnable,
    job_slug,
    run_live_challenge,
    validate_live_inputs,
)
from safe_benchmark.generated.prospective import load_config
from safe_benchmark.trace_schema import AgentTrace

ROOT = Path(__file__).resolve().parent.parent
CONFIG = ROOT / "configs" / "prospective-study.yaml"
SUITE = ROOT / "data" / "generated_safe" / "hidden" / "prospective-suite.json"
PLAN = ROOT / "data" / "generated_safe" / "hidden" / "prospective-run-plan.json"


def _key(row: dict) -> tuple[str, int, str]:
    return row["task_id"], int(row["seed_index"]), row["arm"]


def _read_rows(path: Path) -> list[dict]:
    if not path.exists():
        return []
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, list):
        raise TypeError("results file must contain a JSON list")
    return value


def _recover_interrupted_attempts(output: Path, rows: list[dict], jobs: list[dict]) -> None:
    indexed = {_key(row): row for row in rows}
    for job in jobs:
        journal = output / "attempts" / f"{job_slug(job)}.json"
        if not journal.exists():
            continue
        state = json.loads(journal.read_text(encoding="utf-8"))
        if state.get("status") != "running":
            continue
        key = (job["task_id"], int(job["seed_index"]), job["arm"])
        row = indexed.get(key)
        if row is None:
            row = {
                **job,
                "challenge_variant": job["variant"],
                "status": "incomplete",
                "attempts": [],
            }
            rows.append(row)
            indexed[key] = row
        attempt = int(state["attempt"])
        if len(row["attempts"]) < attempt:
            row["attempts"].append(
                {
                    "attempt": attempt,
                    "status": "infrastructure_failure",
                    "retry_reason": None,
                    "failure_reason": "process_crash",
                    "error": "Previous process ended before a terminal trace was serialized.",
                }
            )
        state["status"] = "infrastructure_failure"
        state["failure_reason"] = "process_crash"
        atomic_write_json(journal, state)


def execute(args: argparse.Namespace) -> int:
    config, _ = load_config(CONFIG)
    suite, plan = validate_live_inputs(config, SUITE, PLAN)
    by_id = {challenge.challenge_id: challenge for challenge in suite.challenges}
    output = args.output
    results_path = output / "results.json"
    rows = _read_rows(results_path)
    _recover_interrupted_attempts(output, rows, plan["jobs"])
    indexed = {_key(row): row for row in rows}
    prompts = {
        arm.name: (ROOT / arm.prompt_file).read_text(encoding="utf-8")
        for arm in config.arms
    }

    for job in plan["jobs"]:
        key = (job["task_id"], int(job["seed_index"]), job["arm"])
        existing = indexed.get(key)
        if not job_is_runnable(existing):
            continue
        attempts = list(existing.get("attempts", [])) if existing else []
        attempt_number = len(attempts) + 1
        retry_reason = attempts[-1].get("failure_reason") if attempts else None
        journal = output / "attempts" / f"{job_slug(job)}.json"
        atomic_write_json(
            journal,
            {
                "task_id": job["task_id"],
                "seed_index": job["seed_index"],
                "arm": job["arm"],
                "attempt": attempt_number,
                "status": "running",
            },
        )
        challenge = by_id[job["task_id"]]
        try:
            agent = (
                DeterministicSmokeAgent(challenge.prompt, challenge.context)
                if args.mode == "smoke"
                else create_azure_agent(prompts[job["arm"]])
            )
            trace, result = run_live_challenge(
                challenge,
                arm=job["arm"],
                seed_index=int(job["seed_index"]),
                system_prompt=prompts[job["arm"]],
                agent=agent,
                max_turns=args.max_turns,
            )
            attempt_path = output / "traces" / f"{job_slug(job)}.attempt-{attempt_number}.json"
            try:
                attempt_path.parent.mkdir(parents=True, exist_ok=True)
                attempt_path.write_text(trace.model_dump_json(indent=2) + "\n", encoding="utf-8")
                AgentTrace.model_validate_json(attempt_path.read_text(encoding="utf-8"))
            except Exception as exc:
                raise InfrastructureFailure("trace_serialization_failure", str(exc)) from exc
            attempts.append(
                {
                    "attempt": attempt_number,
                    "status": "complete",
                    "retry_reason": retry_reason,
                    "trace": str(attempt_path.relative_to(output)).replace("\\", "/"),
                }
            )
            row = {**job, **result, "attempts": attempts}
            indexed[key] = row
            atomic_write_json(journal, {**attempts[-1], "status": "complete"})
        except InfrastructureFailure as exc:
            attempts.append(
                {
                    "attempt": attempt_number,
                    "status": "infrastructure_failure",
                    "retry_reason": retry_reason,
                    "failure_reason": exc.reason,
                    "error": str(exc),
                }
            )
            row = {
                **job,
                "challenge_variant": job["variant"],
                "status": "incomplete",
                "attempts": attempts,
            }
            indexed[key] = row
            atomic_write_json(journal, attempts[-1])
        except Exception as exc:  # noqa: BLE001 - persisted as a non-retryable blocker
            attempts.append(
                {
                    "attempt": attempt_number,
                    "status": "nonretryable_failure",
                    "retry_reason": retry_reason,
                    "error": str(exc),
                }
            )
            row = {
                **job,
                "challenge_variant": job["variant"],
                "status": "incomplete",
                "attempts": attempts,
            }
            indexed[key] = row
            atomic_write_json(journal, attempts[-1])
        rows = [indexed[key] for key in sorted(indexed)]
        atomic_write_json(results_path, rows)

    complete = sum(row.get("status") == "complete" for row in indexed.values())
    incomplete = sum(row.get("status") != "complete" for row in indexed.values())
    print(f"Frozen live run: {complete}/144 complete; {incomplete} incomplete")
    print(f"Results: {results_path}")
    return 0 if complete == 144 else 2


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("smoke", "paid"), required=True)
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "outputs" / "prospective-study",
    )
    parser.add_argument("--max-turns", type=int, default=12)
    return execute(parser.parse_args())


if __name__ == "__main__":
    raise SystemExit(main())
