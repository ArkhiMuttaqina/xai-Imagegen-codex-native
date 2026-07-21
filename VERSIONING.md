# Versioning, Testing, and Release Workflow

`main` always represents the latest released source. The workflow is intentionally client-independent: Codex, Hermes, OpenCode, OpenZsh, IDEs, and ordinary Git shells all produce the same result once they push Git commits.

## Local gate before push

Enable the repository-managed hook once in every clone:

```bash
python scripts/setup_hooks.py
```

The hook runs this shared verifier before every push:

```bash
python scripts/verify.py
```

It compiles the Python entrypoints, runs all unit tests, exercises the MCP server, checks version consistency, builds the release bundle, and smoke-tests the offline installer. A failure blocks the push.

Git does not allow a repository to silently activate hooks after clone. This one-time setup is therefore required for a true local pre-push gate. `SKIP_PRE_PUSH_VERIFY=1` exists only for emergencies; the remote CI gate cannot be bypassed by it.

## Remote gate for every change

`.github/workflows/ci.yml` runs without path filters on:

- every branch push;
- every pull request;
- manual workflow dispatch.

The matrix covers Windows, macOS, and Linux on Python 3.10, 3.13, and 3.14. The final `Required CI` job succeeds only when every matrix job succeeds.

Configure a GitHub ruleset for `main` that:

1. Requires a pull request before merging.
2. Requires the `Required CI` status check.
3. Requires branches to be up to date before merging.
4. Blocks force pushes and branch deletion.
5. Allows `github-actions[bot]` to create the audited release commit, or grants GitHub Actions the required bypass.

## SemVer selection

The release workflow selects the bump in this order:

| Signal | Version change |
|---|---|
| Manual workflow input | Selected patch, minor, or major |
| `breaking/*`, `major/*` branch | Major |
| `feat/*`, `feature/*` branch | Minor |
| `fix/*`, `bugfix/*`, `hotfix/*`, `patch/*` branch | Patch |
| Conventional commit with `!` or `BREAKING CHANGE:` | Major |
| Conventional commit beginning `feat:` | Minor |
| Conventional commit beginning `fix:`, `perf:`, or `refactor:` | Patch |
| Any other tested change | Patch |

The patch fallback means edits from an agent that does not follow branch or commit naming conventions are still versioned and released.

## Automatic release sequence

1. A contributor or agent pushes a change.
2. CI runs the full nine-job platform/runtime matrix.
3. Only a successful CI run on `main` can trigger `.github/workflows/auto-version.yml`.
4. The version workflow rejects stale CI runs and skips existing `chore(release): vX.Y.Z` commits.
5. It runs `python scripts/verify.py` before changing the version or changelog.
6. After tests pass, it updates the manifest, MCP server version, README version, and `CHANGELOG.md`.
7. It validates the final release metadata and installer again.
8. It commits `chore(release): vX.Y.Z` and creates the annotated `vX.Y.Z` tag.
9. The tag starts `.github/workflows/tag-release.yml`, which runs the complete verification suite again.
10. Only then is the ZIP plus SHA-256 checksum published as the Latest GitHub Release.

The release commit triggers CI, but the release guard recognizes it and prevents an infinite version loop. If a newer `main` commit appears while an older CI result is waiting, the stale run exits and the newer commit's own CI result takes over.

## Manual release

Open GitHub Actions, choose **Auto Version**, select **Run workflow**, choose `patch`, `minor`, or `major`, and provide the changelog summary. The same pre-version and tag release gates still run.

## Existing/manual tags

Pushing a valid tag triggers the release gate. The source version must match the tag:

```bash
python scripts/verify.py
python scripts/versioning.py check --tag v0.1.8
git tag -a v0.1.8 -m "v0.1.8"
git push origin v0.1.8
```

## Required repository permission

Under **Settings → Actions → General → Workflow permissions**, enable **Read and write permissions**. The auto-version workflow needs this to push the release commit and tag; the release workflow needs it to publish assets.
