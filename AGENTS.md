# AGENTS.md

Guidance for AI coding agents working in this repository.

## Scope

This repository contains a cross-platform Codex plugin and its marketplace installer for HashMicro XAI image generation and editing.

## Required checks for every agent and shell

These rules are client-independent. They apply to Codex CLI/Desktop, Hermes, OpenCode, OpenZsh, manual shells, IDE integrations, and any other tool that changes this repository.

After cloning once, enable the tracked pre-push hook:

```bash
python scripts/setup_hooks.py
```

Before committing and before pushing any change, run:

```bash
python scripts/verify.py
```

The pre-push hook runs the same command automatically. GitHub Actions repeats it on every branch push and pull request across Windows, macOS, and Linux. Never claim completion when a required check is failing.

Validate `plugins/hashmicro-imagegen-native` with the Codex plugin validator whenever the manifest or skill changes.

## Repository rules

- Keep runtime code compatible with Python 3.10+ and dependency-free unless explicitly approved.
- Preserve Windows, macOS, and Linux support.
- Never commit `.env`, API keys, gateway credentials, generated user images, or production URLs.
- Preserve the proprietary license and copyright notices; do not relicense the project without written company authorization.
- Do not silently switch image models. Prefer the requested model and surface configuration errors clearly.
- Keep manifest and MCP server versions identical.
- Add tests for behavioral changes.
- Update README and changelog for user-visible changes.
- Build release archives only through `scripts/build_release.py`.
- Do not edit release versions or prepend `CHANGELOG.md` until the completed source has passed the full verification suite.

## Versioning

- `fix/*`, `bugfix/*`, `hotfix/*`, `patch/*` → patch release.
- `feat/*`, `feature/*` → minor release.
- `breaking/*`, `major/*` → major release.
- Every successfully tested change reaching `main` receives a release. Branch names and Conventional Commit prefixes choose the SemVer increment; unclassified changes safely default to patch.

See `VERSIONING.md` for the automated tag and GitHub Release flow.

## Installation behavior

The one-line bootstrap downloads the latest GitHub Release, verifies SHA-256, extracts it safely, and runs `install.py --skip-credentials --yes`. The installer must create `~/.codex/.env` when missing and clearly direct the user to fill `XAI_URL` and `XAI_HASHMICRO_API_KEY`.
