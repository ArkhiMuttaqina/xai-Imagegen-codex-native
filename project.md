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

GitHub Actions validates Windows, macOS, and Linux using Python 3.10, 3.13, and 3.14.

## Main components

| Path | Responsibility |
|---|---|
| `plugins/hashmicro-imagegen-native/scripts/mcp_server.py` | Dependency-free stdio MCP server |
| `plugins/hashmicro-imagegen-native/.codex-plugin/plugin.json` | Codex plugin manifest and current version |
| `plugins/hashmicro-imagegen-native/skills/` | Agent routing and usage instructions |
| `.agents/plugins/marketplace.json` | Codex marketplace manifest discovered by the CLI |
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

`main` always represents the latest release source. Every local clone can enable the tracked pre-push verifier with `python scripts/setup_hooks.py`, and remote CI tests every push across the complete supported platform/runtime matrix. A successful non-release change on `main` is versioned only after tests pass; its tag then passes the full gate again before GitHub publishes the ZIP and SHA-256 checksum.

The process is independent of the editing client. Changes from Codex, Hermes, OpenCode, OpenZsh, IDEs, and normal shells are covered as long as they enter the repository through Git.

## License

This repository is proprietary and confidential to HashMicro. It is not licensed for public redistribution or external commercial use. See `LICENSE` for the complete terms and obtain company legal or management approval before external distribution.
