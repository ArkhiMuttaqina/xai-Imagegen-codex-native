# Contributing

## Development setup

Requirements:

- Python 3.10 or newer
- Codex CLI for installer integration testing
- A personal HashMicro XAI test credential for live tests

Run the offline test suite:

```bash
python -m unittest discover -s tests -v
```

Run a protocol smoke test:

```bash
python scripts/smoke_mcp.py
```

## Pull requests

- Keep the Python runtime dependency-free unless a dependency has a clear portability justification.
- Add or update tests for behavior changes.
- Never include credentials or generated images containing confidential data.
- Update `CHANGELOG.md` for user-visible changes.
- Keep the plugin manifest version and MCP server version aligned.
- Test Windows, macOS, and Linux behavior when changing paths, subprocesses, or installation logic.

Choose the branch prefix according to release impact:

- `fix/`, `bugfix/`, `hotfix/`, or `patch/` for a patch release.
- `feat/` or `feature/` for a minor release.
- `breaking/` or `major/` for a major release.
- `docs/`, `chore/`, `ci/`, or `test/` when no release should be created.

See `VERSIONING.md` for the complete automation flow.

## Live gateway tests

Live image generation may incur usage or billing. Run it only with an approved test credential and clearly record the model, size, quality, and output location. Never make live gateway calls in pull-request CI.
