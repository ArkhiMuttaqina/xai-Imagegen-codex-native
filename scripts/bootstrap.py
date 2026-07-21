#!/usr/bin/env python3
"""Download, verify, and install the latest HashMicro imagegen release."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import urllib.request
import zipfile


REPOSITORY = "ArkhiMuttaqina/xai-Imagegen-codex-native"
LATEST_RELEASE_API = f"https://api.github.com/repos/{REPOSITORY}/releases/latest"
USER_AGENT = "hashmicro-imagegen-bootstrap"


def download(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/vnd.github+json"})
    with urllib.request.urlopen(request, timeout=120) as response:
        return response.read()


def release_assets(release: dict) -> tuple[dict, dict]:
    assets = release.get("assets") or []
    zip_assets = [asset for asset in assets if str(asset.get("name", "")).endswith(".zip")]
    checksum_assets = [asset for asset in assets if str(asset.get("name", "")).endswith(".sha256.txt")]
    if len(zip_assets) != 1 or len(checksum_assets) != 1:
        raise SystemExit("Latest release must contain exactly one ZIP and one SHA-256 file.")
    return zip_assets[0], checksum_assets[0]


def verify_archive(archive: bytes, checksum: bytes, archive_name: str) -> None:
    line = checksum.decode("utf-8-sig").strip().splitlines()[0]
    parts = line.split()
    if len(parts) < 2 or parts[-1] != archive_name:
        raise SystemExit("Release checksum file does not match the archive name.")
    expected = parts[0].lower()
    actual = hashlib.sha256(archive).hexdigest()
    if actual != expected:
        raise SystemExit(f"Release checksum mismatch: expected {expected}, received {actual}")


def safe_extract(archive_path: Path, destination: Path) -> None:
    root = destination.resolve()
    with zipfile.ZipFile(archive_path) as archive:
        for member in archive.infolist():
            target = (destination / member.filename).resolve()
            if target != root and root not in target.parents:
                raise SystemExit(f"Unsafe path in release archive: {member.filename}")
        archive.extractall(destination)


def main() -> None:
    print(f"Fetching latest release from https://github.com/{REPOSITORY} ...")
    release = json.loads(download(LATEST_RELEASE_API).decode("utf-8"))
    zip_asset, checksum_asset = release_assets(release)
    archive_name = zip_asset["name"]
    archive = download(zip_asset["browser_download_url"])
    checksum = download(checksum_asset["browser_download_url"])
    verify_archive(archive, checksum, archive_name)
    print(f"Verified {archive_name}")

    with tempfile.TemporaryDirectory(prefix="hashmicro-imagegen-") as raw:
        temp = Path(raw)
        archive_path = temp / archive_name
        archive_path.write_bytes(archive)
        extracted = temp / "release"
        extracted.mkdir()
        safe_extract(archive_path, extracted)
        installers = list(extracted.glob("*/install.py"))
        if len(installers) != 1:
            raise SystemExit("Release archive did not contain exactly one installer.")
        subprocess.run(
            [sys.executable, str(installers[0]), "--skip-credentials", "--yes"],
            check=True,
        )

    codex_home = os.getenv("CODEX_HOME", "").strip()
    env_path = ((Path(codex_home).expanduser() if codex_home else Path.home() / ".codex") / ".env").resolve()
    print("\nInstallation complete.")
    print(f"Credential file: {env_path}")
    print("Fill XAI_URL and XAI_HASHMICRO_API_KEY, restart Codex, then open a new task.")


if __name__ == "__main__":
    main()
