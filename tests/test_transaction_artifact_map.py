from pathlib import Path

from scripts.build_transaction_artifact_map import tree_digest, verify


def test_tree_digest_is_stable_and_path_sensitive(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr("scripts.build_transaction_artifact_map.ROOT", tmp_path)
    first = tmp_path / "a.json"
    second = tmp_path / "b.json"
    first.write_text("same", encoding="utf-8")
    second.write_text("same", encoding="utf-8")
    assert tree_digest([first, second]) == tree_digest([second, first])
    original = tree_digest([first])
    first.write_text("changed", encoding="utf-8")
    assert tree_digest([first]) != original


def test_verify_detects_changed_raw_artifact(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr("scripts.build_transaction_artifact_map.ROOT", tmp_path)
    run_dir = tmp_path / "outputs/runs/example"
    traces_dir = run_dir / "traces"
    traces_dir.mkdir(parents=True)
    result = run_dir / "results.json"
    result.write_text("[]", encoding="utf-8")
    payload = {
        "runs": [
            {
                "name": "example",
                "path": "outputs/runs/example",
                "raw_artifacts": {"outputs/runs/example/results.json": "0" * 64},
                "trace_files": 0,
                "trace_tree_sha256": tree_digest([]),
            }
        ],
        "derived_outputs": {},
    }
    assert verify(payload) == ["raw artifact changed: outputs/runs/example/results.json"]
