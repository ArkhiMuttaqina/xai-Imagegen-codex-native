# Releasing

1. Update the version in:
   - `plugins/hashmicro-imagegen-native/.codex-plugin/plugin.json`
   - `plugins/hashmicro-imagegen-native/scripts/mcp_server.py`
   - `CHANGELOG.md`
2. Run `python -m unittest discover -s tests -v`.
3. Run `python scripts/smoke_mcp.py`.
4. Validate the plugin with the Codex plugin validator.
5. Test the installer on Windows, macOS, and Linux using non-production credentials.
6. Build the ZIP with `python scripts/build_release.py`.
7. Publish the ZIP and its generated SHA-256 file together.
8. Install the ZIP on a clean machine and verify it with `codex plugin list`.

Do not publish a release from a working tree containing `.env`, generated outputs, credentials, or unrelated binaries.

