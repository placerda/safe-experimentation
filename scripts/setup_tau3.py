"""Clone and install τ³-bench locally into data/t3/."""

import subprocess
import sys
from pathlib import Path

REPO_URL = "https://github.com/sierra-research/tau2-bench.git"
TARGET_DIR = Path(__file__).resolve().parent.parent / "data" / "t3"


def main() -> None:
    if (TARGET_DIR / ".git").exists():
        print(f"τ³-bench already cloned at {TARGET_DIR}")
        print("Pulling latest changes...")
        subprocess.run(["git", "pull"], cwd=TARGET_DIR, check=True)
    else:
        print(f"Cloning τ³-bench into {TARGET_DIR}...")
        TARGET_DIR.mkdir(parents=True, exist_ok=True)
        subprocess.run(
            ["git", "clone", REPO_URL, str(TARGET_DIR)],
            check=True,
        )

    # Check if uv is available; fall back to pip if not
    uv_available = subprocess.run(["uv", "--version"], capture_output=True).returncode == 0

    if uv_available:
        print("Installing τ³-bench with uv...")
        subprocess.run(["uv", "sync"], cwd=TARGET_DIR, check=True)
    else:
        print("uv not found — installing τ³-bench with pip...")
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "-e", str(TARGET_DIR)],
            check=True,
        )

    print("✓ τ³-bench setup complete.")


if __name__ == "__main__":
    main()
