
from scripts.analyze_v4 import clustered_bootstrap_diff, holm_correct


def test_clustered_bootstrap_diff_resamples_tasks_deterministically():
    pairs = [
        ("task_a", 1.0, 0.0),
        ("task_a", 0.5, 0.0),
        ("task_b", 0.0, 1.0),
    ]
    first = clustered_bootstrap_diff(pairs, n_boot=200, seed=123)
    second = clustered_bootstrap_diff(pairs, n_boot=200, seed=123)
    assert first == second
    obs, lo, hi, p = first
    assert obs == (1.0 + 0.5 - 1.0) / 3
    assert lo <= obs <= hi
    assert 0.0 <= p <= 1.0


def test_holm_correct_monotone_adjusted_values():
    corrected = holm_correct([("b", 0.04), ("a", 0.01), ("c", 0.03)])
    assert [label for label, _, _ in corrected] == ["a", "c", "b"]
    adjusted = [adj for _, _, adj in corrected]
    assert adjusted == sorted(adjusted)
    assert adjusted == [0.03, 0.06, 0.06]
