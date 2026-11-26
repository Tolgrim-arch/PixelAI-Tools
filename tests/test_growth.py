"""Growth architectures must change structure independently of foliage color."""

import unittest
import json
from pathlib import Path
import tempfile

from pixelai.growth import PROFILES, build_growth_graph
from pixelai.runner import run_spec
from pixelai.inspect_tool import analyze_canvas
from pixelai.exporter import export_png
from pixelai.production_contracts import validate_submission


def render(profile, **overrides):
    operation = {"op": "nature_rig", "kind": "tree", "variant": "oak", "w": 64, "h": 78,
                 "seed": 41, "shadow": False, "growth": {"profile": profile}, **overrides}
    return run_spec({"width": 64, "height": 78, "style": "ext_outline", "ops": [operation]})


class GrowthTest(unittest.TestCase):
    def test_managed_proposals_include_rendered_growth_comparisons(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            proposals, evidence = [], []
            for profile in PROFILES:
                source = {"width": 64, "height": 78, "style": "lineless", "ops": [
                    {"op": "nature_rig", "kind": "tree", "variant": "oak", "w": 64, "h": 78,
                     "seed": 41, "shadow": False, "growth": {"profile": profile}}]}
                source_name, image_name = f"{profile}.json", f"{profile}.png"
                (root / source_name).write_text(json.dumps(source))
                export_png(run_spec(source), root / image_name)
                proposals.append({"id": profile, "structure": f"Tree architecture: {profile}", "source_path": source_name, "image_path": image_name})
                evidence.extend([{"path": source_name}, {"path": image_name}])
            data = {"proposals": proposals, "selected_id": "forked", "evidence": evidence}
            validate_submission("alternatives", data, {"contract": {"native_size": [64, 78]}}, root)
            self.assertEqual(len(data["growth_comparisons"]), 15)
            self.assertTrue(any(not comparison["topology_equal"] for comparison in data["growth_comparisons"]))
            self.assertTrue(all(not comparison["normalized_geometry_equal"] for comparison in data["growth_comparisons"]))

    def test_profiles_change_trunk_geometry_at_a_stable_ground_anchor(self):
        shapes, parents, roots = [], [], []
        for profile in PROFILES:
            graph = build_growth_graph(64, 78, 41, {"profile": profile})
            self.assertEqual(graph["ground_anchor"], [32, 71])
            self.assertEqual(graph, build_growth_graph(64, 78, 41, {"profile": profile}))
            parents.append(tuple((node["id"], node["parent"]) for node in graph["nodes"]))
            roots.append(tuple(tuple(node["point"]) for node in graph["nodes"] if node["role"] == "root"))
            canvas = render(profile, trunk_only=True)
            shapes.append(tuple(pixel[3] for pixel in canvas.pixels))
            self.assertEqual(canvas.clipped_pixels, 0)
            self.assertTrue(any(item.get("type") == "growth_graph" for item in canvas.attachments))
            complete = render(profile)
            stats = analyze_canvas(complete)
            self.assertEqual(stats["islands"], 1)
            self.assertGreaterEqual(min(stats["margins"].values()), 1)
        self.assertEqual(len(set(shapes)), len(PROFILES))
        self.assertGreaterEqual(len(set(parents)), 4)
        self.assertEqual(len(set(roots)), len(PROFILES))

    def test_color_and_seed_have_separate_structural_roles(self):
        first = render("gnarled", color="#488c52")
        second = render("gnarled", color="#9254a4")
        self.assertEqual(first.attachments, second.attachments)
        self.assertNotEqual(first.pixels, second.pixels)
        self.assertNotEqual(build_growth_graph(64, 78, 41, {"profile": "forked"}),
                            build_growth_graph(64, 78, 92, {"profile": "forked"}))

    def test_graph_coordinates_and_radii_follow_postprocessing(self):
        canvas = run_spec({"width": 64, "height": 78, "style": "lineless", "ops": [
            {"op": "nature_rig", "kind": "tree", "variant": "oak", "w": 64, "h": 78,
             "growth": {"profile": "forked"}, "trunk_only": True, "shadow": False}],
             "post": [{"op": "pad", "size": 2}, {"op": "scale", "factor": 2}]})
        graph = canvas.attachments[0]
        self.assertEqual(graph["ground_anchor"], [68, 146])
        original = build_growth_graph(64, 78, 11, {"profile": "forked"})
        self.assertEqual(graph["nodes"][0]["radius"], original["nodes"][0]["radius"] * 2)

    def test_invalid_or_inapplicable_growth_controls_are_rejected(self):
        for options in ({"profile": "unknown"}, {"lean": 3}, {"thikness": 2}, {"spread": float("nan")}):
            with self.assertRaises(ValueError):
                build_growth_graph(64, 78, 41, options)
        with self.assertRaisesRegex(ValueError, "oak, fruit and sakura"):
            render("forked", variant="pine")

    def test_explicit_zero_lean_and_native_size_matrix(self):
        graph = build_growth_graph(64, 78, 41, {"profile": "upright", "lean": 0})
        self.assertTrue(all(node["point"][0] == 32 for node in graph["nodes"] if node["role"] == "stem"))
        for width, height in ((32, 40), (64, 78), (128, 144)):
            for profile in PROFILES:
                for seed in (7, 41, 92):
                    with self.subTest(size=(width, height), profile=profile, seed=seed):
                        canvas = run_spec({"width": width, "height": height, "style": "ext_outline", "ops": [
                            {"op": "nature_rig", "kind": "tree", "variant": "oak", "w": width, "h": height,
                             "seed": seed, "growth": {"profile": profile}}]})
                        stats = analyze_canvas(canvas)
                        self.assertEqual(canvas.clipped_pixels, 0)
                        self.assertGreaterEqual(min(stats["margins"].values()), 1)
