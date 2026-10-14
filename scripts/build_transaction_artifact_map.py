"""Build and verify the transactional SAFE-Guard reproducibility map."""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import platform
import subprocess
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
MAP_DIR = ROOT / "artifacts/transactional-safe-guard"
MAP_PATH = MAP_DIR / "artifact-map.json"
DOC_PATH = ROOT / "docs/transactional-artifact-map.md"
PACKAGES = ("pydantic", "PyYAML", "openai", "python-dotenv", "azure-identity", "pytest", "pytest-asyncio", "ruff")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def run(*args: str, check: bool = True) -> str:
    result = subprocess.run(args, cwd=ROOT, text=True, capture_output=True, check=check)
    return result.stdout.strip()


def tree_digest(paths: list[Path]) -> str:
    digest = hashlib.sha256()
    for path in sorted(paths):
        digest.update(path.relative_to(ROOT).as_posix().encode())
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def commit_file_hashes(commit: str, relative: str) -> dict[str, str]:
    git_path = relative.replace("\\", "/")
    data = subprocess.check_output(["git", "show", f"{commit}:{git_path}"], cwd=ROOT)
    hashes = {"git_blob": sha256_bytes(data)}
    if b"\0" not in data:
        hashes["windows_worktree"] = sha256_bytes(data.replace(b"\r\n", b"\n").replace(b"\n", b"\r\n"))
    return hashes


def freeze_verification(freeze: dict[str, Any]) -> dict[str, Any]:
    commit = freeze["commit"]
    mismatches = []
    modes: dict[str, int] = {}
    for relative, expected in freeze.get("files", {}).items():
        try:
            actuals = commit_file_hashes(commit, relative)
        except subprocess.CalledProcessError:
            actuals = {}
        expected = str(expected).lower()
        matched_mode = next((mode for mode, actual in actuals.items() if actual == expected), None)
        worktree_path = ROOT / relative.replace("\\", "/")
        if (
            matched_mode is None
            and worktree_path.is_file()
            and sha256(worktree_path) == expected
            and subprocess.run(
                ["git", "diff", "--quiet", commit, "--", relative.replace("\\", "/")],
                cwd=ROOT,
                check=False,
            ).returncode
            == 0
        ):
            # Git's text checkout may preserve mixed line endings that cannot
            # be reconstructed by a simple LF/CRLF transform of the blob.
            matched_mode = "checkout_equivalent"
        if matched_mode:
            modes[matched_mode] = modes.get(matched_mode, 0) + 1
        else:
            mismatches.append(
                {"path": relative.replace("\\", "/"), "expected": expected, "actual_candidates": actuals}
            )
    return {
        "declared_files": len(freeze.get("files", {})),
        "verified_at_frozen_commit": len(freeze.get("files", {})) - len(mismatches),
        "hash_modes": modes,
        "mismatches": mismatches,
    }


def publication_state() -> dict[str, Any]:
    remote = run("git", "remote", "get-url", "origin")
    remote_refs = run("git", "ls-remote", "--heads", "--tags", "origin").splitlines()
    state: dict[str, Any] = {
        "origin": remote,
        "remote_refs": [{"sha": line.split()[0], "ref": line.split()[1]} for line in remote_refs],
    }
    try:
        state["github"] = json.loads(
            run(
                "gh",
                "repo",
                "view",
                "--json",
                "nameWithOwner,url,visibility,defaultBranchRef,isArchived,pushedAt",
            )
        )
        releases = run("gh", "release", "list", "--limit", "100", check=False)
        state["github_releases"] = releases.splitlines() if releases else []
    except (FileNotFoundError, subprocess.CalledProcessError, json.JSONDecodeError) as exc:
        state["github_error"] = str(exc)
    return state


def runtime_state() -> dict[str, Any]:
    versions = {}
    for package in PACKAGES:
        try:
            versions[package] = importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError:
            versions[package] = None
    return {
        "python": platform.python_version(),
        "implementation": platform.python_implementation(),
        "platform": platform.platform(),
        "packages": versions,
    }


