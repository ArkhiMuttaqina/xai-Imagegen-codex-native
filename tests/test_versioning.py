from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "versioning.py"


def load_versioning():
    spec = importlib.util.spec_from_file_location("versioning", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class VersioningTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.versioning = load_versioning()

    def test_semver_bumps(self):
        self.assertEqual(self.versioning.bump_semver("0.1.2", "patch"), "0.1.3")
        self.assertEqual(self.versioning.bump_semver("0.1.2", "minor"), "0.2.0")
        self.assertEqual(self.versioning.bump_semver("0.1.2", "major"), "1.0.0")

    def test_branch_classification(self):
        cases = {
            "fix/edit-timeout": "patch",
            "bugfix/path": "patch",
            "hotfix/security": "patch",
            "feat/variations": "minor",
            "feature/masks": "minor",
            "breaking/gateway-v2": "major",
            "major/new-contract": "major",
            "docs/readme": "none",
            "chore/dependencies": "none",
        }
        for branch, expected in cases.items():
            with self.subTest(branch=branch):
                self.assertEqual(self.versioning.classify_branch(branch), expected)

    def test_manual_bump_overrides_branch(self):
        self.assertEqual(self.versioning.classify_branch("docs/readme", "minor"), "minor")

    def test_commit_message_classification(self):
        cases = {
            "fix: repair installer": "patch",
            "perf(mcp): reduce polling overhead": "patch",
            "feat: add image variations": "minor",
            "feat(api)!: replace gateway contract": "major",
            "docs: explain updates\n\nBREAKING CHANGE: configuration moved": "major",
            "Update README from another agent": "none",
        }
        for message, expected in cases.items():
            with self.subTest(message=message):
                self.assertEqual(self.versioning.classify_message(message), expected)

    def test_release_selection_covers_unclassified_agent_changes(self):
        self.assertEqual(
            self.versioning.select_release_bump(message="Edited by Hermes without a conventional prefix"),
            "patch",
        )
        self.assertEqual(self.versioning.select_release_bump(branch="feat/new-tool"), "minor")
        self.assertEqual(
            self.versioning.select_release_bump(branch="fix/small", message="feat: larger change", manual="major"),
            "major",
        )

    def test_source_versions_are_consistent(self):
        self.assertRegex(self.versioning.check(), r"^[0-9]+\.[0-9]+\.[0-9]+$")

    def test_update_version_changes_all_release_files(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            manifest = root / "plugin.json"
            server = root / "mcp_server.py"
            readme = root / "README.md"
            changelog = root / "CHANGELOG.md"
            manifest.write_text('{"version": "0.1.2"}\n', encoding="utf-8")
            server.write_text('SERVER_VERSION = "0.1.2"\n', encoding="utf-8")
            readme.write_text('# Plugin v0.1.2\nVersion `0.1.2`\n', encoding="utf-8")
            changelog.write_text('# Changelog\n\n## 0.1.2\n', encoding="utf-8")

            originals = (
                self.versioning.MANIFEST,
                self.versioning.SERVER,
                self.versioning.README,
                self.versioning.CHANGELOG,
            )
            try:
                self.versioning.MANIFEST = manifest
                self.versioning.SERVER = server
                self.versioning.README = readme
                self.versioning.CHANGELOG = changelog
                self.assertEqual(self.versioning.update_version("patch", "Fix edit polling"), "0.1.3")
                self.assertEqual(json.loads(manifest.read_text(encoding="utf-8"))["version"], "0.1.3")
                self.assertIn('SERVER_VERSION = "0.1.3"', server.read_text(encoding="utf-8"))
                self.assertIn("v0.1.3", readme.read_text(encoding="utf-8"))
                self.assertIn("Fix edit polling", changelog.read_text(encoding="utf-8"))
            finally:
                (
                    self.versioning.MANIFEST,
                    self.versioning.SERVER,
                    self.versioning.README,
                    self.versioning.CHANGELOG,
                ) = originals


if __name__ == "__main__":
    unittest.main()
