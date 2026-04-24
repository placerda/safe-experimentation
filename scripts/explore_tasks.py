"""Explore available tasks in τ³-bench for airline and retail domains.

Prints task IDs, user goals, and available tools to help with task selection.
"""

import json
import sys
from pathlib import Path

# Add τ³-bench to path so we can import its modules
TAU3_DIR = Path(__file__).resolve().parent.parent / "data" / "t3"


def try_load_tasks_via_tau2() -> bool:
    """Try loading tasks using τ³-bench's own API."""
    try:
        sys.path.insert(0, str(TAU3_DIR / "src"))
        from tau2.domains import load_domain

        for domain_name in ["airline", "retail"]:
            print(f"\n{'='*60}")
            print(f"Domain: {domain_name}")
            print(f"{'='*60}")

            domain = load_domain(domain_name)
            tasks = domain.tasks

            print(f"Total tasks: {len(tasks)}\n")
            for i, task in enumerate(tasks):
                print(f"  [{i}] ID: {getattr(task, 'id', i)}")
                if hasattr(task, "user_instruction"):
                    goal = task.user_instruction[:120]
                    print(f"      Goal: {goal}...")
                if hasattr(task, "tools") and task.tools:
                    print(f"      Tools: {[t.name if hasattr(t, 'name') else str(t) for t in task.tools[:5]]}")
                print()
        return True
    except Exception as e:
        print(f"Could not load via tau2 API: {e}")
        return False


def try_load_tasks_from_files() -> bool:
    """Fallback: scan for task JSON/JSONL files in τ³-bench."""
    task_dirs = list(TAU3_DIR.rglob("*tasks*"))
    task_files = [f for f in TAU3_DIR.rglob("*.json") if "task" in f.name.lower()]
    task_files += [f for f in TAU3_DIR.rglob("*.jsonl") if "task" in f.name.lower()]

    if not task_dirs and not task_files:
        print("No task files found. Is τ³-bench installed? Run: python scripts/setup_tau3.py")
        return False

    print("Found task-related paths:")
    for p in sorted(set(task_dirs + task_files))[:20]:
        print(f"  {p.relative_to(TAU3_DIR)}")

    for f in task_files[:5]:
        print(f"\nSample from {f.name}:")
        if f.suffix == ".jsonl":
            with open(f) as fh:
                for line in list(fh)[:3]:
                    data = json.loads(line)
                    print(f"  Keys: {list(data.keys())}")
                    if "user_goal" in data:
                        print(f"  Goal: {data['user_goal'][:100]}")
        elif f.suffix == ".json":
            with open(f) as fh:
                data = json.load(fh)
                if isinstance(data, list):
                    print(f"  {len(data)} tasks, keys: {list(data[0].keys()) if data else 'empty'}")
                else:
                    print(f"  Keys: {list(data.keys())}")
    return True


def main() -> None:
    if not TAU3_DIR.exists() or not (TAU3_DIR / ".git").exists():
        print("τ³-bench not found. Run first: python scripts/setup_tau3.py")
        sys.exit(1)

    print(f"tau3-bench directory: {TAU3_DIR}")
    if not try_load_tasks_via_tau2():
        try_load_tasks_from_files()


if __name__ == "__main__":
    main()