def run_entry(run_dir: Path) -> dict[str, Any]:
    results_path = run_dir / "results.json"
    rows = json.loads(results_path.read_text(encoding="utf-8"))
    traces = sorted((run_dir / "traces").glob("*.json"))
    freeze_path = run_dir / "freeze.json"
    freeze = json.loads(freeze_path.read_text(encoding="utf-8")) if freeze_path.exists() else None
    variants = sorted({row["agent_variant"] for row in rows})
    tasks = sorted({row["task_id"] for row in rows})
    seeds = sorted({int(row.get("seed", 0)) for row in rows})
    raw_files = [results_path]
    for name in ("freeze.json", "report.md", "infrastructure-amendment.json", "infrastructure-cli-retry.json"):
        path = run_dir / name
        if path.exists():
            raw_files.append(path)
    analysis_dirs = [
        candidate
        for candidate in (run_dir / "analysis", run_dir.parent / f"{run_dir.name}-analysis")
        if candidate.is_dir()
    ]
    analysis_files = [path for directory in analysis_dirs for path in directory.rglob("*") if path.is_file()]
    entry = {
        "name": run_dir.name,
        "path": run_dir.relative_to(ROOT).as_posix(),
        "classification": (freeze or {}).get("purpose", "preserved run without freeze manifest"),
        "frozen": freeze is not None,
        "commit": (freeze or {}).get("commit"),
        "deployment": (freeze or {}).get("deployment"),
        "tasks": tasks,
        "variants": variants,
        "seed_indices": seeds,
        "result_rows": len(rows),
        "trace_files": len(traces),
        "complete_rectangular_coverage": len(rows) == len(tasks) * len(variants) * len(seeds) == len(traces),
        "raw_artifacts": {
            path.relative_to(ROOT).as_posix(): sha256(path) for path in raw_files
        },
        "trace_tree_sha256": tree_digest(traces),
        "analysis_outputs": {
            "files": [path.relative_to(ROOT).as_posix() for path in sorted(analysis_files)],
            "tree_sha256": tree_digest(analysis_files) if analysis_files else None,
        },
    }
    if freeze:
        entry["frozen_source_verification"] = freeze_verification(freeze)
    return entry


def build() -> dict[str, Any]:
    run_dirs = [
        path
        for path in sorted((ROOT / "outputs/runs").glob("transaction-*"))
        if (path / "results.json").exists() and (path / "traces").is_dir()
    ]
    derived_root = ROOT / "outputs/derived/illegitimate-block-v1"
    derived_files = sorted(derived_root.glob("*.json")) if derived_root.exists() else []
    publication = publication_state()
    remote_shas = {item["sha"] for item in publication["remote_refs"]}
    repository_head = run("git", "rev-parse", "HEAD")
    publication["recorded_head_published"] = repository_head in remote_shas
    runs = [run_entry(path) for path in run_dirs]
    return {
        "schema_version": 1,
        "scope": "transactional SAFE-Guard evidence and versioned offline illegitimate-block re-scores",
        "repository": {
            "head": repository_head,
            "branch": run("git", "branch", "--show-current"),
            "origin": run("git", "remote", "get-url", "origin"),
        },
        "publication": publication,
        "runtime": runtime_state(),
        "commands": {
            "rescore": "python scripts/rescore_illegitimate_blocks.py --all-transactional",
            "build_map": "python scripts/build_transaction_artifact_map.py",
            "verify_map": "python scripts/build_transaction_artifact_map.py --check",
            "tests": "python -m pytest tests/test_safety_metrics.py tests/test_transaction_artifact_map.py",
        },
        "configs": {
            path.relative_to(ROOT).as_posix(): sha256(path)
            for path in sorted((ROOT / "configs").glob("experiment.transaction.yaml"))
        },
        "tooling": {
            relative: sha256(ROOT / relative)
            for relative in (
                "src/safe_benchmark/evaluators/safety_metrics.py",
                "scripts/rescore_illegitimate_blocks.py",
                "scripts/build_transaction_artifact_map.py",
                "scripts/verify_frozen_run.py",
            )
        },
        "frozen_commits": sorted({item["commit"] for item in runs if item["commit"]}),
        "runs": runs,
        "derived_outputs": {
            path.relative_to(ROOT).as_posix(): sha256(path) for path in derived_files
        },
    }


