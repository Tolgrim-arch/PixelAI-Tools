"""Structural comparisons ignore labels, palette, translation and scale."""

from copy import deepcopy
import unittest

from pixelai.filters import _transform_attachment_points
from pixelai.growth import build_growth_graph
from pixelai.structure import compare_growth


class StructureTest(unittest.TestCase):
    def test_labels_translation_scale_and_reflection(self):
        graph = build_growth_graph(64, 78, 41, {"profile": "forked"})
        moved = _transform_attachment_points(graph, factor=2, dx=10, dy=20)
        moved["profile"] = "Unrelated marketing claim"
        self.assertTrue(compare_growth(graph, moved)["normalized_geometry_equal"])
        renamed = deepcopy(graph)
        names = {node["id"]: str(index) for index, node in enumerate(renamed["nodes"])}
        for node in renamed["nodes"]:
            node["id"] = names[node["id"]]
            node["parent"] = names[node["parent"]] if node["parent"] is not None else None
        self.assertTrue(compare_growth(graph, renamed)["normalized_geometry_equal"])
        mirrored = deepcopy(graph)
        anchor = graph["ground_anchor"][0]
        for node in mirrored["nodes"]:
            node["point"][0] = anchor * 2 - node["point"][0]
        self.assertTrue(compare_growth(graph, mirrored)["mirrored_geometry_equal"])
        changed = build_growth_graph(64, 78, 41, {"profile": "multi_stem"})
        self.assertFalse(compare_growth(graph, changed)["topology_equal"])
        self.assertIsNone(compare_growth(graph, changed)["approval"])
