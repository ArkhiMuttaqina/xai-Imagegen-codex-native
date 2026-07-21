from __future__ import annotations

import importlib.util
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "build_release.py"


def load_builder():
    spec = importlib.util.spec_from_file_location("build_release", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class ReleaseLayoutTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.builder = load_builder()

    def test_release_uses_codex_marketplace_manifest_location(self):
        self.assertIn(".agents/plugins/marketplace.json", self.builder.RELEASE_FILES)
        self.assertNotIn("marketplace.json", self.builder.RELEASE_FILES)
        self.assertTrue((ROOT / ".agents" / "plugins" / "marketplace.json").is_file())


if __name__ == "__main__":
    unittest.main()
