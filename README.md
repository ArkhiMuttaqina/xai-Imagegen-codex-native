<div align="center">
  <img src="brand.png" alt="HashMicro XAI Image Gen for Codex" width="520">

  # HashMicro XAI Image Gen for Codex v0.1.8

  [![CI](https://github.com/ArkhiMuttaqina/xai-Imagegen-codex-native/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/ArkhiMuttaqina/xai-Imagegen-codex-native/actions/workflows/ci.yml)
  [![Latest Release](https://img.shields.io/github/v/release/ArkhiMuttaqina/xai-Imagegen-codex-native?display_name=tag&sort=semver)](https://github.com/ArkhiMuttaqina/xai-Imagegen-codex-native/releases/latest)
  [![Release Workflow](https://img.shields.io/github/actions/workflow/status/ArkhiMuttaqina/xai-Imagegen-codex-native/tag-release.yml?label=release)](https://github.com/ArkhiMuttaqina/xai-Imagegen-codex-native/actions/workflows/tag-release.yml)
  [![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
  [![Platforms](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-5E5E5E)](https://github.com/ArkhiMuttaqina/xai-Imagegen-codex-native/actions/workflows/ci.yml)
  [![License: Proprietary](https://img.shields.io/badge/license-Proprietary-red)](LICENSE)

  Native HashMicro XAI image generation and background editing for Codex.
</div>

Portable ZIP bundle for Windows, macOS, and Linux. The MCP server uses only the Python standard library; no `pip install` is required.

The CI badge covers the selected build matrix: Windows, macOS, and Linux on Python 3.10, 3.13, and 3.14. A green badge means all nine platform/runtime jobs passed on `main`.

## What's new

- Detects existing HashMicro plugin installs and asks before removing them, preventing duplicate MCP and skill names.
- Accepts aspect ratios such as `9:16`, `16:9`, `3:4`, and `1:1`, then maps them to gateway-safe sizes.
- Keeps completed background edit results pollable for a limited TTL.
- Adds configurable request timeout and clearer network diagnostics.

## Requirements

- Codex Desktop/CLI
- Python 3.10 or newer
- HashMicro XAI gateway URL and API key
- Network access to the gateway

Do not share your API key inside this ZIP. Each user should use their own credentials.

## Repository layout

```text
.
├── AGENTS.md
├── brand.png
├── install.py
├── LICENSE
├── .agents/plugins/marketplace.json
├── project.md
├── plugins/hashmicro-imagegen-native/
│   ├── .codex-plugin/plugin.json
│   ├── .mcp.json
│   ├── scripts/mcp_server.py
│   └── skills/hashmicro-native-imagegen/SKILL.md
├── scripts/
│   ├── build_release.py
│   ├── bootstrap.py
│   └── smoke_mcp.py
└── tests/
```

The runtime intentionally uses only Python's standard library.

## Quick install or update

The same bootstrap command handles both a first-time installation and future updates:

- **First install:** downloads the Latest GitHub Release, verifies its SHA-256 checksum, installs the marketplace/plugin, and creates `~/.codex/.env` when it does not exist.
- **Update:** downloads the newest Latest Release, replaces the installed plugin files, reinstalls the marketplace/plugin registration, and preserves the existing `~/.codex/.env` credentials.

### One-line from an agent (Codex CLI / ChatGPT Desktop prompt)

Paste this into any shell-capable AI agent:

```text
Install or update the HashMicro XAI Image Gen plugin for Codex to the latest release from the official repository ArkhiMuttaqina/xai-Imagegen-codex-native. Detect my operating system and run the appropriate verified bootstrap command below exactly once. Preserve my existing .env credentials during an update. Do not ask me to paste credentials into chat. If the command exits nonzero, report the exact error and stop; do not manually patch the downloaded or installed package. After it succeeds, show the installed plugin version and the exact local .env path. If required values are missing, tell me to fill XAI_URL and XAI_HASHMICRO_API_KEY in that file. Then tell me to restart Codex and open a new task.

macOS/Linux:
curl -fsSL https://raw.githubusercontent.com/ArkhiMuttaqina/xai-Imagegen-codex-native/main/scripts/bootstrap.py | python3 -

Windows PowerShell:
curl.exe -fsSL https://raw.githubusercontent.com/ArkhiMuttaqina/xai-Imagegen-codex-native/main/scripts/bootstrap.py | py -
```

### Run it directly

Windows PowerShell:

```powershell
curl.exe -fsSL https://raw.githubusercontent.com/ArkhiMuttaqina/xai-Imagegen-codex-native/main/scripts/bootstrap.py | py -
```

macOS/Linux:

```bash
curl -fsSL https://raw.githubusercontent.com/ArkhiMuttaqina/xai-Imagegen-codex-native/main/scripts/bootstrap.py | python3 -
```

The bootstrap always resolves GitHub's Latest Release rather than trusting the repository folder name. It verifies the published checksum before safely extracting and installing the bundle.

### After the first install

After it finishes, edit the path printed by the installer. The default location is:

- Windows: `%USERPROFILE%\.codex\.env`
- macOS/Linux: `~/.codex/.env`

Fill these values locally:

```dotenv
XAI_URL="https://your-gateway.example"
XAI_HASHMICRO_API_KEY="your-personal-key"
XAI_IMAGE_MODEL="codex/gpt-5.6-sol"
```

Never paste the API key into an AI chat or commit the `.env` file.

Restart Codex completely and open a new task so the newly installed plugin and MCP server are loaded.

### Updating an existing install

Run the same command or paste the same agent prompt again. You do not need to uninstall the previous version first.

During an update, the installer:

1. Downloads and verifies the current Latest Release.
2. Replaces the local plugin bundle and refreshes Codex registration.
3. Keeps the existing values in `~/.codex/.env`.
4. Reports the installed version and asks you to restart Codex.

Verify the active installation after restarting:

```bash
codex plugin list
```

Only one enabled `hashmicro-imagegen-native` entry should remain, using marketplace `hashmicro-xai-local` and the version shown by the [Latest Release badge](https://github.com/ArkhiMuttaqina/xai-Imagegen-codex-native/releases/latest).

On Windows, close other running Codex tasks before updating. An active HashMicro MCP process may temporarily lock files in the plugin cache. If the update reports a locked-file or access-denied error, fully exit Codex, rerun the same PowerShell command in an external terminal, then reopen Codex.

## Install

1. Extract the ZIP completely.
2. Open Terminal, PowerShell, or Command Prompt inside the extracted folder.
3. Run:

   Windows:

   ```powershell
   py install.py
   ```

   macOS/Linux:

   ```bash
   python3 install.py
   ```

4. Enter `XAI_URL` and `XAI_HASHMICRO_API_KEY` when prompted.
5. Restart Codex and start a new task.

The installer copies the bundle to `~/.codex/local-plugins/hashmicro-imagegen-share`, detects the exact Python executable, creates a portable MCP configuration, registers the local marketplace, and installs the plugin.

If another `hashmicro-imagegen-native` install exists, the installer asks before removing it. This is required to prevent duplicate tool, MCP server, and skill names. For an unattended migration, pass `--yes`.

If the Codex CLI is not on `PATH`, the installer prints the two commands that need to be run later.

## Existing credentials

If `~/.codex/.env` already contains the required values, the installer reuses them. To configure credentials manually, run:

```bash
python3 install.py --skip-credentials
```

Required values:

```dotenv
XAI_URL="https://your-gateway.example"
XAI_HASHMICRO_API_KEY="your-personal-key"
```

Optional values:

```dotenv
XAI_IMAGE_MODEL="codex/gpt-5.6-sol"
XAI_REASONING_EFFORT="low"
XAI_IMAGE_TIMEOUT_SEC="600"
XAI_IMAGE_JOB_TTL_SEC="3600"
```

## Migrating from an older or differently named local build

The installer detects installed variants such as `hashmicro-imagegen-native@personal` and `hashmicro-imagegen-native@hashmicro-xai-local`. Approve the migration when prompted, or run `python3 install.py --yes`.

To verify the result:

```bash
codex plugin list
```

Only one enabled `hashmicro-imagegen-native` install should remain, from marketplace `hashmicro-xai-local`, at the latest released version.

## Usage notes

- Generate images with `hashmicro_generate_image`.
- Start edits with `hashmicro_edit_image`, then poll `hashmicro_get_image_result` using the returned job id.
- For vertical wallpaper requests, pass `size: "9:16"`; the server uses a gateway-safe portrait size and preserves crop-safe composition.
- If a request times out, ask before retrying because the upstream request may still complete or be billed.

## Test prompt

> Generate a vertical 9:16 cyberpunk product advertisement through HashMicro XAI and save it under outputs/.

## Uninstall

```bash
codex plugin remove hashmicro-imagegen-native@hashmicro-xai-local
codex plugin marketplace remove hashmicro-xai-local
```

Then delete `~/.codex/local-plugins/hashmicro-imagegen-share` if desired. Removing credentials from `~/.codex/.env` is optional and should only be done if no other integration uses them.

## Development

Enable the repository-managed pre-push test gate once per clone:

```bash
python scripts/setup_hooks.py
```

Run the complete local gate at any time:

```bash
python scripts/verify.py
```

Every `git push` then runs the same unit, MCP, version, build, and installer checks before data is sent to GitHub. The hook is portable across Git Bash, macOS, and Linux, and automatically finds `python3`, `python`, or the Windows `py` launcher.

Git hooks are local Git configuration and cannot securely auto-enable themselves after clone. Agents and contributors must run `python scripts/setup_hooks.py` once. Even when a local hook was not enabled, GitHub Actions still tests every pushed branch without path filters, so changes made by Codex, Hermes, OpenCode, OpenZsh, an IDE, or a normal shell enter the same remote gate.

Live generation is not part of CI because it requires credentials and may incur usage or billing.

## Automated releases

`main` always contains the latest released source. Every change is tested before the version and changelog are updated. SemVer is selected in this order:

- Manual release choice: `patch`, `minor`, or `major`
- Branch prefixes: `fix/*` → patch, `feat/*` → minor, `breaking/*` → major
- Conventional commits: `fix:` → patch, `feat:` → minor, and `type!:` or `BREAKING CHANGE:` → major
- Any other successfully tested change → patch

CI runs on every push and pull request across the complete Windows/macOS/Linux matrix. A successful CI run for a non-release commit on `main` triggers the version workflow. It verifies the completed source again, updates the version and `CHANGELOG.md`, creates `vX.Y.Z`, and lets the tag workflow run the full release gate before publishing the ZIP and checksum as Latest.

Configure the repository ruleset to require the `Required CI` status before merging into `main`. See `VERSIONING.md` for the complete tool-independent flow and repository settings.

## License

Copyright © 2026 HashMicro. All rights reserved.

This project is proprietary and confidential. It is provided only for authorized HashMicro business use and is not open-source software. Copying, redistribution, sublicensing, publication, or external commercial use requires prior written permission from an authorized HashMicro representative.

See the complete [HashMicro Proprietary License](LICENSE). The owning legal entity and final terms should be confirmed by the company's legal or management team before external distribution.
