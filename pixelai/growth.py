"""Seeded growth architectures shared by trunk geometry and canopy supports."""

import math
import random

from pixelai.geometry import tapered_polygon


PROFILES = ("upright", "forked", "multi_stem", "gnarled", "leaning", "windswept")


def build_growth_graph(width, height, seed, options):
    if type(width) is not int or type(height) is not int or width < 32 or height < 40:
        raise ValueError("Growth trees require native width >= 32 and height >= 40")
    if not isinstance(options, dict) or set(options) - {"profile", "lean", "spread", "thickness", "root_span"}:
        raise ValueError("growth accepts profile, lean, spread, thickness and root_span")
    profile = options.get("profile", "forked")
    if profile not in PROFILES:
        raise ValueError(f"Unknown growth profile; choose {', '.join(PROFILES)}")
    values = {}
    for key, default, low, high in (("lean", 0, -1, 1), ("spread", 1, .6, 1.25),
                                    ("thickness", 1, .6, 1.8), ("root_span", 1, .6, 1.5)):
        value = options.get(key, default)
        if type(value) not in (int, float) or not math.isfinite(value) or not low <= value <= high:
            raise ValueError(f"growth.{key} must be between {low} and {high}")
        values[key] = value
    rng = random.Random(seed ^ 0x6A09E667)
    cx, foot = width // 2, height - max(7, height // 14)
    rx, ry = width * .34, height * .27
    cy = max(ry + 4, height * .38)
    radius = max(1.6, width * .045 * values["thickness"])
    lean = values["lean"] if "lean" in options else rng.choice((-1, 1)) * rng.uniform(.18, .40)
    nodes = []

    def add(name, parent, x, y, scale, role="stem"):
        node = {"id": name, "parent": parent,
                "point": [round(max(4, min(width-5, x))), round(max(5, min(foot, y)))],
                "radius": max(.7, radius * scale), "role": role}
        nodes.append(node)
        return name

    add("base", None, cx, foot-2, 1.05)
    root_patterns = {
        "upright": (-2.0, 2.3), "forked": (-3.1, -.6, 2.8),
        "multi_stem": (-3.7, .2, 3.5), "gnarled": (-3.3, -1.4, 2.4, 3.6),
        "leaning": (-3.6, 1.9), "windswept": (-4.0, -.8, 2.1),
    }
    handed = -1 if lean < 0 else 1
    for index, spread in enumerate(root_patterns[profile]):
        span = radius * spread * values["root_span"] * rng.uniform(.88, 1.12)
        add(f"root_{index}", "base", cx + handed * span, foot-(index % 2), .24, "root")
    if profile == "forked":
        fork = add("low_fork", "base", cx + lean*rx*.18, foot - height*.12, .85)
        parents = [add(f"bough_{i}", fork, cx + side*rx*.40 + lean*rx*.2, cy+ry*.70, .58)
                   for i, side in enumerate((-1, 1))]
        layout = [(-.65, .04), (-.32, -.55), (.23, -.64), (.63, .15)]
    elif profile == "multi_stem":
        parents = [add(f"stem_{i}", "base", cx + side*rx*.58 + lean*rx*.12, cy+ry*.65, .52)
                   for i, side in enumerate((-1, 0, 1))]
        layout = [(-.67, .14), (-.38, -.47), (.03, -.65), (.35, -.38), (.68, .20)]
    elif profile == "gnarled":
        side = -1 if lean < 0 else 1
        bend = add("lower_bend", "base", cx + side*rx*.36, foot-height*.14, .95)
        bend = add("upper_bend", bend, cx - side*rx*.23, cy+ry*1.05, .80)
        parents = [add("high_fork", bend, cx + side*rx*.12, cy+ry*.55, .65)]
        layout = [(-.63, .10), (-.34, -.60), (.17, -.74), (.63, .20)]
    else:
        amount = lean if profile == "upright" or "lean" in options else (1 if lean >= 0 else -1) * max(.65, abs(lean))
        bend = add("trunk_knee", "base", cx + amount*rx*.34, foot-height*.19, .90)
        parents = [add("high_fork", bend, cx + amount*rx*.72, cy+ry*.78, .65)]
        if profile == "windswept":
            side = 1 if amount > 0 else -1
            layout = [(side*-.12, -.50), (side*.30, -.74), (side*.72, -.20), (side*.75, .36)]
        else:
            shift = amount*.25
            layout = [(-.60+shift, .12), (-.22+shift, -.63), (.23+shift, -.70), (.62+shift, .15)]
    for index, (tx, ty) in enumerate(layout):
        parent_index = min(len(parents)-1, index*len(parents)//len(layout))
        add(f"crown_tip_{index}", parents[parent_index],
            cx + tx*rx*values["spread"] + rng.uniform(-.07, .07)*rx,
            cy + ty*ry + rng.uniform(-.07, .07)*ry, .30, "tip")
    return {"schema_version": 1, "profile": profile, "ground_anchor": [cx, foot], "nodes": nodes}


def draw_growth_trunk(canvas, graph, bark):
    if len(bark) < 4:
        raise ValueError("Growth trees require at least four bark ramp colors")
    nodes = {node["id"]: node for node in graph["nodes"]}
    for node in graph["nodes"]:
        if node["parent"] is None:
            continue
        parent = nodes[node["parent"]]
        start, end = parent["point"], node["point"]
        quad = tapered_polygon(start, end, parent["radius"], node["radius"])
        polygon = lambda points: [(round(x), round(y)) for x, y in points]
        canvas.draw_polygon(polygon(quad), bark[1], filled=True)
        side = (0, 1) if quad[0][0] <= quad[3][0] else (3, 2)
        canvas.draw_polygon(polygon([quad[side[0]], quad[side[1]], end, start]), bark[2], filled=True)
        if node["role"] == "stem" and parent["radius"] >= 2:
            a, b = quad[side[0]], quad[side[1]]
            inner_a = (a[0]*.65 + start[0]*.35, a[1]*.65 + start[1]*.35)
            inner_b = (b[0]*.65 + end[0]*.35, b[1]*.65 + end[1]*.35)
            canvas.draw_polygon(polygon([a, b, inner_b, inner_a]), bark[3], filled=True)


def crown_bands(graph, width, height, seed, sway=0):
    from pixelai import leafstudy as leaves
    rng = random.Random(seed ^ 0xBB67AE85)
    bands = {}
    for node in graph["nodes"]:
        if node["role"] != "tip":
            continue
        x, y = node["point"]
        radius = max(4, round(width * rng.uniform(.19, .23)))
        radius = min(radius, max(4, min(x-3, width-4-x, y-3)))
        mass = leaves._disc_bands(x+sway, y, radius, leaves._L2,
                                 (-.17, -.2, .88), (-.2, -.2, 1.0))
        for point, tone in mass.items():
            px, py = point
            if 2 <= px < width-2 and 2 <= py < height-7:
                bands[point] = min(bands.get(point, 3), tone)
    return bands
