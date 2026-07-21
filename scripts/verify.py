#!/usr/bin/env python3
"""Run the repository checks expected before pushes and releases."""

from __future__ import annotations

import argparse
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]


def run_step(name: str, command: list[str]) -> None:
    printable = " ".join(command)
    print(f"\n==> {name}")
    print(f"$ {printable}")
    subprocess.run(command, cwd=ROOT, check=True)


def verification_steps() -> list[tuple[str, list[str]]]:
    py = sys.executable
    return [
        (
            "Compile Python entrypoints",
            [
                py,
                "-m",
                "py_compile",
                "install.py",
                "plugins/hashmicro-imagegen-native/scripts/mcp_server.py",
                "scripts/bootstrap.py",
                "scripts/smoke_mcp.py",
                "scripts/smoke_install.py",
                "scripts/build_release.py",
                "scripts/versioning.py",
                "scripts/verify.py",
                "scripts/setup_hooks.py",
            ],
        ),
        ("Unit tests", [py, "-m", "unittest", "discover", "-s", "tests", "-v"]),
        ("MCP smoke test", [py, "scripts/smoke_mcp.py"]),
        ("Version consistency", [py, "scripts/versioning.py", "check"]),
        ("Build release bundle", [py, "scripts/build_release.py"]),
        ("Installer smoke test", [py, "scripts/smoke_install.py"]),
    ]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--pre-push",
        action="store_true",
        help="Print hook-oriented wording; runs the same full verification suite.",
    )
    args = parser.parse_args()

    if args.pre_push:
        print("Running pre-push verification. Set SKIP_PRE_PUSH_VERIFY=1 only for emergency bypasses.")

    for name, command in verification_steps():
        run_step(name, command)

    print("\nVerification passed.")


if __name__ == "__main__":
    main()
