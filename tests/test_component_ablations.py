"""Contract and regression tests for generated SAFE component ablations."""

from __future__ import annotations

from pathlib import Path

from safe_benchmark.generated.ablation import (
    AblationProfile,
    evaluate_profile,
    render_markdown,
    run_ablation_suite,
)
from safe_benchmark.generated.generator import load_suite
from safe_benchmark.generated.schema import CandidateTrace, Dimension, TraceEvent

ROOT = Path(__file__).resolve().parent.parent
FIXTURE = ROOT / "data" / "generated_safe" / "fixtures" / "public-seed-1701.json"


def _results_by_profile():
    report = run_ablation_suite(load_suite(FIXTURE))
    return report, {result.profile: result for result in report.profiles}


def test_full_safe_guard_allows_legitimate_and_blocks_all_negative_mutations() -> None:
    _, results = _results_by_profile()
    full = results[AblationProfile.FULL_SAFE_GUARD]

    assert full.aggregate.legitimate_allow_rate == 1.0
    assert full.aggregate.illegitimate_block_rate == 1.0
    assert all(full.contract_conformance.values())


def test_leave_one_dimension_out_has_expected_controlled_failure_surface() -> None:
    _, results = _results_by_profile()
    omitted_by_profile = {
        AblationProfile.WITHOUT_SCOPE: Dimension.SCOPE,
        AblationProfile.WITHOUT_ANCHORED_DECISIONS: Dimension.ANCHORED_DECISIONS,
        AblationProfile.WITHOUT_FLOW_INTEGRITY: Dimension.FLOW_INTEGRITY,
        AblationProfile.WITHOUT_ESCALATION: Dimension.ESCALATION,
    }

    for profile, omitted in omitted_by_profile.items():
        result = results[profile]
        assert result.aggregate.legitimate_allow_rate == 1.0
        for dimension, metrics in result.by_dimension.items():
            expected = 0.0 if dimension == omitted.value else 1.0
            assert metrics.illegitimate_block_rate == expected
        assert all(result.contract_conformance.values())


def test_manifest_and_intent_surfaces_are_distinct_from_full_guard() -> None:
    _, results = _results_by_profile()
    manifest = results[AblationProfile.MANIFEST_ONLY]
    intent = results[AblationProfile.INTENT_AUTHORITY_ONLY]

    assert manifest.aggregate.legitimate_allow_rate == 1.0
    assert intent.aggregate.legitimate_allow_rate == 1.0
    assert manifest.aggregate.illegitimate_block_rate < 1.0
    assert intent.aggregate.illegitimate_block_rate < 1.0
    reordered_adversarial = next(
        outcome
        for outcome in manifest.outcomes
        if outcome.family == "reordered-dependencies" and outcome.variant == "adversarial"
    )
    assert not reordered_adversarial.illegitimate_blocked
    intent_exposed = {
        (outcome.family, outcome.variant)
        for outcome in intent.outcomes
        if not outcome.illegitimate_blocked
    }
    assert ("multi-item-coverage", "adversarial") in intent_exposed
    assert ("stale-replayed-approval", "adversarial") in intent_exposed


def test_intent_authority_ignores_replay_but_rejects_action_substitution() -> None:
    suite = load_suite(FIXTURE)
    replay_challenge = next(
        challenge
        for challenge in suite.challenges
        if challenge.family == "stale-replayed-approval"
        and challenge.variant.value == "adversarial"
    )
    replay_action = replay_challenge.reference_trace.events[-1]
    replay = CandidateTrace(
        challenge_id=replay_challenge.challenge_id,
        events=[
            replay_action,
            TraceEvent.model_validate(replay_action.model_dump()),
        ],
    )
    assert evaluate_profile(
        AblationProfile.INTENT_AUTHORITY_ONLY, replay_challenge, replay
    ).allowed
    assert not evaluate_profile(AblationProfile.MANIFEST_ONLY, replay_challenge, replay).allowed

    substitution = next(
        challenge
        for challenge in suite.challenges
        if challenge.family == "target-substitution"
        and challenge.variant.value == "adversarial"
    )
    assert not evaluate_profile(
        AblationProfile.INTENT_AUTHORITY_ONLY,
        substitution,
        substitution.negative_trace,
    ).allowed


def test_report_is_deterministic_and_marks_mechanism_boundary() -> None:
    suite = load_suite(FIXTURE)
    first = run_ablation_suite(suite)
    second = run_ablation_suite(suite)

    assert first == second
    assert first.evaluation_kind == "mechanism_test"
    assert not first.agent_effectiveness_measured
    markdown = render_markdown(first)
    assert "does not measure agent effectiveness" in markdown
    assert "Violation prevention by family" in markdown
