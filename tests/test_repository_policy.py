from __future__ import annotations

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class RepositoryPolicyTests(unittest.TestCase):
    def test_ci_covers_every_push_without_path_filters(self):
        workflow = (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
        self.assertIn("  push:\n", workflow)
        self.assertNotIn("paths-ignore:", workflow)
        self.assertNotIn("branches-ignore:", workflow)
        self.assertIn("python scripts/verify.py", workflow)
        self.assertIn("Required CI", workflow)

    def test_release_waits_for_successful_main_ci(self):
        workflow = (ROOT / ".github" / "workflows" / "auto-version.yml").read_text(encoding="utf-8")
        self.assertIn("workflow_run:", workflow)
        self.assertIn("github.event.workflow_run.conclusion == 'success'", workflow)
        self.assertIn("github.event.workflow_run.head_branch == 'main'", workflow)
        self.assertLess(
            workflow.index("Test completed source before changing version or changelog"),
            workflow.index("Update version and changelog after tests pass"),
        )

    def test_tag_release_runs_full_verification(self):
        workflow = (ROOT / ".github" / "workflows" / "tag-release.yml").read_text(encoding="utf-8")
        self.assertIn('python scripts/versioning.py check --tag "$GITHUB_REF_NAME"', workflow)
        self.assertIn("python scripts/verify.py", workflow)
        self.assertIn("dist/*.sha256.txt", workflow)

    def test_pre_push_hook_uses_shared_verifier(self):
        hook = (ROOT / ".githooks" / "pre-push").read_text(encoding="utf-8")
        self.assertTrue(hook.startswith("#!/usr/bin/env sh\n"))
        self.assertIn("scripts/verify.py --pre-push", hook)


if __name__ == "__main__":
    unittest.main()
