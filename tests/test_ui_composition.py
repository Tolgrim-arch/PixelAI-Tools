"""UI compositions reserve content, bound ornament and preserve state geometry."""

import unittest

from pixelai.runner import run_spec
from pixelai.ui_composition import PROFILES, STATES, build_layout


def render(profile,state="normal",width=64,height=40,**fields):
    return run_spec({"width":width,"height":height,"style":"lineless","ops":[
        {"op":"ui_rig","w":width,"h":height,"state":state,"composition":{"profile":profile},**fields}]})


class UICompositionTest(unittest.TestCase):
    def test_size_profile_state_matrix_protects_content(self):
        for width,height in ((64,40),(96,48),(128,64)):
            for profile in PROFILES:
                geometry = None
                for state in STATES:
                    with self.subTest(size=(width,height),profile=profile,state=state):
                        canvas = render(profile,state,width,height)
                        self.assertEqual(canvas.clipped_pixels,0)
                        self.assertEqual(canvas.warnings,[])
                        graph = canvas.attachments[0]
                        if geometry is None:
                            geometry = graph["content"]
                        self.assertEqual(graph["content"],geometry)
                        content = graph["content"]
                        colors = {canvas.get_pixel(x,y) for x in range(content["min"][0],content["max"][0]) for y in range(content["min"][1],content["max"][1])}
                        self.assertEqual(len(colors),1)
                        self.assertLessEqual(len(graph["anchors"]),4)

    def test_states_have_distinct_pixels_and_profiles_have_distinct_layouts(self):
        for profile in PROFILES:
            self.assertEqual(len({tuple(render(profile,state).pixels) for state in STATES}),6)
        layouts = [build_layout(64,40,{"profile":profile}) for profile in PROFILES]
        self.assertEqual(len({str((item["content"],item["cuts"],item["anchors"])) for item in layouts}),6)

    def test_invalid_and_inactive_controls(self):
        for options in ({"profile":"unknown"},{"border":True},{"padding":1},{"ornament_budget":5},{"content_min":[100,20]},{"profile":"quiet","motif":"stud"}):
            with self.assertRaises(ValueError):
                build_layout(64,40,options)
        with self.assertRaisesRegex(ValueError,"inactive/unsupported"):
            render("header",frame_width=4)
        with self.assertRaisesRegex(ValueError,"normal/hover"):
            render("quiet",state="mystery")

    def test_managed_proposals_compare_layout_geometry_without_theme(self):
        import json
        from pathlib import Path
        import tempfile
        from pixelai.exporter import export_png
        from pixelai.production_contracts import validate_submission
        from pixelai.structure import compare_graphs
        self.assertTrue(compare_graphs(render("header").attachments[0],render("header",theme="gold").attachments[0])["normalized_geometry_equal"])
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            data = {"proposals":[],"evidence":[],"selected_id":"quiet"}
            for profile in PROFILES:
                spec = {"width":64,"height":40,"style":"lineless","ops":[{"op":"ui_rig","w":64,"h":40,"composition":{"profile":profile}}]}
                (root/f"{profile}.json").write_text(json.dumps(spec))
                export_png(run_spec(spec),root/f"{profile}.png")
                data["proposals"].append({"id":profile,"structure":profile,"source_path":f"{profile}.json","image_path":f"{profile}.png"})
                data["evidence"].extend({"path":f"{profile}.{extension}"} for extension in ("json","png"))
            validate_submission("alternatives",data,{"contract":{"native_size":[64,40]}},root)
            self.assertEqual(len(data["ui_comparisons"]),15)
            self.assertTrue(all(not pair["normalized_geometry_equal"] for pair in data["ui_comparisons"]))
