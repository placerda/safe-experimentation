"""Tests for scripts/stats_v6.py using synthetic result records."""
from __future__ import annotations

import json

import pytest

from scripts.stats_v6 import (
    analyze,
    compare,
    index_rows,
    main,
    mcnemar_exact,
    metric_value,
    summarize,
    task_level_wilcoxon,
)


def _row(variant, task, seed=0, **kw):
    base = {
        "task_id": task,
        "agent_variant": variant,
        "domain": task.split("_")[0],
        "seed": seed,
        "invalid": False,
        "error": None,
        "tau2_reward": 1.0,
        "any_unsafe_write": False,
        "commission_error": False,
        "unsafe_extra_writes": 0,
        "missed_gold_writes": 0,
        "executed_writes": 1,
        "transferred": False,
        "unconfirmed_writes": 0,
        "unauthenticated_writes": 0,
        "blocked_calls": 0,
        "blocks_by_rule": {},
    }
    base.update(kw)
    return base


def test_metric_value_success_and_bool():
    assert metric_value({"tau2_reward": 1.0}, "success") == 1.0
    assert metric_value({"tau2_reward": 0.0}, "success") == 0.0
    assert metric_value({"tau2_reward": None}, "success") is None
    assert metric_value({"any_unsafe_write": True}, "any_unsafe_write") == 1.0
    assert metric_value({"unsafe_extra_writes": 3}, "unsafe_extra_writes") == 3.0
    assert metric_value({}, "unsafe_extra_writes") is None


def test_mcnemar_exact():
    assert mcnemar_exact([(0, 0), (1, 1)]) == (0, 0, 1.0)
    b, c, p = mcnemar_exact([(0, 1)] * 6)
    assert (b, c) == (0, 6)
    assert p == pytest.approx(2 * 0.5**6)


def test_task_level_wilcoxon_all_zero():
    assert task_level_wilcoxon([0.0, 0.0, 0.0]) == 1.0


def test_index_rows_excludes_invalid_and_errored():
    rows = [
        _row("baseline", "airline_000"),
        _row("baseline", "airline_001", invalid=True),
        _row("baseline", "airline_002", error="boom"),
    ]
    idx = index_rows(rows)
    assert set(idx) == {("baseline", "airline_000", 0)}


def test_compare_pairs_by_task_and_seed():
    rows = []
    for i in range(8):
        for s in (0, 1):
            rows.append(_row("baseline", f"airline_{i:03d}", s, any_unsafe_write=True))
            rows.append(_row("safeguard", f"airline_{i:03d}", s, any_unsafe_write=False))
    # An unpaired row must be ignored.
    rows.append(_row("safeguard", "airline_099", 0, any_unsafe_write=True))
    r = compare(index_rows(rows), "safeguard", "baseline", "any_unsafe_write", n_boot=200)
    assert r["n_pairs"] == 16
    assert r["n_tasks"] == 8
    assert r["diff"] == pytest.approx(-1.0)
    assert r["tasks_better"] == 8 and r["tasks_worse"] == 0
    assert r["mcnemar_b"] == 0 and r["mcnemar_c"] == 16
    assert r["p_wilcoxon_task"] < 0.01


def test_compare_success_direction():
    rows = []
    for i in range(6):
        rows.append(_row("baseline", f"retail_{i:03d}", tau2_reward=0.0))
        rows.append(_row("safeguard", f"retail_{i:03d}", tau2_reward=1.0))
    r = compare(index_rows(rows), "safeguard", "baseline", "success", n_boot=200)
    assert r["diff"] == pytest.approx(1.0)
    assert r["tasks_better"] == 6


def test_analyze_holm_and_families():
    rows = []
    for i in range(10):
        t = f"airline_{i:03d}"
        rows.append(_row("baseline", t, any_unsafe_write=i < 6, unsafe_extra_writes=2 if i < 6 else 0))
        rows.append(_row("safe-prompt", t, any_unsafe_write=i < 4))
        rows.append(_row("safeguard", t))
        rows.append(_row("safeguard-noF", t, any_unsafe_write=i < 3))
    results = analyze(rows, n_boot=200)
    families = {r["family"] for r in results}
    assert families == {"primary", "ablation"}
    for r in results:
        assert r["p_holm"] >= r["p_wilcoxon_task"] - 1e-12
        assert 0.0 <= r["p_holm"] <= 1.0
    comps = {(r["treatment"], r["control"]) for r in results}
    assert ("safeguard", "baseline") in comps
    assert ("safeguard", "safeguard-noF") in comps
    # Missing ablations are skipped, not reported.
    assert ("safeguard", "safeguard-noS") not in comps


def test_summarize_counts_exclusions_and_rules():
    rows = [
        _row("safeguard", "airline_000", blocks_by_rule={"F:confirm": 2}),
        _row("safeguard", "airline_001", blocks_by_rule={"F:confirm": 1, "A:unanchored": 1}),
        _row("safeguard", "airline_002", error="x"),
        _row("baseline", "retail_000"),
    ]
    s = {e["variant"]: e for e in summarize(rows)}
    assert s["safeguard"]["n_valid"] == 2
    assert s["safeguard"]["n_excluded"] == 1
    assert s["safeguard"]["blocks_by_rule"] == {"A:unanchored": 1, "F:confirm": 3}
    airline = {e["variant"]: e for e in summarize(rows, "airline")}
    assert "baseline" not in airline


def test_main_writes_outputs(tmp_path):
    rows = []
    for i in range(6):
        rows.append(_row("baseline", f"airline_{i:03d}", any_unsafe_write=i % 2 == 0))
        rows.append(_row("safeguard", f"airline_{i:03d}"))
    run = tmp_path / "run"
    run.mkdir()
    (run / "results.json").write_text(json.dumps(rows), encoding="utf-8")
    assert main([str(run), "--n-boot", "100"]) == 0
    md = (run / "stats.md").read_text(encoding="utf-8")
    assert "safeguard vs baseline" in md
    assert (run / "stats.csv").exists()
    data = json.loads((run / "stats.json").read_text(encoding="utf-8"))
    assert data["comparisons"]
