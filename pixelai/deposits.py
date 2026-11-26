"""Facet-clipped deposits derived from fault boundaries and exposure planes."""

import math

from pixelai.fracture import clip_halfplane, polygon_area


def clip_convex(subject, boundary):
    signed = sum(a[0]*b[1]-b[0]*a[1] for a, b in zip(boundary, boundary[1:]+boundary[:1]))
    result = subject
    for first, second in zip(boundary, boundary[1:]+boundary[:1]):
        normal = [second[1]-first[1], first[0]-second[0]]
        if signed < 0:
            normal = [-value for value in normal]
        offset = sum(first[axis]*normal[axis] for axis in range(2))
        result = clip_halfplane(result, normal, offset)
        if len(result) < 3:
            return []
    return result


def shared_boundaries(facets):
    """Return positive-length shared segments, including subdivided cut edges."""
    result = []
    for index, first in enumerate(facets):
        for second in facets[index+1:]:
            for a, b in zip(first["polygon"], first["polygon"][1:]+first["polygon"][:1]):
                delta = [b[axis]-a[axis] for axis in range(2)]
                length = math.hypot(*delta)
                if length < 1e-9:
                    continue
                for c, d in zip(second["polygon"], second["polygon"][1:]+second["polygon"][:1]):
                    if any(abs(delta[0]*(point[1]-a[1])-delta[1]*(point[0]-a[0]))/length > 1e-7 for point in (c, d)):
                        continue
                    axis = 0 if abs(delta[0]) >= abs(delta[1]) else 1
                    low, high = sorted(( (point[axis]-a[axis])/delta[axis] for point in (c, d)))
                    low, high = max(0, low), min(1, high)
                    if (high-low)*length > 1e-6:
                        points = [[a[k]+t*delta[k] for k in range(2)] for t in (low, high)]
                        result.append({"points": points, "facets": [first["id"], second["id"]]})
    return sorted(result, key=lambda item: (-math.dist(*item["points"]), item["facets"]))


def on_boundary(point, polygon):
    for first, second in zip(polygon, polygon[1:]+polygon[:1]):
        delta = [second[axis]-first[axis] for axis in range(2)]
        length = math.hypot(*delta)
        if length > 1e-9 and abs(delta[0]*(point[1]-first[1])-delta[1]*(point[0]-first[0]))/length <= 1e-6:
            along = sum((point[axis]-first[axis])*delta[axis] for axis in range(2))/length**2
            if -1e-7 <= along <= 1+1e-7:
                return True
    return False


def validate_deposit(variant, options, cuts):
    if not isinstance(options, dict):
        raise ValueError("deposit must be an object")
    fields = {"pattern", "width", "seams"} if variant == "ore" else {"coverage", "slope"} if variant == "mossy" else set()
    if set(options)-fields or (variant == "boulder" and options):
        raise ValueError(f"Inactive/unsupported deposit controls for {variant}")
    if variant == "ore":
        pattern = options.get("pattern", "vein")
        if pattern not in ("vein", "network", "junction"):
            raise ValueError("deposit.pattern must be vein, network or junction")
        if pattern == "junction" and ("seams" in options or cuts < 2):
            raise ValueError("Junction pockets require cuts>=2 and do not accept seams")
        seams = options.get("seams", min(2, cuts) if pattern == "network" else 1)
        if type(seams) is not int or not 1 <= seams <= min(3, cuts):
            raise ValueError("deposit.seams must be an integer in [1,3] no greater than fracture.cuts")
    limits = (("width", .03, .12),) if variant == "ore" else (("coverage", .1, .5), ("slope", -.5, .5)) if variant == "mossy" else ()
    for field, low, high in limits:
        value = options.get(field, .065 if field == "width" else .3 if field == "coverage" else 0)
        if type(value) not in (int, float) or not math.isfinite(value) or not low <= value <= high:
            raise ValueError(f"deposit.{field} must be between {low} and {high}")


def material_regions(mass, variant, options):
    records = []
    if variant == "mossy":
        outline = mass["outline"]
        top, bottom = min(p[1] for p in outline), max(p[1] for p in outline)
        center = (min(p[0] for p in outline)+max(p[0] for p in outline))/2
        slope = options.get("slope", 0)
        boundary = top+(bottom-top)*options.get("coverage", .3)-slope*center
        for facet in mass["facets"]:
            polygon = clip_halfplane(facet["polygon"], [-slope, 1], boundary)
            if len(polygon) >= 3 and polygon_area(polygon) > .01:
                records.append({"facet": facet["id"], "role": "moss", "polygon": polygon})
    elif variant == "ore":
        outline = mass["outline"]
        extent = min(max(p[k] for p in outline)-min(p[k] for p in outline) for k in range(2))
        faults = shared_boundaries(mass["facets"])
        pattern = options.get("pattern", "vein")
        if pattern == "junction":
            candidates = {}
            for facet in mass["facets"]:
                for point in facet["polygon"]:
                    key = tuple(round(value, 7) for value in point)
                    candidates.setdefault(key, set()).add(facet["id"])
            candidates = [point for point in candidates if sum(on_boundary(point, facet["polygon"]) for facet in mass["facets"]) >= 3]
            if not candidates:
                raise ValueError("No multi-facet junction exists; change fracture angle/seed or increase cuts")
            center = candidates[0]
            for role, factor in (("ore", 1), ("ore_highlight", .45)):
                radius = extent*options.get("width", .065)*factor
                pocket = [[center[0]+math.cos(index*math.pi/4)*radius, center[1]+math.sin(index*math.pi/4)*radius] for index in range(8)]
                for facet in mass["facets"]:
                    polygon = clip_convex(pocket, facet["polygon"])
                    if len(polygon) >= 3 and polygon_area(polygon) > .01:
                        records.append({"facet": facet["id"], "role": role, "polygon": polygon, "junction": list(center)})
            return records
        seams = options.get("seams", min(2, len(faults)) if pattern == "network" else 1)
        for seam in faults[:seams]:
            first, second = seam["points"]
            dx, dy = second[0]-first[0], second[1]-first[1]
            length = math.hypot(dx, dy)
            for role, factor in (("ore", 1), ("ore_highlight", .28)):
                width = extent*options.get("width", .065)*factor
                normal = [-dy/length*width, dx/length*width]
                strip = [[first[k]+normal[k] for k in range(2)], [second[k]+normal[k] for k in range(2)],
                         [second[k]-normal[k] for k in range(2)], [first[k]-normal[k] for k in range(2)]]
                for facet in mass["facets"]:
                    polygon = clip_convex(strip, facet["polygon"])
                    if len(polygon) >= 3 and polygon_area(polygon) > .01:
                        records.append({"facet": facet["id"], "role": role, "polygon": polygon, "fault": seam["points"]})
    return records
