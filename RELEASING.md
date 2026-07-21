# Releasing

Normal releases are automated. Use a branch prefix documented in `VERSIONING.md`, open a pull request, and merge it into `main`.

The workflow updates all version-bearing source files, creates the tag, builds the portable archive, uploads its checksum, and marks the GitHub Release as Latest.

Before merging a release-producing pull request:

1. Run `python -m unittest discover -s tests -v`.
2. Run `python scripts/smoke_mcp.py`.
3. Run `python scripts/versioning.py check`.
4. Validate the plugin with the Codex plugin validator.
5. Test live gateway behavior when the runtime itself changed.

For a controlled manual bump:

```bash
python scripts/versioning.py bump patch --summary "Describe the fix"
python -m unittest discover -s tests -v
python scripts/build_release.py
```

Prefer the GitHub Actions manual trigger because it also commits, tags, and publishes the release consistently.

Do not publish a release from a working tree containing `.env`, generated outputs, credentials, or unrelated binaries.
