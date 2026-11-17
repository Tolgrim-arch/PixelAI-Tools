import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


class InstalledWorkflowTest(unittest.TestCase):
    def cli(self, *args, cwd, spec=None, check=True):
        env = os.environ.copy()
        checkout = Path(__file__).resolve().parents[1]
        if (checkout / "pixelai" / "__main__.py").is_file():
            env["PYTHONPATH"] = str(checkout)
        return subprocess.run(
            [sys.executable, "-m", "pixelai", *map(str, args)],
            cwd=cwd,
            env=env,
            input=json.dumps(spec) if spec is not None else None,
            capture_output=True,
            text=True,
            check=check,
        )

    def test_outputs_and_relative_asset_paths(self):
        with tempfile.TemporaryDirectory(prefix="pixelai smoke ") as directory:
            root = Path(directory)
            parents = root / "parent assets"
            parents.mkdir()
            sprite = parents / "base sprite.png"
            spec = {"width": 16, "height": 16, "style": "lineless",
                    "ops": [{"op": "rect", "x": 4, "y": 4, "w": 5, "h": 8, "color": "#ff9090"}]}
            rendered = self.cli("render", "-", "-o", sprite, "--json", cwd=root, spec=spec)
            self.assertEqual(Path(json.loads(rendered.stdout)["artifacts"]["image"]), sprite)
            parent = {**spec, "ops": [{"op": "load_png", "path": sprite.name}]}
            (parents / "parent.json").write_text(json.dumps(parent), encoding="utf-8")
            child = root / "child spec.json"
            child.write_text(json.dumps({
                "extends": "parent assets/parent.json",
                "frames": [{"ops": []}, {"ops": [{"op": "pixel", "x": 3, "y": 4, "color": "#ffffff"}]}]
            }), encoding="utf-8")

            result = self.cli("validate", child, cwd=parents)
            self.assertEqual(json.loads(result.stdout)["frame_count"], 2)
            gif = root / "animated sprite.gif"
            self.cli("render", child, "-o", gif, "--json", cwd=parents)
            self.assertEqual(json.loads(self.cli("inspect", gif, cwd=root).stdout)["frame_count"], 2)

            (root / "project.godot").touch()
            result = self.cli("render", child, "-o", "art/sheet.png", "--sheet",
                              "--meta", "frames.json", "--godot", "frames.tres", "--json", cwd=root)
            paths = json.loads(result.stdout)["artifacts"]
            self.assertEqual(set(paths), {"image", "metadata", "godot"})
            for path in paths.values():
                self.assertTrue(Path(path).is_file())
            metadata = json.loads(Path(paths["metadata"]).read_text(encoding="utf-8"))
            self.assertEqual([(f["x"], f["y"]) for f in metadata["frames"]], [(0, 0), (16, 0)])
            self.assertIn('path="res://art/sheet.png"', Path(paths["godot"]).read_text(encoding="utf-8"))

    def test_bad_operation_reports_field_and_does_not_export(self):
        with tempfile.TemporaryDirectory(prefix="pixelai invalid ") as directory:
            spec = {"width": 4, "height": 4, "ops": [{"op": "pixel", "x": 1}]}
            for args in (("validate", "-"), ("render", "-", "-o", "invalid.png", "--json")):
                result = self.cli(*args, cwd=directory, spec=spec, check=False)
                self.assertEqual(result.returncode, 1)
                self.assertIn("ops[0] (pixel)", result.stderr)
                self.assertIn("'y'", result.stderr)
                self.assertEqual(result.stdout, "")
                self.assertFalse((Path(directory) / "invalid.png").exists())
