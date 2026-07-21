from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
SERVER_PATH = ROOT / "plugins" / "hashmicro-imagegen-native" / "scripts" / "mcp_server.py"
MANIFEST_PATH = ROOT / "plugins" / "hashmicro-imagegen-native" / ".codex-plugin" / "plugin.json"


def load_server():
    spec = importlib.util.spec_from_file_location("hashmicro_mcp_server", SERVER_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class McpServerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = load_server()

    def test_manifest_and_server_versions_match(self):
        manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        self.assertEqual(manifest["version"], self.server.SERVER_VERSION)

    def test_ratio_mapping_preserves_orientation(self):
        cases = {
            "9:16": "1024x1536",
            "2:3": "1024x1536",
            "3:4": "1024x1536",
            "16:9": "1536x1024",
            "3:2": "1536x1024",
            "4:3": "1536x1024",
            "1:1": "1024x1024",
            "1024x1792": "1024x1536",
            "1792x1024": "1536x1024",
        }
        for requested, expected in cases.items():
            with self.subTest(requested=requested):
                size, prompt, note = self.server._size_and_prompt("prompt", requested, edit=False)
                self.assertEqual(size, expected)
                self.assertIn(expected, note)
                self.assertIn("crop-safe", prompt)

    def test_auto_generation_stays_auto(self):
        size, prompt, note = self.server._size_and_prompt("prompt", "auto", edit=False)
        self.assertEqual(size, "auto")
        self.assertEqual(prompt, "prompt")
        self.assertIsNone(note)

    def test_edit_auto_defaults_to_square(self):
        size, prompt, note = self.server._size_and_prompt("prompt", "auto", edit=True)
        self.assertEqual(size, "1024x1024")
        self.assertIn("crop-safe", prompt)
        self.assertEqual(note, "auto -> 1024x1024")

    def test_tools_schema_exposes_three_tools(self):
        names = {tool["name"] for tool in self.server.TOOLS}
        self.assertEqual(names, {"hashmicro_generate_image", "hashmicro_edit_image", "hashmicro_get_image_result"})
        generate = next(tool for tool in self.server.TOOLS if tool["name"] == "hashmicro_generate_image")
        edit = next(tool for tool in self.server.TOOLS if tool["name"] == "hashmicro_edit_image")
        self.assertEqual(generate["inputSchema"]["required"], ["prompt"])
        self.assertEqual(edit["inputSchema"]["required"], ["prompt", "images"])


if __name__ == "__main__":
    unittest.main()
