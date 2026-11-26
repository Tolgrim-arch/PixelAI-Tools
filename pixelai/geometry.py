"""Finite convex-region validation and positive-area overlap tests."""

import math


def tapered_polygon(start, end, root_radius, tip_radius):
    """Return a tapered segment quad in the caller's coordinate space."""
    dx, dy = end[0] - start[0], end[1] - start[1]
    length = math.hypot(dx, dy) or 1
    nx, ny = -dy / length, dx / length
    return [(start[0] + nx * root_radius, start[1] + ny * root_radius),
            (end[0] + nx * tip_radius, end[1] + ny * tip_radius),
            (end[0] - nx * tip_radius, end[1] - ny * tip_radius),
            (start[0] - nx * root_radius, start[1] - ny * root_radius)]


def _cross(a, b, c):
    return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])


def validate_polygon(points):
    if not isinstance(points, list) or len(points) < 3:
        raise ValueError("Region polygon requires at least three vertices")
    for point in points:
        if not isinstance(point, list) or len(point) != 2 or any(type(v) not in (int, float) or not math.isfinite(v) for v in point):
            raise ValueError("Region vertices must be finite coordinate pairs")
    if len({tuple(point) for point in points}) != len(points):
        raise ValueError("Region polygon repeats a vertex")
    turns = [_cross(points[i-1], points[i], points[(i+1) % len(points)]) for i in range(len(points))]
    if not any(abs(turn) > 1e-9 for turn in turns) or (any(t > 1e-9 for t in turns) and any(t < -1e-9 for t in turns)):
        raise ValueError("Region polygons must be nondegenerate and convex")
    # Consistent turning alone does not rule out a self-intersecting star.
    for i in range(len(points)):
        a, b = points[i], points[(i+1) % len(points)]
        for j in range(i+1, len(points)):
            if j == i+1 or (i == 0 and j == len(points)-1):
                continue
            c, d = points[j], points[(j+1) % len(points)]
            if _cross(a, b, c) * _cross(a, b, d) < 0 and _cross(c, d, a) * _cross(c, d, b) < 0:
                raise ValueError("Region polygon self-intersects")
    return points


def overlap(first, second):
    """SAT overlap for validated convex polygons; boundary contact is not overlap."""
    for polygon in (first, second):
        for i, a in enumerate(polygon):
            b = polygon[(i+1) % len(polygon)]
            axis = (a[1] - b[1], b[0] - a[0])
            pa = [p[0] * axis[0] + p[1] * axis[1] for p in first]
            pb = [p[0] * axis[0] + p[1] * axis[1] for p in second]
            if max(pa) <= min(pb) + 1e-9 or max(pb) <= min(pa) + 1e-9:
                return False
    return True


def world_regions(frame, origin):
    return [{**region, "polygon": [[point[0] + origin[0], point[1] + origin[1]] for point in region["polygon"]]}
            for region in frame.get("regions", [])]
