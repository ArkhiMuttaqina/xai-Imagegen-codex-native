#!/usr/bin/env python3
"""Enable the repository-managed Git hooks for the current clone."""

from __future__ import annotations

from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    subprocess.run(["git", "config", "core.hooksPath", ".githooks"], cwd=ROOT, check=True)
    print("Enabled repository Git hooks via core.hooksPath=.githooks")
    print("Future git pushes will run: python scripts/verify.py --pre-push")


if __name__ == "__main__":
    main()
