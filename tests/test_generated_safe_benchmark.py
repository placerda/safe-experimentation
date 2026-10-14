"""Tests for the deterministic specification-generated SAFE benchmark."""

from __future__ import annotations

import json
from pathlib import Path

from safe_benchmark.generated.freeze import (
    build_manifest,
    create_seed_file,
    load_seed_file,
    verify_manifest,
)
from safe_benchmark.generated.generator import generate_suite, load_specification, load_suite, suite_sha256
from safe_benchmark.generated.oracle import evaluate_candidate, validate_reference_pair
from safe_benchmark.generated.schema import CandidateTrace, TraceEvent

ROOT = Path(__file__).resolve().parent.parent
SPEC = ROOT / "data" / "generated_safe" / "specification.yaml"
FIXTURE = ROOT / "data" / "generated_safe" / "fixtures" / "public-seed-1701.json"

EXPECTED_FAMILIES = {
    "target-substitution",
    "source-destination-inversion",
    "multi-item-coverage",
    "wrong-feasible-set",
    "unauthorized-attribute-change",
    "reordered-dependencies",
    "stale-replayed-approval",
    "multi-action-assent",
    "payment-provenance",
    "backend-failure",
    "observer-failure",
    "ambiguity-escalation",
}


def test_generation_is_deterministic_and_fixture_is_current() -> None:
    specification, spec_hash = load_specification(SPEC)
    first = generate_suite(specification, spec_hash, 1701)
    second = generate_suite(specification, spec_hash, 1701)
    fixture = load_suite(FIXTURE)

    assert first == second
    assert first == fixture
    assert suite_sha256(first) == "768bd79554b0730c0e486bf18bc80d40d1c8d5a0ea571f7028caf1b389c6c1fa"


def test_all_required_families_dimensions_and_pairs_are_present() -> None:
    suite = load_suite(FIXTURE)

    assert {challenge.family for challenge in suite.challenges} == EXPECTED_FAMILIES
    assert {challenge.dimension.value for challenge in suite.challenges} == {
        "scope",
        "anchored_decisions",
        "flow_integrity",
        "escalation",
    }
    assert len(suite.challenges) == len(EXPECTED_FAMILIES) * 2
    for family in EXPECTED_FAMILIES:
        assert {
            challenge.variant.value for challenge in suite.challenges if challenge.family == family
        } == {"adversarial", "near_neighbor"}


def test_every_reference_passes_and_every_negative_fails() -> None:
    suite = load_suite(FIXTURE)

    for challenge in suite.challenges:
        assert validate_reference_pair(challenge) == []
        assert evaluate_candidate(challenge, challenge.reference_trace).passed
        negative = evaluate_candidate(challenge, challenge.negative_trace)
        assert not negative.passed, challenge.challenge_id
        assert negative.violations


def test_oracles_detect_required_edge_cases() -> None:
    suite = load_suite(FIXTURE)
    adverse = {
        challenge.family: challenge
        for challenge in suite.challenges
        if challenge.variant.value == "adversarial"
    }

    expected_fragments = {
        "target-substitution": "forbidden event",
        "source-destination-inversion": "forbidden event",
        "multi-item-coverage": "expected 2 actions",
        "wrong-feasible-set": "missing required event",
        "unauthorized-attribute-change": "unauthorized arguments",
        "reordered-dependencies": "order violation",
        "stale-replayed-approval": "expected 1 actions",
        "multi-action-assent": "missing required event",
        "payment-provenance": "forbidden event",
        "backend-failure": "missing required event",
        "observer-failure": "forbidden event",
        "ambiguity-escalation": "missing required event",
    }
    for family, fragment in expected_fragments.items():
        result = evaluate_candidate(adverse[family], adverse[family].negative_trace)
        assert any(fragment in violation for violation in result.violations), (
            family,
            result.violations,
        )


def test_oracle_rejects_mismatched_challenge_id() -> None:
    challenge = load_suite(FIXTURE).challenges[0]
    candidate = CandidateTrace(
        challenge_id="wrong-id",
        events=challenge.reference_trace.events,
    )
    result = evaluate_candidate(challenge, candidate)
    assert not result.passed
    assert "candidate challenge_id does not match" in result.violations


def test_hidden_seed_freeze_and_tamper_detection(tmp_path: Path) -> None:
    _, spec_hash = load_specification(SPEC)
    seed_path = tmp_path / "private" / "seeds.json"
    seeds = create_seed_file(seed_path, 3)
    manifest = build_manifest(spec_hash, seeds)

    assert load_seed_file(seed_path) == seeds
    assert verify_manifest(manifest, spec_hash, seeds) == []
    tampered = json.loads(json.dumps(manifest))
    tampered["seed_commitments"][0] = "0" * 64
    assert verify_manifest(tampered, spec_hash, seeds)


def test_approval_replay_is_detected_directly() -> None:
    suite = load_suite(FIXTURE)
    challenge = next(
        challenge
        for challenge in suite.challenges
        if challenge.family == "stale-replayed-approval"
        and challenge.variant.value == "adversarial"
    )
    action = challenge.reference_trace.events[-1]
    replay = CandidateTrace(
        challenge_id=challenge.challenge_id,
        events=[*challenge.reference_trace.events, TraceEvent.model_validate(action.model_dump())],
    )

    result = evaluate_candidate(challenge, replay)
    assert not result.passed
    assert any("replayed" in violation for violation in result.violations)
