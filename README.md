# HashMicro XAI Image Gen for Codex v0.1.2

Portable ZIP bundle for Windows, macOS, and Linux. The MCP server uses only the Python standard library; no `pip install` is required.

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
├── install.py
├── marketplace.json
├── plugins/hashmicro-imagegen-native/
│   ├── .codex-plugin/plugin.json
│   ├── .mcp.json
│   ├── scripts/mcp_server.py
│   └── skills/hashmicro-native-imagegen/SKILL.md
├── scripts/
│   ├── build_release.py
│   └── smoke_mcp.py
└── tests/
```

The runtime intentionally uses only Python's standard library.

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

## Upgrade from an older local build

The installer detects installed variants such as `hashmicro-imagegen-native@personal` and `hashmicro-imagegen-native@hashmicro-xai-local`. Approve the migration when prompted, or run `python3 install.py --yes`.

To verify the result:

```bash
codex plugin list
```

Only one enabled `hashmicro-imagegen-native` install should remain, from marketplace `hashmicro-xai-local`, at version `0.1.2`.

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

```bash
python -m unittest discover -s tests -v
python scripts/smoke_mcp.py
python scripts/versioning.py check
python scripts/build_release.py
```

Live generation is not part of CI because it requires credentials and may incur usage or billing.

## Automated releases

`main` always contains the latest released source. Pull-request branch prefixes determine the next SemVer release:

- `fix/*` → patch
- `feat/*` → minor
- `breaking/*` → major

After an eligible pull request is merged, GitHub Actions updates the source version, creates `vX.Y.Z`, builds the ZIP and checksum, and publishes it as the Latest GitHub Release. See `VERSIONING.md` for branch aliases, manual releases, and required repository settings.

## License

No open-source license is included yet. Treat this repository as private/internal until the team selects and adds the correct license.
