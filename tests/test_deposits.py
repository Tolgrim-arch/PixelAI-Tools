"""Deposits follow modeled faces and cannot change the underlying silhouette."""

import unittest

from pixelai.deposits import clip_convex, shared_boundaries, on_boundary
from pixelai.fracture import PROFILES, build_fracture, polygon_area
from pixelai.runner import run_spec
from pixelai.structure import compare_graphs


def render(profile, variant="boulder", size=48, **fields):
    return run_spec({"width": size, "height": size, "style": "lineless", "ops": [
        {"op": "nature_rig", "kind": "rock", "variant": variant, "w": size, "h": size, "seed": 42, "shadow": False,
         "fracture": {"profile": profile}, **fields}]})


class DepositTest(unittest.TestCase):
    def test_deposits_are_face_clipped_and_preserve_structure(self):
        for size in (32, 64):
            for profile in PROFILES:
                bare = render(profile, size=size)
                for variant in ("ore", "mossy"):
                    with self.subTest(size=size, profile=profile, variant=variant):
                        canvas = render(profile, variant, size)
                        self.assertEqual(canvas.clipped_pixels, 0)
                        self.assertEqual([pixel[3] for pixel in canvas.pixels], [pixel[3] for pixel in bare.pixels])
                        self.assertNotEqual(canvas.pixels, bare.pixels)
                        self.assertTrue(compare_graphs(bare.attachments[0], canvas.attachments[0])["normalized_geometry_equal"])
                        self.assertEqual(render(profile, variant, size, fracture_only=True).pixels, bare.pixels)
                        graph = canvas.attachments[0]
                        facets = {facet["id"]: facet["polygon"] for mass in graph["masses"] for facet in mass["facets"]}
                        self.assertTrue(graph["material_regions"])
                        for region in graph["material_regions"]:
                            self.assertAlmostEqual(polygon_area(clip_convex(region["polygon"], facets[region["facet"]])), polygon_area(region["polygon"]))

    def test_ore_uses_actual_shared_faults_and_moss_uses_exposure_plane(self):
        graph = render("block", "ore", deposit={"seams": 3, "width": .1}).attachments[0]
        faults = [fault["points"] for mass in graph["masses"] for fault in shared_boundaries(mass["facets"])]
        self.assertTrue(all(region["fault"] in faults for region in graph["material_regions"]))
        graph = render("block", "mossy", deposit={"coverage": .4, "slope": .3}).attachments[0]
        outline = graph["masses"][0]["outline"]
        boundary = min(p[1] for p in outline)+(max(p[1] for p in outline)-min(p[1] for p in outline))*.4
        center = (min(p[0] for p in outline)+max(p[0] for p in outline))/2
        for region in graph["material_regions"]:
            self.assertTrue(all(point[1] <= boundary+.3*(point[0]-center)+1e-7 for point in region["polygon"]))

    def test_inactive_invalid_and_missing_deposit_controls(self):
        for variant, options in (("ore", {"seams": True}), ("ore", {"seams": 4}), ("ore", {"width": .2}),
                                 ("ore", {"coverage": .3}), ("mossy", {"slope": float("nan")}), ("mossy", {"coverage": 0})):
            with self.subTest(variant=variant, options=options), self.assertRaises(ValueError):
                render("block", variant, deposit=options)
        with self.assertRaisesRegex(ValueError, "Inactive material"):
            render("block", deposit={})
        with self.assertRaisesRegex(ValueError, "Inactive material"):
            render("block", "mossy", accent_color="#aabbcc")
        with self.assertRaisesRegex(ValueError, "require an explicit fracture"):
            run_spec({"width": 48, "height": 48, "ops": [{"op": "nature_rig", "kind": "rock", "deposit": {}}]})

    def test_junctions_and_networks_are_geometric_and_export_is_source_bound(self):
        from contextlib import redirect_stdout
        import io
        import json
        from pathlib import Path
        import tempfile
        from pixelai.cli import main
        from pixelai.provenance import verify_construction
        for profile in PROFILES:
            bare = render(profile)
            for pattern in ("network", "junction"):
                canvas = render(profile, "ore", deposit={"pattern": pattern, "width": .12})
                self.assertEqual([p[3] for p in bare.pixels], [p[3] for p in canvas.pixels])
                self.assertNotEqual(canvas.pixels, bare.pixels)
                if pattern == "junction":
                    for mass in canvas.attachments[0]["masses"]:
                        regions = [region for region in canvas.attachments[0]["material_regions"] if region["facet"].startswith(mass["id"]+"_")]
                        self.assertTrue(regions)
                        for region in regions:
                            self.assertGreaterEqual(sum(on_boundary(region["junction"], facet["polygon"]) for facet in mass["facets"]), 3)
        with self.assertRaisesRegex(ValueError, "cuts>=2"):
            run_spec({"width": 48, "height": 48, "ops": [{"op": "nature_rig", "kind": "rock", "variant": "ore", "w": 48, "h": 48,
                      "fracture": {"cuts": 1}, "deposit": {"pattern": "junction"}}]})
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            spec = json.loads((Path(__file__).resolve().parents[1] / "specs/fracture_runtime.json").read_text())
            (root / "source.json").write_text(json.dumps(spec))
            with redirect_stdout(io.StringIO()):
                self.assertEqual(main(["render", str(root / "source.json"), "-o", str(root / "ore.png"), "--manifest", str(root / "ore.json")]), 0)
            submission = {"source_path": "source.json", "image_path": "ore.png", "manifest_path": "ore.json",
                          "evidence": [{"path": name} for name in ("source.json", "ore.png", "ore.json")]}
            proof = verify_construction(root, submission, [104, 104])
            self.assertTrue(proof["fracture_graphs"][0]["material_regions"])
            manifest = json.loads((root / "ore.json").read_text())
            self.assertEqual(manifest["frames"][0]["pivot"], proof["fracture_graphs"][0]["ground_anchor"])
            spec["ops"][0]["deposit"]["width"] = .12
            (root / "source.json").write_text(json.dumps(spec))
            with self.assertRaisesRegex(ValueError, "does not match the source"):
                verify_construction(root, submission)
