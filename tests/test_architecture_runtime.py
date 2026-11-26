"""Modeled footprints remain source-bound and preserve open courtyard space."""

from contextlib import redirect_stdout
import io
import json
from pathlib import Path
import tempfile
import unittest

from pixelai.architecture import build_architecture, projection
from pixelai.cli import main
from pixelai.manifest import load_manifest
from pixelai.provenance import verify_construction
from pixelai.runner import run_spec
from pixelai.runtime import render_scene


class ArchitectureRuntimeTest(unittest.TestCase):
    def test_derived_footprints_transform_and_override_precedence(self):
        spec = {"width": 96, "height": 96, "style": "lineless", "ops": [
            {"op": "building", "w": 96, "h": 96, "architecture": {"profile": "l_wing"}}],
            "runtime": {"derive": "structure", "regions_from_structure": "footprints"},
            "post": [{"op": "pad", "size": 2}, {"op": "scale", "factor": 2}]}
        canvas = run_spec(spec)
        graph, runtime = canvas.attachments
        self.assertEqual(runtime["pivot"], graph["ground_anchor"])
        self.assertEqual(runtime["sockets"]["entrance"], graph["ground_anchor"])
        self.assertEqual([region["polygon"] for region in runtime["regions"]], [item["polygon"] for item in graph["footprints"]])
        spec["runtime"]["regions"] = []
        self.assertEqual(run_spec(spec).attachments[-1]["regions"], [])
        spec["runtime"]["frame_overrides"] = {"0": {"sockets": {"entrance": [30, 40]}}}
        self.assertEqual(run_spec(spec).attachments[-1]["sockets"]["entrance"], [64, 84])

    def test_exported_courtyard_gap_and_collision_provenance(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            spec = json.loads((Path(__file__).resolve().parents[1] / "specs/architecture_runtime.json").read_text())
            (root / "source.json").write_text(json.dumps(spec))
            with redirect_stdout(io.StringIO()):
                self.assertEqual(main(["render", str(root / "source.json"), "-o", str(root / "building.png"), "--manifest", str(root / "building.json")]), 0)
            manifest, _ = load_manifest(root / "building.json")
            self.assertEqual(len(manifest["frames"][0]["regions"]), 4)
            proof = {"source_path": "source.json", "image_path": "building.png", "manifest_path": "building.json",
                     "evidence": [{"path": name} for name in ("source.json", "building.png", "building.json")]}
            verify_construction(root, proof)
            probe = {"asset_id": "probe", "width": 4, "height": 4, "style": "lineless",
                     "ops": [{"op": "rect", "x": 1, "y": 1, "w": 2, "h": 2, "color": "#449966"}],
                     "runtime": {"pivot": [2, 2], "ground_anchor": [2, 2], "sort_origin": [2, 2],
                                 "regions": [{"id": "body", "role": "collision", "polygon": [[1.75, 1.75], [2.25, 1.75], [2.25, 2.25], [1.75, 2.25]]}]}}
            (root / "probe-source.json").write_text(json.dumps(probe))
            with redirect_stdout(io.StringIO()):
                self.assertEqual(main(["render", str(root / "probe-source.json"), "-o", str(root / "probe.png"), "--manifest", str(root / "probe.json")]), 0)
            project, _ = projection(build_architecture(96, 96, {"profile": "courtyard"}), 96, 96)
            gap = project((6, 4, 0))
            scene = {"schema_version": 1, "width": 96, "height": 96, "collision_mode": "block", "times_ms": [0],
                     "actors": [{"id": "building", "manifest": "building.json", "clip": "default", "position": manifest["frames"][0]["pivot"]},
                                {"id": "probe", "manifest": "probe.json", "clip": "default", "position": gap}],
                     "expectations": [{"actor": "probe", "time_ms": 0, "position": gap}]}
            (root / "scene.json").write_text(json.dumps(scene))
            report = render_scene(root / "scene.json", root / "gap")
            self.assertEqual(report["scenario"]["status"], "passed")
            self.assertEqual(report["trace"][0]["region_overlaps"], [])
            scene["actors"][1]["position"] = project((6, 1, 0))
            scene.pop("expectations")
            (root / "scene.json").write_text(json.dumps(scene))
            with self.assertRaisesRegex(ValueError, "overlaps at 0ms"):
                render_scene(root / "scene.json", root / "blocked")
            self.assertFalse((root / "blocked").exists())
            manifest["frames"][0]["regions"] = []
            (root / "building.json").write_text(json.dumps(manifest))
            with self.assertRaisesRegex(ValueError, "runtime regions"):
                verify_construction(root, proof)

    def test_invalid_or_inapplicable_derivation_is_explicit(self):
        for runtime in ({"regions_from_structure": "footprints"}, {"derive": "structure", "regions_from_structure": "silhouette"}):
            with self.assertRaisesRegex(ValueError, "requires footprints"):
                run_spec({"width": 96, "height": 96, "ops": [], "runtime": runtime})
        with self.assertRaisesRegex(ValueError, "architecture graph"):
            run_spec({"width": 64, "height": 64, "ops": [{"op": "char_rig", "size": 64, "morphology": {}}],
                      "runtime": {"derive": "structure", "regions_from_structure": "footprints"}})
