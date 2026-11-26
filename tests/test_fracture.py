"""Fracture geometry conserves mass and varies without recoloring or noise."""

import unittest

from pixelai.fracture import PROFILES, build_fracture, polygon_area
from pixelai.runner import run_spec
from pixelai.structure import compare_graphs


def render(profile, size=48, seed=42, **fields):
    return run_spec({"width": size, "height": size, "style": "ext_outline", "ops": [
        {"op": "nature_rig", "kind": "rock", "w": size, "h": size, "seed": seed, "shadow": False,
         "fracture": {"profile": profile}, **fields}]})


class FractureTest(unittest.TestCase):
    def test_mass_conservation_clearance_and_determinism(self):
        for size in (32, 48, 64):
            for profile in PROFILES:
                for seed in (1, 42, 77):
                    with self.subTest(size=size, profile=profile, seed=seed):
                        canvas = render(profile, size, seed)
                        self.assertEqual(canvas.clipped_pixels, 0)
                        self.assertEqual(canvas.warnings, [])
                        graph = canvas.attachments[0]
                        self.assertEqual(graph, build_fracture(size, size, seed, {"profile": profile}))
                        for mass in graph["masses"]:
                            self.assertEqual(len(mass["facets"]), 4)
                            self.assertAlmostEqual(sum(polygon_area(facet["polygon"]) for facet in mass["facets"]), polygon_area(mass["outline"]))

    def test_profiles_change_silhouettes_and_recolors_preserve_structure(self):
        shapes, graphs = set(), []
        for profile in PROFILES:
            canvas = render(profile)
            shapes.add(tuple(pixel[3] for pixel in canvas.pixels))
            graphs.append(canvas.attachments[0])
            self.assertEqual(canvas.pixels, render(profile).pixels)
            self.assertEqual(canvas.attachments, render(profile, color="#b48670").attachments)
        self.assertEqual(len(shapes), 6)
        for i, first in enumerate(graphs):
            for second in graphs[i+1:]:
                self.assertFalse(compare_graphs(first, second)["normalized_geometry_equal"])

    def test_invalid_and_inactive_fields(self):
        for options in ({"profile": "unknown"}, {"cuts": True}, {"cuts": 6}, {"angle": float("nan")}, {"magic": 1}):
            with self.assertRaises(ValueError):
                build_fracture(48, 48, 42, options)
        with self.assertRaisesRegex(ValueError, "native"):
            build_fracture(16, 16, 42, {})
        with self.assertRaisesRegex(ValueError, "inactive/unsupported"):
            render("block", sway=True)
        with self.assertRaisesRegex(ValueError, "kind:rock"):
            run_spec({"width": 48, "height": 48, "ops": [{"op": "nature_rig", "kind": "tree", "fracture": {}}]})

    def test_cut_ranges_graph_transforms_and_managed_comparisons(self):
        import json
        from pathlib import Path
        import tempfile
        from pixelai.exporter import export_png
        from pixelai.filters import _transform_attachment_points
        from pixelai.production_contracts import validate_submission
        for profile in PROFILES:
            for cuts in (1, 5):
                for angle in (-75, 75):
                    graph = build_fracture(32, 32, 77, {"profile": profile, "cuts": cuts, "angle": angle})
                    self.assertTrue(all(len(mass["facets"]) == cuts+1 for mass in graph["masses"]))
        graph = build_fracture(48, 48, 42, {})
        moved = _transform_attachment_points(graph, factor=2, dx=13, dy=17)
        self.assertTrue(compare_graphs(graph, moved)["normalized_geometry_equal"])
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            data = {"proposals": [], "evidence": [], "selected_id": "slab"}
            for profile in PROFILES:
                spec = {"width": 48, "height": 48, "style": "ext_outline", "ops": [
                    {"op": "nature_rig", "kind": "rock", "w": 48, "h": 48, "shadow": False, "fracture": {"profile": profile}}]}
                (root / f"{profile}.json").write_text(json.dumps(spec))
                export_png(run_spec(spec), root / f"{profile}.png")
                data["proposals"].append({"id": profile, "structure": profile, "source_path": f"{profile}.json", "image_path": f"{profile}.png"})
                data["evidence"].extend({"path": f"{profile}.{extension}"} for extension in ("json", "png"))
            validate_submission("alternatives", data, {"contract": {"native_size": [48, 48]}}, root)
            self.assertEqual(len(data["fracture_comparisons"]), 15)
