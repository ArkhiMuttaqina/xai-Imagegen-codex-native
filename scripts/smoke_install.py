#!/usr/bin/env python3
"""Offline smoke test for the built release installer on the current platform."""

from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import zipfile


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "plugins" / "hashmicro-imagegen-native" / ".codex-plugin" / "plugin.json"


def main() -> None:
    version = json.loads(MANIFEST.read_text(encoding="utf-8"))["version"]
    archive = ROOT / "dist" / f"hashmicro-imagegen-share-v{version}.zip"
    if not archive.is_file():
        raise SystemExit(f"Build the release first: {archive}")

    with tempfile.TemporaryDirectory(prefix="hashmicro-install-smoke-") as raw:
        temp = Path(raw)
        extracted = temp / "release"
        extracted.mkdir()
        with zipfile.ZipFile(archive) as bundle:
            bundle.extractall(extracted)
        installers = list(extracted.glob("*/install.py"))
        if len(installers) != 1:
            raise SystemExit("Release must contain exactly one installer")

        fake_home = temp / "home"
        fake_codex_home = fake_home / ".codex"
        environment = os.environ.copy()
        environment.update({
            "HOME": str(fake_home),
            "USERPROFILE": str(fake_home),
            "CODEX_HOME": str(fake_codex_home),
        })
        subprocess.run(
            [sys.executable, str(installers[0]), "--skip-credentials", "--skip-codex", "--yes"],
            check=True,
            env=environment,
        )

        installed = fake_home / ".codex" / "local-plugins" / "hashmicro-imagegen-share"
        required = (
            installed / ".agents" / "plugins" / "marketplace.json",
            installed / "plugins" / "hashmicro-imagegen-native" / ".codex-plugin" / "plugin.json",
            installed / "plugins" / "hashmicro-imagegen-native" / ".mcp.json",
            fake_codex_home / ".env",
        )
        missing = [str(path) for path in required if not path.is_file()]
        if missing:
            raise SystemExit("Installer smoke test missing files: " + ", ".join(missing))

    print(f"Installer smoke test passed for v{version} on {sys.platform} / Python {sys.version.split()[0]}")


if __name__ == "__main__":
    main()
