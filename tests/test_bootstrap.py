from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest import mock
import zipfile


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "bootstrap.py"


def load_bootstrap():
    spec = importlib.util.spec_from_file_location("bootstrap", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class BootstrapTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bootstrap = load_bootstrap()

    def test_release_assets_selects_zip_and_checksum(self):
        release = {
            "assets": [
                {"name": "plugin.zip", "browser_download_url": "zip"},
                {"name": "plugin.sha256.txt", "browser_download_url": "checksum"},
            ]
        }
        archive, checksum = self.bootstrap.release_assets(release)
        self.assertEqual(archive["name"], "plugin.zip")
        self.assertEqual(checksum["name"], "plugin.sha256.txt")

    def test_verify_archive(self):
        archive = b"archive-content"
        digest = hashlib.sha256(archive).hexdigest()
        self.bootstrap.verify_archive(archive, f"{digest}  plugin.zip\n".encode(), "plugin.zip")

    def test_safe_extract_rejects_path_traversal(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            archive = root / "bad.zip"
            destination = root / "out"
            destination.mkdir()
            with zipfile.ZipFile(archive, "w") as bundle:
                bundle.writestr("../escape.txt", "bad")
            with self.assertRaises(SystemExit):
                self.bootstrap.safe_extract(archive, destination)

    def test_installer_failure_is_reported_without_fallback(self):
        error = self.bootstrap.subprocess.CalledProcessError(7, ["python", "install.py"])
        with mock.patch.object(self.bootstrap.subprocess, "run", side_effect=error):
            with self.assertRaisesRegex(SystemExit, "exit code 7.*did not apply a fallback patch"):
                self.bootstrap.run_installer(Path("install.py"))


if __name__ == "__main__":
    unittest.main()
