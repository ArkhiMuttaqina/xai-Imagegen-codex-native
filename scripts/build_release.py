#!/usr/bin/env python3
"""Build a deterministic shareable ZIP and SHA-256 file."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import zipfile


ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / "plugins" / "hashmicro-imagegen-native"
MANIFEST = PLUGIN / ".codex-plugin" / "plugin.json"
RELEASE_FILES = (
    "AGENTS.md",
    "brand.png",
    "install.py",
    "LICENSE",
    ".agents/plugins/marketplace.json",
    "project.md",
    "README.md",
    "CHANGELOG.md",
    "scripts/bootstrap.py",
    "plugins/hashmicro-imagegen-native/.mcp.json",
    "plugins/hashmicro-imagegen-native/.codex-plugin/plugin.json",
    "plugins/hashmicro-imagegen-native/scripts/mcp_server.py",
    "plugins/hashmicro-imagegen-native/skills/hashmicro-native-imagegen/SKILL.md",
)


def main() -> None:
    version = json.loads(MANIFEST.read_text(encoding="utf-8"))["version"]
    archive_root = f"hashmicro-imagegen-share-v{version}"
    dist = ROOT / "dist"
    dist.mkdir(exist_ok=True)
    output = dist / f"{archive_root}.zip"
    if output.exists():
        output.unlink()

    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for relative in RELEASE_FILES:
            source = ROOT / relative
            if not source.is_file():
                raise SystemExit(f"Missing release file: {relative}")
            info = zipfile.ZipInfo(f"{archive_root}/{relative}", date_time=(2026, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            archive.writestr(info, source.read_bytes(), compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)

    digest = hashlib.sha256(output.read_bytes()).hexdigest()
    checksum = output.with_suffix(".sha256.txt")
    checksum.write_text(f"{digest}  {output.name}\n", encoding="utf-8", newline="\n")
    print(output)
    print(checksum)
    print(digest)


if __name__ == "__main__":
    main()