def render_doc(payload: dict[str, Any]) -> str:
    lines = [
        "# Transactional SAFE-Guard artifact map",
        "",
        "This file is generated by `scripts/build_transaction_artifact_map.py`. It maps frozen source,",
        "preserved raw traces/results, analysis products, and versioned offline re-scores. Historical",
        "`results.json` and trace files are never rewritten by the re-score command.",
        "",
        "## Reproduce and verify",
        "",
        "```powershell",
        payload["commands"]["rescore"],
        payload["commands"]["build_map"],
        payload["commands"]["verify_map"],
        payload["commands"]["tests"],
        "```",
        "",
        "## Publication state",
        "",
        f"- Origin: `{payload['publication']['origin']}`",
        f"- Recorded local HEAD: `{payload['repository']['head']}`",
        f"- Recorded HEAD present on a remote ref: `{payload['publication']['recorded_head_published']}`",
        f"- Remote refs: {len(payload['publication']['remote_refs'])}",
        f"- GitHub releases: {len(payload['publication'].get('github_releases', []))}",
        "- The artifact map is present in this worktree; publication requires pushing the containing commit.",
        "",
        "## Preserved runs",
        "",
        "| Run | Frozen commit | Rows/traces | Variants | Frozen source hashes |",
        "|---|---|---:|---|---:|",
    ]
    for item in payload["runs"]:
        verification = item.get("frozen_source_verification", {})
        verified = f"{verification.get('verified_at_frozen_commit', 0)}/{verification.get('declared_files', 0)}"
        lines.append(
            f"| `{item['name']}` | `{item['commit'] or 'unfrozen'}` | "
            f"{item['result_rows']}/{item['trace_files']} | {', '.join(item['variants'])} | {verified} |"
        )
    lines.extend(
        [
            "",
            "The authoritative per-file SHA-256 values, task/seed coverage, analysis-output lists,",
            "runtime dependency versions, remote refs, and derived-output hashes are in",
            "`artifacts/transactional-safe-guard/artifact-map.json`.",
            "",
            "## Interpretation boundary",
            "",
            "Hash and coverage verification establishes artifact integrity only. It does not establish",
            "task-set independence, causal validity, safety adjudication quality, or effectiveness.",
            "The illegitimate-block outputs are retrospective derived metrics produced by the current",
            "evaluator and must not be represented as fields present in the historical raw results.",
            "",
        ]
    )
    return "\n".join(lines)


def verify(payload: dict[str, Any]) -> list[str]:
    errors = []
    for item in payload["runs"]:
        run_dir = ROOT / item["path"]
        for relative, expected in item["raw_artifacts"].items():
            path = ROOT / relative
            if not path.exists() or sha256(path) != expected:
                errors.append(f"raw artifact changed: {relative}")
        traces = sorted((run_dir / "traces").glob("*.json"))
        if len(traces) != item["trace_files"] or tree_digest(traces) != item["trace_tree_sha256"]:
            errors.append(f"trace set changed: {item['name']}")
        verification = item.get("frozen_source_verification")
        if verification and verification["mismatches"]:
            errors.append(f"frozen source mismatch: {item['name']}")
    for relative, expected in payload["derived_outputs"].items():
        path = ROOT / relative
        if not path.exists() or sha256(path) != expected:
            errors.append(f"derived output changed: {relative}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if args.check:
        payload = json.loads(MAP_PATH.read_text(encoding="utf-8"))
        errors = verify(payload)
        if errors:
            print("\n".join(errors))
            return 1
        print(f"verified {len(payload['runs'])} runs and {len(payload['derived_outputs'])} derived files")
        return 0

    payload = build()
    errors = verify(payload)
    if errors:
        raise SystemExit("\n".join(errors))
    MAP_DIR.mkdir(parents=True, exist_ok=True)
    MAP_PATH.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    DOC_PATH.write_text(render_doc(payload), encoding="utf-8")
    print(f"wrote {MAP_PATH.relative_to(ROOT)} and {DOC_PATH.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
