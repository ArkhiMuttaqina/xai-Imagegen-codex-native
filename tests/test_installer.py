from __future__ import annotations

import importlib.util
import os
from pathlib import Path
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
INSTALLER_PATH = ROOT / "install.py"


def load_installer():
    spec = importlib.util.spec_from_file_location("hashmicro_installer", INSTALLER_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class InstallerTests(unittest.TestCase):
    def setUp(self):
        self.installer = load_installer()

    def test_migration_sequence_removes_existing_before_add(self):
        recorded = []

        def fake_run_capture(parts, check=True):
            recorded.append(parts)
            if parts[1:] == ["plugin", "list"]:
                out = "hashmicro-imagegen-native@personal  installed, enabled  0.1.0  C:\\old\n"
            elif parts[1:] == ["plugin", "marketplace", "list"]:
                out = "MARKETPLACE ROOT\nhashmicro-xai-local C:\\old\npersonal C:\\Users\\x\n"
            else:
                out = ""
            return subprocess.CompletedProcess(parts, 0, stdout=out, stderr="")

        self.installer.run_capture = fake_run_capture
        self.installer.codex_executable = lambda: "codex"
        self.installer.run_codex(Path(r"C:\portable"), skip=False, assume_yes=True)
        self.assertEqual(
            recorded,
            [
                ["codex", "plugin", "list"],
                ["codex", "plugin", "marketplace", "list"],
                ["codex", "plugin", "remove", "hashmicro-imagegen-native@personal"],
                ["codex", "plugin", "marketplace", "remove", "hashmicro-xai-local"],
                ["codex", "plugin", "marketplace", "add", r"C:\portable"],
                ["codex", "plugin", "add", "hashmicro-imagegen-native@hashmicro-xai-local"],
            ],
        )

    def test_noninteractive_conflict_aborts_before_mutation(self):
        recorded = []

        def fake_run_capture(parts, check=True):
            recorded.append(parts)
            if parts[1:] == ["plugin", "list"]:
                out = "hashmicro-imagegen-native@personal  installed, enabled  0.1.0  C:\\old\n"
            elif parts[1:] == ["plugin", "marketplace", "list"]:
                out = "MARKETPLACE ROOT\npersonal C:\\Users\\x\n"
            else:
                out = ""
            return subprocess.CompletedProcess(parts, 0, stdout=out, stderr="")

        self.installer.run_capture = fake_run_capture
        self.installer.codex_executable = lambda: "codex"
        self.installer.sys.stdin.isatty = lambda: False
        with self.assertRaises(SystemExit):
            self.installer.run_codex(Path(r"C:\portable"), skip=False, assume_yes=False)
        self.assertEqual(recorded, [["codex", "plugin", "list"], ["codex", "plugin", "marketplace", "list"]])

    def test_skip_credentials_creates_fillable_env_template(self):
        with tempfile.TemporaryDirectory() as raw:
            previous = os.environ.get("CODEX_HOME")
            os.environ["CODEX_HOME"] = raw
            try:
                self.installer.update_env(skip=True)
                env_path = Path(raw) / ".env"
                values = self.installer.parse_env(env_path)
                self.assertEqual(values["XAI_URL"], "")
                self.assertEqual(values["XAI_HASHMICRO_API_KEY"], "")
                self.assertEqual(values["XAI_IMAGE_MODEL"], "codex/gpt-5.6-sol")
            finally:
                if previous is None:
                    os.environ.pop("CODEX_HOME", None)
                else:
                    os.environ["CODEX_HOME"] = previous


if __name__ == "__main__":
    unittest.main()
