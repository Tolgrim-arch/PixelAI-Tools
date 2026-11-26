"""Graph motion diagnostics distinguish planted body changes from root travel."""

from copy import deepcopy
import unittest

from pixelai.canvas import Canvas
from pixelai.motion_analysis import analyze_motion


def frame(chest=(0, -10), hand=(4, -8), anchor=(10, 20)):
    canvas = Canvas(32, 32)
    nodes = [{"id": "ground", "parent": None, "role": "ground", "point": list(anchor)}]
    for name, role, offset in (("chest", "chest", chest), ("hand", "hand", hand)):
        nodes.append({"id": name, "parent": "ground", "role": role, "point": [anchor[axis]+offset[axis] for axis in range(2)]})
    canvas.attachments.append({"type": "anatomy_graph", "nodes": nodes, "ground_anchor": list(anchor), "view": "right", "action": "attack"})
    return canvas


class MotionAnalysisTest(unittest.TestCase):
    def test_review_packet_recomputes_motion_from_verified_source(self):
        from contextlib import redirect_stdout
        import io
        import json
        from pathlib import Path
        import tempfile
        from pixelai.cli import main
        from pixelai.evidence import bind_evidence
        from pixelai.review_packet import prepare_packet
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            spec = {"asset_id": "worker", "width": 64, "height": 64, "style": "lineless", "runtime": {"derive": "structure"},
                    "frames": [{"ops": [{"op": "char_rig", "size": 64, "shadow": False, "posture": {"lean": lean}}]} for lean in (0, .15)]}
            (root / "source.json").write_text(json.dumps(spec))
            with redirect_stdout(io.StringIO()):
                self.assertEqual(main(["render", str(root / "source.json"), "-o", str(root / "sheet.png"), "--manifest", str(root / "asset.json")]), 0)
            construction = {"source_path": "source.json", "image_path": "sheet.png", "manifest_path": "asset.json",
                            "evidence": bind_evidence(root, [{"path": name} for name in ("source.json", "sheet.png", "asset.json")]),
                            "motion_diagnostics": {"status": "FAKE AUTHOR CLAIM"}}
            packet = prepare_packet(root, {"native_size": [64, 64], "category": "human"}, construction, "art_review")
            self.assertEqual(packet["motion_diagnostics"]["status"], "available")
            self.assertTrue(packet["motion_diagnostics"]["report"]["clips"]["default"]["body_motion_detected"])
            self.assertNotIn("FAKE AUTHOR CLAIM", json.dumps(packet))

    def test_limb_only_root_travel_and_body_loading(self):
        frames = [frame(), frame(hand=(8, -8)), frame(chest=(2, -9), hand=(8, -8), anchor=(15, 20))]
        report = analyze_motion(frames, [100, 50, 200], {"strike": {"frames": [0, 1, 2], "loop": False}}, True)
        strike = report["clips"]["strike"]
        self.assertTrue(strike["transitions"][0]["limb_without_body_motion"])
        self.assertEqual(strike["transitions"][0]["at_ms"], 100)
        self.assertEqual(strike["transitions"][1]["at_ms"], 150)
        self.assertEqual(strike["transitions"][1]["ground_delta_px"], 5)
        self.assertEqual(strike["joint_tracks"]["chest"]["span_px"], [2, 1])
        self.assertTrue(strike["body_motion_detected"])
        self.assertIsNone(report["approval"])
        root_only = analyze_motion([frame(), frame(anchor=(20, 20))], [100, 100], {"move": {"frames": [0, 1], "loop": True}})
        self.assertFalse(root_only["clips"]["move"]["body_motion_detected"])

    def test_holds_and_loop_join_timing(self):
        report = analyze_motion([frame(), frame(chest=(2, -10))], [100, 200], {"loop": {"frames": [0, 0, 1], "loop": True}})
        transitions = report["clips"]["loop"]["transitions"]
        self.assertEqual([item["at_ms"] for item in transitions], [100, 200, 400])
        self.assertEqual(transitions[0]["body_max_delta_px"], 0)
        self.assertTrue(transitions[-1]["loop_join"])
        self.assertNotIn("ground_relative_path", report["clips"]["loop"]["joint_tracks"]["chest"])

    def test_ambiguous_and_inconsistent_graphs(self):
        first, second = frame(), frame()
        second.attachments.append(deepcopy(second.attachments[0]))
        with self.assertRaisesRegex(ValueError, "exactly one"):
            analyze_motion([first, second], [100, 100], {"bad": {"frames": [0, 1], "loop": False}})
        second.attachments.pop()
        second.attachments[0]["nodes"][1]["role"] = "head"
        with self.assertRaisesRegex(ValueError, "consistent joint"):
            analyze_motion([first, second], [100, 100], {"bad": {"frames": [0, 1], "loop": False}})
