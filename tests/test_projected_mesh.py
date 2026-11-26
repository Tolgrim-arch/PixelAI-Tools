"""Projected faces must preserve occlusion and coplanar detail independent of order."""

import unittest

from pixelai.canvas import Canvas
from pixelai.projected_mesh import ProjectedMesh


class ProjectedMeshTest(unittest.TestCase):
    def test_depth_and_overlay_priority_are_order_independent(self):
        red, blue, green = (220, 40, 40, 255), (40, 60, 200, 255), (40, 180, 80, 255)
        far = [(2, 2, 0), (12, 2, 0), (12, 12, 0), (2, 12, 0)]
        near = [(2, 2, 3), (12, 2, 3), (12, 12, 3), (2, 12, 3)]
        overlay = [(4.3, 4.7, 3), (9.4, 4.7, 3), (9.4, 9.2, 3), (4.3, 9.2, 3)]
        rendered = []
        for faces in ([(far, red, 0), (near, blue, 0), (overlay, green, 1)],
                      [(overlay, green, 1), (near, blue, 0), (far, red, 0)]):
            canvas = Canvas(16, 16)
            mesh = ProjectedMesh(canvas, lambda point: point[:2])
            for points, color, priority in faces:
                mesh.face(points, color, priority)
            mesh.commit()
            rendered.append(canvas.pixels)
            self.assertEqual(canvas.get_pixel(6, 6), green)
            self.assertEqual(canvas.get_pixel(3, 3), blue)
        self.assertEqual(rendered[0], rendered[1])
