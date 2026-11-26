"""Seeded half-plane fractures drive rock masses and rendered stone facets."""

import math
from random import Random

from pixelai.color import brighten, darken, ground_shadow_color, parse_color


PROFILES = {
    "slab": (((.02,.66),(.18,.48),(.72,.44),(.98,.65),(.89,1),(.12,1)),),
    "spire": (((.29,.96),(.26,.36),(.46,.02),(.61,.12),(.78,.83),(.64,1)),),
    "wedge": (((.03,.91),(.17,.68),(.76,.13),(.97,.28),(.92,.96),(.62,1)),),
    "block": (((.08,.88),(.03,.33),(.26,.12),(.77,.19),(.98,.52),(.86,1),(.28,1)),),
    "shard": (((.04,.97),(.23,.50),(.89,.03),(.77,.67),(.59,1)),),
    "twin": (((.02,.94),(.04,.51),(.23,.25),(.47,.49),(.53,.97)),
             ((.42,.98),(.47,.31),(.67,.08),(.93,.39),(.98,.89),(.81,1))),
}


def polygon_area(points):
    return abs(sum(a[0]*b[1]-b[0]*a[1] for a, b in zip(points, points[1:]+points[:1])))/2


def polygon_center(points):
    # A convex polygon's vertex mean is interior and is stable for cut placement.
    return [sum(point[axis] for point in points)/len(points) for axis in range(2)]


def clip_halfplane(points, normal, offset):
    """Retain n.p <= offset; shared cut intersections are computed identically."""
    result = []
    for first, second in zip(points, points[1:]+points[:1]):
        a = sum(first[axis]*normal[axis] for axis in range(2))-offset
        b = sum(second[axis]*normal[axis] for axis in range(2))-offset
        if a <= 1e-9:
            result.append(list(first))
        if (a < -1e-9 and b > 1e-9) or (b < -1e-9 and a > 1e-9):
            ratio = a/(a-b)
            result.append([first[axis]+ratio*(second[axis]-first[axis]) for axis in range(2)])
    return result


def build_fracture(width, height, seed, options, origin=(0, 0)):
    if type(width) is not int or type(height) is not int or width < 32 or height < 32:
        raise ValueError("fracture rocks require native w>=32,h>=32")
    if type(seed) is not int:
        raise ValueError("fracture seed must be an integer")
    if not isinstance(options, dict) or set(options)-{"profile", "cuts", "angle"}:
        raise ValueError("fracture accepts profile, cuts and angle only")
    profile = options.get("profile", "block")
    if not isinstance(profile, str) or profile not in PROFILES:
        raise ValueError(f"fracture.profile must be one of {', '.join(PROFILES)}")
    cuts, angle = options.get("cuts", 3), options.get("angle", -25)
    if type(cuts) is not int or not 1 <= cuts <= 5:
        raise ValueError("fracture.cuts must be an integer between 1 and 5")
    if type(angle) not in (int, float) or not math.isfinite(angle) or not -75 <= angle <= 75:
        raise ValueError("fracture.angle must be between -75 and 75 degrees")
    rng = Random(seed)
    masses = []
    nodes = [{"id": "ground", "parent": None, "role": "ground", "point": [origin[0]+width//2, origin[1]+height-5], "radius": 0}]
    for index, template in enumerate(PROFILES[profile]):
        outline = [[origin[0]+4+x*(width-9), origin[1]+4+y*(height-9)] for x, y in template]
        faces = [outline]
        for cut in range(cuts):
            target = max(range(len(faces)), key=lambda i: polygon_area(faces[i]))
            polygon = faces[target]
            for _ in range(12):
                theta = math.radians(angle+rng.uniform(-22, 22)+(90 if cut%2 else 0))
                normal = [math.cos(theta), math.sin(theta)]
                projections = [sum(point[axis]*normal[axis] for axis in range(2)) for point in polygon]
                offset = min(projections)+(max(projections)-min(projections))*rng.uniform(.35,.65)
                first = clip_halfplane(polygon, normal, offset)
                second = clip_halfplane(polygon, [-value for value in normal], -offset)
                if min(polygon_area(first), polygon_area(second)) >= polygon_area(outline)*.045:
                    faces[target:target+1] = [first, second]
                    break
            else:
                raise ValueError("Fracture cut budget exhausted; reduce cuts or change angle/seed")
        name = f"mass_{index}"
        nodes.append({"id": name, "parent": "ground", "role": "rock_mass", "point": polygon_center(outline), "radius": 0})
        records = []
        for j, polygon in enumerate(faces):
            face_id = f"{name}_facet_{j}"
            center = polygon_center(polygon)
            nodes.append({"id": face_id, "parent": name, "role": "facet", "point": center, "radius": 0})
            for k, point in enumerate(polygon):
                nodes.append({"id": f"{face_id}_corner_{k}", "parent": face_id, "role": "facet_corner", "point": point, "radius": 0})
            records.append({"id": face_id, "polygon": polygon})
        masses.append({"id": name, "outline": outline, "facets": records})
    return {"type": "fracture_graph", "schema_version": 1, "profile": profile, "seed": seed,
            "cuts": cuts, "angle": angle, "ground_anchor": nodes[0]["point"], "nodes": nodes, "masses": masses}


def draw_fracture(canvas, x, y, palette, op):
    from pixelai.schema import UNIVERSAL_OP_FIELDS
    supported = {"x", "y", "kind", "variant", "w", "h", "seed", "color", "shadow_color", "fracture"}
    inactive = set(op)-supported-UNIVERSAL_OP_FIELDS
    if inactive:
        raise ValueError("Fracture mode has inactive/unsupported fields: "+", ".join(sorted(inactive)))
    if op.get("variant", "boulder") != "boulder":
        raise ValueError("fracture currently supports bare boulder geometry only")
    width, height = op.get("w", 32), op.get("h", 32)
    graph = build_fracture(width, height, op.get("seed", 42), op["fracture"], (x, y))
    stone = parse_color(op.get("color", "stone" if "stone" in palette else "#8694a8"), palette)
    if op.get("shadow", True):
        previous = canvas.mark_shadow, canvas.mark_no_outline
        canvas.mark_shadow = canvas.mark_no_outline = True
        shadow = ground_shadow_color(parse_color(op.get("shadow_color", "shadow" if "shadow" in palette else "#33293a"), palette))
        canvas.draw_ellipse(x+width//2, y+height-4, max(2, width//3), 1, shadow)
        canvas.mark_shadow, canvas.mark_no_outline = previous
    for mass in graph["masses"]:
        for facet in mass["facets"]:
            center = polygon_center(facet["polygon"])
            light = (center[0]-x)/width*.32+(center[1]-y)/height*.55
            factor = 1.35-light
            color = brighten(stone, factor) if factor >= 1 else darken(stone, factor)
            canvas.draw_polygon([[round(v) for v in point] for point in facet["polygon"]], color)
    canvas.attachments.append(graph)
