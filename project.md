# Project Overview

## Name

HashMicro XAI Image Gen for Codex

## Purpose

Provide native MCP image generation and background image-editing tools for Codex Desktop and CLI through the HashMicro XAI gateway.

## Supported platforms

- Windows
- macOS
- Linux
- Python 3.10 and newer

GitHub Actions validates Windows, macOS, and Linux using Python 3.10 and 3.13.

## Main components

| Path | Responsibility |
|---|---|
| `plugins/hashmicro-imagegen-native/scripts/mcp_server.py` | Dependency-free stdio MCP server |
| `plugins/hashmicro-imagegen-native/.codex-plugin/plugin.json` | Codex plugin manifest and current version |
| `plugins/hashmicro-imagegen-native/skills/` | Agent routing and usage instructions |
| `install.py` | Cross-platform local marketplace and plugin installer |
| `scripts/bootstrap.py` | One-line latest-release downloader and verified installer |
| `scripts/build_release.py` | Deterministic release ZIP and checksum builder |
| `scripts/versioning.py` | SemVer bumping and tag/source validation |
| `.github/workflows/` | CI, automatic versioning, tagging, and GitHub Releases |

## Configuration

The plugin reads configuration from `~/.codex/.env` or `$CODEX_HOME/.env`:

```dotenv
XAI_URL="https://your-gateway.example"
XAI_HASHMICRO_API_KEY="your-personal-key"
XAI_IMAGE_MODEL="codex/gpt-5.6-sol"
XAI_REASONING_EFFORT="low"
XAI_IMAGE_TIMEOUT_SEC="600"
XAI_IMAGE_JOB_TTL_SEC="3600"
```

Only `XAI_URL` and `XAI_HASHMICRO_API_KEY` are mandatory. Credentials are user-specific and must never be stored in Git.

## Release model

`main` always represents the latest release source. Stable versions use tags such as `v0.1.4`, and every GitHub Release contains a ZIP plus its SHA-256 checksum.

## License

This repository is proprietary and confidential to HashMicro. It is not licensed for public redistribution or external commercial use. See `LICENSE` for the complete terms and obtain company legal or management approval before external distribution.
