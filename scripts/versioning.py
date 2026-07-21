#!/usr/bin/env python3
"""Semantic-version management for the plugin and release workflows."""

from __future__ import annotations

import argparse
from datetime import date
import json
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "plugins" / "hashmicro-imagegen-native" / ".codex-plugin" / "plugin.json"
SERVER = ROOT / "plugins" / "hashmicro-imagegen-native" / "scripts" / "mcp_server.py"
README = ROOT / "README.md"
CHANGELOG = ROOT / "CHANGELOG.md"
SEMVER = re.compile(r"^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)$")


def current_version() -> str:
    version = str(json.loads(MANIFEST.read_text(encoding="utf-8"))["version"])
    if not SEMVER.fullmatch(version):
        raise SystemExit(f"Manifest version is not stable SemVer: {version}")
    return version


def server_version() -> str:
    match = re.search(r'^SERVER_VERSION = "([^"]+)"$', SERVER.read_text(encoding="utf-8"), re.MULTILINE)
    if not match:
        raise SystemExit("SERVER_VERSION was not found")
    return match.group(1)


def bump_semver(version: str, part: str) -> str:
    match = SEMVER.fullmatch(version)
    if not match:
        raise ValueError(f"Invalid SemVer: {version}")
    major, minor, patch = (int(value) for value in match.groups())
    if part == "major":
        return f"{major + 1}.0.0"
    if part == "minor":
        return f"{major}.{minor + 1}.0"
    if part == "patch":
        return f"{major}.{minor}.{patch + 1}"
    raise ValueError(f"Unknown bump type: {part}")


def classify_branch(branch: str, manual: str = "") -> str:
    if manual in {"patch", "minor", "major"}:
        return manual
    normalized = branch.strip().lower()
    mappings = (
        (("breaking/", "major/"), "major"),
        (("feat/", "feature/"), "minor"),
        (("fix/", "bugfix/", "hotfix/", "patch/"), "patch"),
    )
    for prefixes, bump in mappings:
        if normalized.startswith(prefixes):
            return bump
    return "none"


def classify_message(message: str) -> str:
    normalized = message.strip().lower()
    if "breaking change:" in normalized or re.match(r"^[a-z]+(?:\([^)]*\))?!:", normalized):
        return "major"
    if re.match(r"^feat(?:\([^)]*\))?:", normalized):
        return "minor"
    if re.match(r"^(fix|perf|refactor)(?:\([^)]*\))?:", normalized):
        return "patch"
    return "none"


def select_release_bump(branch: str = "", message: str = "", manual: str = "") -> str:
    if manual in {"patch", "minor", "major"}:
        return manual
    branch_bump = classify_branch(branch)
    if branch_bump != "none":
        return branch_bump
    message_bump = classify_message(message)
    if message_bump != "none":
        return message_bump
    return "patch"


def check(tag: str = "") -> str:
    manifest = current_version()
    runtime = server_version()
    if manifest != runtime:
        raise SystemExit(f"Version mismatch: manifest={manifest}, server={runtime}")
    if tag:
        normalized = tag[1:] if tag.startswith("v") else tag
        if normalized != manifest:
            raise SystemExit(f"Tag mismatch: tag={tag}, source={manifest}")
    return manifest


def replace_server_version(old: str, new: str) -> None:
    text = SERVER.read_text(encoding="utf-8")
    updated, count = re.subn(
        rf'^SERVER_VERSION = "{re.escape(old)}"$',
        f'SERVER_VERSION = "{new}"',
        text,
        count=1,
        flags=re.MULTILINE,
    )
    if count != 1:
        raise SystemExit("Could not update SERVER_VERSION exactly once")
    SERVER.write_text(updated, encoding="utf-8", newline="\n")


def update_version(part: str, summary: str) -> str:
    old = check()
    new = bump_semver(old, part)

    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    manifest["version"] = new
    MANIFEST.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8", newline="\n")
    replace_server_version(old, new)

    readme = README.read_text(encoding="utf-8")
    readme = readme.replace(f"v{old}", f"v{new}").replace(f"`{old}`", f"`{new}`")
    README.write_text(readme, encoding="utf-8", newline="\n")

    changelog = CHANGELOG.read_text(encoding="utf-8")
    heading = f"## {new} - {date.today().isoformat()}\n\n- {summary.strip() or 'Automated release.'}\n\n"
    if changelog.startswith("# Changelog\n\n"):
        changelog = "# Changelog\n\n" + heading + changelog[len("# Changelog\n\n"):]
    else:
        changelog = "# Changelog\n\n" + heading + changelog
    CHANGELOG.write_text(changelog, encoding="utf-8", newline="\n")
    return new


def main() -> None:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)

    check_parser = subparsers.add_parser("check")
    check_parser.add_argument("--tag", default="")

    classify_parser = subparsers.add_parser("classify")
    classify_parser.add_argument("--branch", default="")
    classify_parser.add_argument("--manual", default="")

    select_parser = subparsers.add_parser("select")
    select_parser.add_argument("--branch", default="")
    select_parser.add_argument("--message", default="")
    select_parser.add_argument("--manual", default="")

    bump_parser = subparsers.add_parser("bump")
    bump_parser.add_argument("part", choices=["patch", "minor", "major"])
    bump_parser.add_argument("--summary", default="Automated release.")

    args = parser.parse_args()
    if args.command == "check":
        print(check(args.tag))
    elif args.command == "classify":
        print(classify_branch(args.branch, args.manual))
    elif args.command == "select":
        print(select_release_bump(args.branch, args.message, args.manual))
    else:
        print(update_version(args.part, args.summary))


if __name__ == "__main__":
    main()
