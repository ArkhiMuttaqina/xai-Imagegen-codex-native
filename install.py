#!/usr/bin/env python3
"""Cross-platform installer for the HashMicro XAI Codex plugin."""

from __future__ import annotations

import argparse
import getpass
import json
import os
from pathlib import Path
import shutil
import shlex
import subprocess
import sys


BUNDLE_NAME = "hashmicro-imagegen-share"
PLUGIN_NAME = "hashmicro-imagegen-native"
MARKETPLACE_NAME = "hashmicro-xai-local"
ENV_DEFAULTS = {
    "XAI_URL": "",
    "XAI_HASHMICRO_API_KEY": "",
    "XAI_IMAGE_MODEL": "codex/gpt-5.6-sol",
}


def marketplace_manifest(bundle: Path) -> Path:
    return bundle / ".agents" / "plugins" / "marketplace.json"


def validate_bundle_layout(bundle: Path) -> Path:
    root = bundle.resolve()
    marketplace_path = marketplace_manifest(root)
    if not marketplace_path.is_file():
        raise SystemExit(f"Missing Codex marketplace manifest: {marketplace_path}")
    try:
        marketplace = json.loads(marketplace_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SystemExit(f"Invalid Codex marketplace manifest: {exc}") from exc
    if marketplace.get("name") != MARKETPLACE_NAME:
        raise SystemExit(f"Marketplace name must be {MARKETPLACE_NAME!r}")
    entries = [entry for entry in marketplace.get("plugins", []) if entry.get("name") == PLUGIN_NAME]
    if len(entries) != 1:
        raise SystemExit(f"Marketplace must contain exactly one {PLUGIN_NAME!r} entry")
    source = entries[0].get("source") or {}
    if source.get("source") != "local" or source.get("path") != f"./plugins/{PLUGIN_NAME}":
        raise SystemExit("Marketplace plugin source must use the canonical local plugin path")

    plugin = (root / "plugins" / PLUGIN_NAME).resolve()
    if root not in plugin.parents or not plugin.is_dir():
        raise SystemExit(f"Plugin directory is missing or unsafe: {plugin}")
    manifest_path = plugin / ".codex-plugin" / "plugin.json"
    server_path = plugin / "scripts" / "mcp_server.py"
    skill_path = plugin / "skills" / "hashmicro-native-imagegen" / "SKILL.md"
    for required in (manifest_path, server_path, skill_path):
        if not required.is_file():
            raise SystemExit(f"Required plugin file is missing: {required}")
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SystemExit(f"Invalid plugin manifest: {exc}") from exc
    if manifest.get("name") != PLUGIN_NAME or not manifest.get("version"):
        raise SystemExit("Plugin manifest name/version is invalid")
    return marketplace_path


def format_command(parts: list[str]) -> str:
    if os.name == "nt":
        return subprocess.list2cmdline(parts)
    return " ".join(shlex.quote(part) for part in parts)


def codex_executable() -> str | None:
    candidates = ["codex.cmd", "codex.exe", "codex"] if os.name == "nt" else ["codex"]
    for candidate in candidates:
        resolved = shutil.which(candidate)
        if resolved:
            return resolved
    return None


def run_capture(parts: list[str], *, check: bool = True) -> subprocess.CompletedProcess[str]:
    actual = list(parts)
    if actual and actual[0] == "codex":
        resolved = codex_executable()
        if not resolved:
            raise SystemExit("Codex CLI is not on PATH.")
        actual[0] = resolved
    result = subprocess.run(actual, text=True, capture_output=True)
    if check and result.returncode != 0:
        combined = "\n".join(part for part in (result.stdout, result.stderr) if part.strip())
        raise SystemExit(f"Command failed: {format_command(parts)}\n{combined}".rstrip())
    return result


def copy_bundle(source: Path, destination: Path) -> Path:
    if source.resolve() == destination.resolve():
        return destination
    if destination.exists():
        shutil.rmtree(destination)
    shutil.copytree(source, destination, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    return destination


def configure_mcp(bundle: Path) -> None:
    plugin = bundle / "plugins" / PLUGIN_NAME
    server = (plugin / "scripts" / "mcp_server.py").resolve()
    config = {
        "mcpServers": {
            "hashmicro_imagegen": {
                "command": str(Path(sys.executable).resolve()),
                "args": [str(server)],
                "startup_timeout_sec": 15,
                "tool_timeout_sec": 900,
            }
        }
    }
    (plugin / ".mcp.json").write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")


def parse_env(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.exists():
        return values
    for raw in path.read_text(encoding="utf-8-sig").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip("'\"")
    return values


def codex_env_path() -> Path:
    codex_home = os.getenv("CODEX_HOME", "").strip()
    return (Path(codex_home).expanduser() if codex_home else Path.home() / ".codex") / ".env"


def ensure_env_template() -> Path:
    env_path = codex_env_path()
    env_path.parent.mkdir(parents=True, exist_ok=True)
    lines = env_path.read_text(encoding="utf-8-sig").splitlines() if env_path.exists() else []
    existing = {
        line.split("=", 1)[0].strip()
        for line in lines
        if line.strip() and not line.lstrip().startswith("#") and "=" in line
    }
    missing = [key for key in ENV_DEFAULTS if key not in existing]
    if missing:
        if lines and lines[-1].strip():
            lines.append("")
        lines.append("# HashMicro XAI Image Gen")
        lines.extend(f"{key}={json.dumps(ENV_DEFAULTS[key])}" for key in missing)
        env_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8", newline="\n")
    return env_path


def update_env(skip: bool) -> None:
    env_path = ensure_env_template()
    if skip:
        print("\nCredential template is ready.")
        print(f"Edit this file: {env_path}")
        print("Fill XAI_URL and XAI_HASHMICRO_API_KEY, then restart Codex.")
        return
    current = parse_env(env_path)
    url = os.getenv("XAI_URL") or current.get("XAI_URL") or input("XAI_URL: ").strip()
    key = os.getenv("XAI_HASHMICRO_API_KEY") or current.get("XAI_HASHMICRO_API_KEY")
    if not key:
        key = getpass.getpass("XAI_HASHMICRO_API_KEY (input hidden): ").strip()
    if not url or not key:
        raise SystemExit("XAI_URL and XAI_HASHMICRO_API_KEY are required.")

    preserved = []
    if env_path.exists():
        for raw in env_path.read_text(encoding="utf-8-sig").splitlines():
            if not raw.lstrip().startswith(("XAI_URL=", "XAI_HASHMICRO_API_KEY=")):
                preserved.append(raw)
    preserved.extend([
        f"XAI_URL={json.dumps(url)}",
        f"XAI_HASHMICRO_API_KEY={json.dumps(key)}",
    ])
    env_path.write_text("\n".join(preserved).rstrip() + "\n", encoding="utf-8")


def installed_hashmicro_marketplaces() -> list[str]:
    result = run_capture(["codex", "plugin", "list"])
    marketplaces: list[str] = []
    for raw in result.stdout.splitlines():
        line = raw.strip()
        if not line.startswith(f"{PLUGIN_NAME}@"):
            continue
        if "not installed" in line or "installed" not in line:
            continue
        marketplaces.append(line.split()[0].split("@", 1)[1])
    return sorted(set(marketplaces))


def configured_marketplaces() -> set[str]:
    result = run_capture(["codex", "plugin", "marketplace", "list"])
    return {
        line.split()[0]
        for line in result.stdout.splitlines()[1:]
        if line.strip()
    }


def confirm_migration(marketplaces: list[str], assume_yes: bool) -> bool:
    if not marketplaces or assume_yes:
        return True
    print("\nExisting HashMicro plugin installs were detected:")
    for marketplace in marketplaces:
        print(f"- {PLUGIN_NAME}@{marketplace}")
    print("\nThey must be removed first to avoid duplicate MCP server and skill names.")
    if not sys.stdin.isatty():
        return False
    answer = input("Remove the existing installs and continue? [y/N]: ").strip().lower()
    return answer in {"y", "yes"}


def print_manual_commands(bundle: Path, marketplaces: list[str] | None = None) -> None:
    print("\nCodex CLI was not run. Execute these commands manually after reviewing them:")
    for marketplace in marketplaces or []:
        print(format_command(["codex", "plugin", "remove", f"{PLUGIN_NAME}@{marketplace}"]))
    print(format_command(["codex", "plugin", "marketplace", "remove", MARKETPLACE_NAME]))
    print(format_command(["codex", "plugin", "marketplace", "add", str(bundle)]))
    print(format_command(["codex", "plugin", "add", f"{PLUGIN_NAME}@{MARKETPLACE_NAME}"]))


def run_codex(bundle: Path, *, skip: bool, assume_yes: bool) -> None:
    if skip or not codex_executable():
        print_manual_commands(bundle)
        return

    installed = installed_hashmicro_marketplaces()
    marketplaces = configured_marketplaces()
    if installed and not confirm_migration(installed, assume_yes):
        print_manual_commands(bundle, installed)
        raise SystemExit("Aborted before changing Codex plugin installation.")

    for marketplace in installed:
        run_capture(["codex", "plugin", "remove", f"{PLUGIN_NAME}@{marketplace}"])

    if MARKETPLACE_NAME in marketplaces:
        run_capture(["codex", "plugin", "marketplace", "remove", MARKETPLACE_NAME])

    run_capture(["codex", "plugin", "marketplace", "add", str(bundle)])
    run_capture(["codex", "plugin", "add", f"{PLUGIN_NAME}@{MARKETPLACE_NAME}"])
    print(f"Marketplace: {marketplace_manifest(bundle)}")


def install_bundle(
    source: Path,
    destination: Path,
    *,
    skip_credentials: bool,
    skip_codex: bool,
    assume_yes: bool,
) -> Path:
    validate_bundle_layout(source)
    destination.parent.mkdir(parents=True, exist_ok=True)
    bundle = copy_bundle(source, destination)
    configure_mcp(bundle)
    validate_bundle_layout(bundle)
    run_codex(bundle, skip=skip_codex, assume_yes=assume_yes)
    update_env(skip_credentials)
    return bundle


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--skip-credentials", action="store_true")
    parser.add_argument("--skip-codex", action="store_true")
    parser.add_argument("--yes", action="store_true", help="remove existing HashMicro plugin installs without prompting")
    args = parser.parse_args()

    source = Path(__file__).resolve().parent
    destination = Path.home() / ".codex" / "local-plugins" / BUNDLE_NAME
    bundle = install_bundle(
        source,
        destination,
        skip_credentials=args.skip_credentials,
        skip_codex=args.skip_codex,
        assume_yes=args.yes,
    )
    print("\nInstalled. Restart Codex and open a new task to use the plugin.")
    print(f"Installed files: {bundle}")


if __name__ == "__main__":
    main()
