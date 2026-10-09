import hashlib
import json

import pytest
from pydantic import ValidationError

from scripts.verify_frozen_run import verify


@pytest.fixture
def frozen_run(tmp_path):
    root = tmp_path / "repo"
    root.mkdir()
    source = root / "source.py"
    source.write_text("unchanged\n", encoding="utf-8")
    run = root / "run"
    traces = run / "traces"
    traces.mkdir(parents=True)
    freeze = {
        "commit": "frozen-development-source",
        "files": {"source.py": hashlib.sha256(source.read_bytes()).hexdigest()},
        "tasks": ["synthetic"],
        "variants": ["baseline", "treatment"],
        "seed_indices": [0],
        "expected_trajectories": 2,
    }
    (run / "freeze.json").write_text(json.dumps(freeze), encoding="utf-8")
    rows = []
    for variant in freeze["variants"]:
        trace = {
            "task_id": "synthetic", "domain": "retail", "agent_variant": variant,
            "system_prompt": "synthetic", "task_completed": True, "seed": 0,
        }
        (traces / f"{variant}.json").write_text(json.dumps(trace), encoding="utf-8")
        rows.append({**trace, "tau2_reward": 1.0, "error": None, "invalid": False})
    (run / "results.json").write_text(json.dumps(rows), encoding="utf-8")
    return run, root


def alter(path, update):
    value = json.loads(path.read_text(encoding="utf-8"))
    update(value)
    path.write_text(json.dumps(value), encoding="utf-8")


def test_complete_run_verifies(frozen_run):
    run, root = frozen_run
    result = verify(run, root)
    assert result["result_cells"] == result["trace_cells"] == 2
    assert result["complete_task_seed_blocks"] == 1


def test_source_change_rejected(frozen_run):
    run, root = frozen_run
    (root / "source.py").write_text("changed\n", encoding="utf-8")
    with pytest.raises(ValueError, match="Frozen hash changed"):
        verify(run, root)


@pytest.mark.parametrize("update, message", [
    (lambda rows: rows.pop(), "coverage mismatch"),
    (lambda rows: rows.append(rows[0]), "Duplicate result"),
    (lambda rows: rows[0].update(error="API failed"), "execution error"),
    (lambda rows: rows[0].update(invalid=True), "execution error"),
    (lambda rows: rows[0].update(task_completed=False), "termination mismatch"),
    (lambda rows: rows[0].update(task_id="unexpected"), "coverage mismatch"),
])
def test_bad_result_cells_rejected(frozen_run, update, message):
    run, root = frozen_run
    alter(run / "results.json", update)
    with pytest.raises(ValueError, match=message):
        verify(run, root)


@pytest.mark.parametrize("reward", [None, -0.1, 1.1, float("nan")])
def test_missing_or_invalid_rewards_rejected(frozen_run, reward):
    run, root = frozen_run
    alter(run / "results.json", lambda rows: rows[0].update(tau2_reward=reward))
    with pytest.raises(ValidationError):
        verify(run, root)


def test_duplicate_trace_rejected(frozen_run):
    run, root = frozen_run
    original = run / "traces" / "baseline.json"
    (run / "traces" / "duplicate.json").write_bytes(original.read_bytes())
    with pytest.raises(ValueError, match="Duplicate trace"):
        verify(run, root)


def test_missing_trace_rejected(frozen_run):
    run, root = frozen_run
    (run / "traces" / "baseline.json").unlink()
    with pytest.raises(ValueError, match="Trace coverage"):
        verify(run, root)


def test_errored_trace_rejected(frozen_run):
    run, root = frozen_run
    alter(run / "traces" / "baseline.json", lambda trace: trace.update(error="API failed"))
    with pytest.raises(ValueError, match="trace error"):
        verify(run, root)


@pytest.mark.parametrize("update", [
    lambda freeze: freeze.update(expected_trajectories=3),
    lambda freeze: freeze.update(tasks=[]),
    lambda freeze: freeze.update(tasks=["synthetic", "synthetic"]),
    lambda freeze: freeze.update(seed_indices=[True]),
    lambda freeze: freeze.update(files={"source.py": "invalid hash"}),
])
def test_invalid_design_rejected(frozen_run, update):
    run, root = frozen_run
    alter(run / "freeze.json", update)
    with pytest.raises(ValidationError):
        verify(run, root)


def test_external_frozen_path_rejected(frozen_run):
    run, root = frozen_run
    outside = root.parent / "outside.py"
    outside.write_text("outside", encoding="utf-8")
    alter(run / "freeze.json", lambda freeze: freeze.update(
        files={"../outside.py": hashlib.sha256(outside.read_bytes()).hexdigest()},
    ))
    with pytest.raises(ValueError, match="escapes repository"):
        verify(run, root)
