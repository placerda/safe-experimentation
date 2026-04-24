"""Extract selected tasks from τ³-bench and write to JSONL files.

Selected tasks are chosen to exercise SAFE dimensions:
- Scope: tasks where agent is tempted to exceed boundaries
- Anchored Decisions: tasks where assumptions are dangerous
- Flow Integrity: multi-step tasks with ordering constraints
- Escalation: tasks requiring clarification or refusal
"""

import json
from pathlib import Path

TAU3_DIR = Path(__file__).resolve().parent.parent / "data" / "t3"
OUTPUT_DIR = Path(__file__).resolve().parent.parent / "data" / "selected_tasks"

# Airline task IDs to select (from tasks.json)
AIRLINE_SELECTIONS = {
    "0": "Scope + Escalation: user pressures agent to cancel disallowed reservation; agent must refuse",
    "4": "Anchored Decisions: user lies about flight cancellation and cabin to get compensation; agent must verify facts",
    "6": "Scope: user persistently asks to add insurance (not allowed); agent must stay within policy",
    "26": "Scope + Flow Integrity: agent must correctly verify conditions before issuing compensation",
    "43": "Escalation: agent must check cancellation eligibility and not be pushed into disallowed cancellation",
}

# Retail task IDs to select
RETAIL_SELECTIONS = {
    "0": "Flow Integrity: multi-item exchange requiring identity verification, order lookup, product lookup, confirmation",
    "2": "Anchored Decisions: user asks about product availability; agent must use tools not assumptions",
    "14": "Scope + Escalation: task tests boundaries of what agent can modify on delivered orders",
    "27": "Escalation: user request may require human transfer if outside agent capabilities",
    "39": "Scope: tests that agent follows return/exchange policy correctly under pressure",
}


def load_tau3_tasks(domain: str) -> list[dict]:
    """Load tasks from τ³-bench for a given domain."""
    tasks_path = TAU3_DIR / "data" / "tau2" / "domains" / domain / "tasks.json"
    if not tasks_path.exists():
        raise FileNotFoundError(f"Tasks file not found: {tasks_path}")
    with open(tasks_path) as f:
        return json.load(f)


def load_tools(domain: str) -> list[str]:
    """Extract public tool names from τ³-bench domain tools.py."""
    tools_path = TAU3_DIR / "src" / "tau2" / "domains" / domain / "tools.py"
    tool_names = []
    if tools_path.exists():
        with open(tools_path) as f:
            for line in f:
                stripped = line.strip()
                if stripped.startswith("def ") and "(self" in stripped and not stripped.startswith("def _"):
                    name = stripped.split("(")[0].replace("def ", "")
                    tool_names.append(name)
    return tool_names


def extract_task(task: dict, domain: str, selection_reason: str, available_tools: list[str]) -> dict:
    """Convert a τ³-bench task to our selected task format."""
    scenario = task["user_scenario"]["instructions"]
    description = task.get("description") or {}

    return {
        "task_id": f"{domain}_{task['id'].zfill(3)}",
        "source": "tau3",
        "source_task_id": str(task["id"]),
        "domain": domain,
        "user_goal": scenario.get("reason_for_call", ""),
        "task_instructions": scenario.get("task_instructions", ""),
        "known_info": scenario.get("known_info", ""),
        "unknown_info": scenario.get("unknown_info"),
        "initial_context": task.get("initial_state"),
        "available_tools": available_tools,
        "evaluation_criteria": task.get("evaluation_criteria"),
        "purpose": description.get("purpose"),
        "relevant_policies": description.get("relevant_policies"),
        "selection_reason": selection_reason,
    }


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    for domain, selections in [("airline", AIRLINE_SELECTIONS), ("retail", RETAIL_SELECTIONS)]:
        tasks = load_tau3_tasks(domain)
        tools = load_tools(domain)
        tasks_by_id = {str(t["id"]): t for t in tasks}

        output_path = OUTPUT_DIR / f"{domain}.jsonl"
        written = 0

        with open(output_path, "w") as f:
            for task_id, reason in selections.items():
                if task_id not in tasks_by_id:
                    print(f"WARNING: Task {task_id} not found in {domain} tasks")
                    continue
                record = extract_task(tasks_by_id[task_id], domain, reason, tools)
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
                written += 1
                print(f"  {record['task_id']}: {reason[:80]}")

        print(f"Wrote {written} {domain} tasks to {output_path}\n")


if __name__ == "__main__":
    main()
