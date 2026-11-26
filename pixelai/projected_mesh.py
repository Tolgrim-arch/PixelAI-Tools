"""Depth-tested convex faces for small native-resolution projected models."""

import math


class ProjectedMesh:
    def __init__(self, canvas, project):
        self.canvas, self.project = canvas, project
        self.fragments = {}

    def face(self, points, color, priority=0):
        vertices = [(*self.project(point), .55*point[0]-point[1]+.35*point[2]) for point in points]
        for index in range(1, len(vertices)-1):
            self._triangle(vertices[0], vertices[index], vertices[index+1], color, priority)

    def _triangle(self, a, b, c, color, priority):
        denominator = (b[1]-c[1])*(a[0]-c[0])+(c[0]-b[0])*(a[1]-c[1])
        if abs(denominator) < 1e-12:
            return
        left, right = max(0, math.ceil(min(a[0], b[0], c[0]))), min(self.canvas.width-1, math.floor(max(a[0], b[0], c[0])))
        top, bottom = max(0, math.ceil(min(a[1], b[1], c[1]))), min(self.canvas.height-1, math.floor(max(a[1], b[1], c[1])))
        for y in range(top, bottom+1):
            for x in range(left, right+1):
                first = ((b[1]-c[1])*(x-c[0])+(c[0]-b[0])*(y-c[1]))/denominator
                second = ((c[1]-a[1])*(x-c[0])+(a[0]-c[0])*(y-c[1]))/denominator
                third = 1-first-second
                if min(first, second, third) < -1e-9:
                    continue
                depth = first*a[2]+second*b[2]+third*c[2]
                previous = self.fragments.get((x, y))
                if previous is None or depth > previous[0]+1e-9 or (abs(depth-previous[0]) <= 1e-9 and priority >= previous[1]):
                    self.fragments[x, y] = depth, priority, color

    def commit(self):
        for (x, y), (_, _, color) in self.fragments.items():
            self.canvas.set_pixel(x, y, color)
