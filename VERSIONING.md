# Versioning and Branch Workflow

`main` is always the latest released source. Feature and fix work should reach `main` through pull requests.

## Branch prefixes

The branch merged into `main` selects the SemVer increment:

| Branch prefix | Version change | Example |
|---|---|---|
| `fix/`, `bugfix/`, `hotfix/`, `patch/` | Patch | `0.1.2` → `0.1.3` |
| `feat/`, `feature/` | Minor | `0.1.2` → `0.2.0` |
| `breaking/`, `major/` | Major | `0.1.2` → `1.0.0` |
| `docs/`, `chore/`, `ci/`, `test/`, other | No automatic release | Version unchanged |

Examples:

```bash
git switch -c fix/edit-auto-size
git switch -c feat/image-variations
git switch -c breaking/new-gateway-contract
```

## Automatic release sequence

When an eligible pull request is merged into `main`, `.github/workflows/auto-version.yml`:

1. Determines patch, minor, or major from the merged branch name.
2. Updates the plugin manifest, MCP server version, README, and changelog.
3. Runs unit tests, the MCP smoke test, and version consistency validation.
4. Commits `chore(release): vX.Y.Z` directly to `main`.
5. Creates the annotated Git tag `vX.Y.Z`.
6. Builds the portable ZIP and SHA-256 file.
7. Publishes a GitHub Release and marks it as Latest.

The release commit is made by `github-actions[bot]` so automated changes are auditable. Human commits retain their configured authors.

## Manual release

Open GitHub Actions, select **Auto Version and Release**, choose **Run workflow**, then select `patch`, `minor`, or `major` and enter the changelog summary.

## Existing/manual tags

Pushing an existing valid tag such as `v0.1.3` triggers `.github/workflows/tag-release.yml`. The workflow refuses to publish when the tag does not match the source version.

```bash
python scripts/versioning.py check --tag v0.1.3
git tag -a v0.1.3 -m "v0.1.3"
git push origin v0.1.3
```

## Repository settings

GitHub Actions requires **Read and write permissions** for workflows:

1. Open repository **Settings → Actions → General**.
2. Under **Workflow permissions**, select **Read and write permissions**.
3. Save the setting.

If `main` has branch protection that blocks GitHub Actions from pushing the release commit, either allow GitHub Actions to bypass that rule or switch to a release-PR workflow.

