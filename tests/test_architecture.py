"""Building volume layouts drive distinct silhouettes and actual footprints."""

import unittest

from pixelai.architecture import LAYOUTS, build_architecture
from pixelai.runner import run_spec
from pixelai.structure import compare_graphs


def render(profile, rotation=0, size=96, **fields):
    return run_spec({"width": size, "height": size, "style": "ext_outline", "ops": [
        {"op": "building", "w": size, "h": size, "architecture": {"profile": profile, "rotation": rotation}, **fields}]})


class ArchitectureTest(unittest.TestCase):
    def test_rotation_size_clearance_and_connected_footprints(self):
        for size in (64, 96, 128):
            for profile in LAYOUTS:
                for rotation in (0, 90, 180, 270):
                    with self.subTest(size=size, profile=profile, rotation=rotation):
                        canvas = render(profile, rotation, size)
                        self.assertEqual(canvas.clipped_pixels, 0)
                        self.assertEqual(canvas.warnings, [])
                        graph = canvas.attachments[0]
                        self.assertEqual(graph["type"], "architecture_graph")
                        self.assertEqual(len(graph["footprints"]), len(LAYOUTS[profile]))
                        reachable = {"mass_0"}
                        for _ in graph["volumes"]:
                            for first, second in graph["connections"]:
                                if first in reachable or second in reachable:
                                    reachable.update((first, second))
                        self.assertEqual(reachable, {volume["id"] for volume in graph["volumes"]})

    def test_geometry_varies_without_facade_decoration(self):
        shapes, graphs = set(), []
        for profile in LAYOUTS:
            canvas = render(profile, massing_only=True)
            shapes.add(tuple(pixel[3] for pixel in canvas.pixels))
            graphs.append(canvas.attachments[0])
            self.assertEqual(canvas.pixels, render(profile, massing_only=True).pixels)
        self.assertEqual(len(shapes), 6)
        for index, first in enumerate(graphs):
            for second in graphs[index+1:]:
                self.assertFalse(compare_graphs(first, second)["normalized_geometry_equal"])

    def test_recolor_and_decoration_do_not_change_graph(self):
        first = render("l_wing")
        second = render("l_wing", wall_color="#8ba8a0", roof_color="#596780", massing_only=True)
        self.assertNotEqual(first.pixels, second.pixels)
        self.assertEqual(first.attachments, second.attachments)

    def test_transforms_and_managed_proposal_comparisons(self):
        import json
        from pathlib import Path
        import tempfile
        from pixelai.exporter import export_png
        from pixelai.production_contracts import validate_submission
        from pixelai.filters import _transform_attachment_points
        first = render("courtyard").attachments[0]
        transformed = _transform_attachment_points(first, factor=2, dx=7, dy=9)
        self.assertTrue(compare_graphs(first, transformed)["normalized_geometry_equal"])
        self.assertEqual(transformed["volumes"], first["volumes"])
        self.assertEqual(transformed["footprints"][0]["polygon"][0], [value*2+offset for value, offset in zip(first["footprints"][0]["polygon"][0], (7, 9))])
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            data = {"proposals": [], "evidence": [], "selected_id": "longhouse"}
            for profile in LAYOUTS:
                spec = {"width": 96, "height": 96, "style": "ext_outline", "ops": [
                    {"op": "building", "w": 96, "h": 96, "architecture": {"profile": profile}, "massing_only": True}]}
                (root / f"{profile}.json").write_text(json.dumps(spec))
                export_png(run_spec(spec), root / f"{profile}.png")
                data["proposals"].append({"id": profile, "structure": profile, "source_path": f"{profile}.json", "image_path": f"{profile}.png"})
                data["evidence"].extend({"path": f"{profile}.{extension}"} for extension in ("json", "png"))
            validate_submission("alternatives", data, {"contract": {"native_size": [96, 96]}}, root)
            self.assertEqual(len(data["architecture_comparisons"]), 15)
            self.assertTrue(all(not pair["normalized_geometry_equal"] for pair in data["architecture_comparisons"]))

    def test_invalid_or_inactive_controls_are_explicit(self):
        for options in ({"profile": "unknown"}, {"rotation": True}, {"rotation": 45}, {"roof_pitch": float("inf")}, {"wall_height": .1}, {"seed": 2}):
            with self.assertRaises(ValueError):
                build_architecture(96, 96, options)
        with self.assertRaisesRegex(ValueError, "native"):
            build_architecture(32, 32, {})
        with self.assertRaisesRegex(ValueError, "inactive/unsupported"):
            render("tower", chimney=True)
        with self.assertRaisesRegex(ValueError, "inactive field"):
            render("tower", shadow=True)
        with self.assertRaisesRegex(ValueError, "requires architecture"):
            run_spec({"width": 96, "height": 96, "ops": [{"op": "building", "massing_only": True}]})
