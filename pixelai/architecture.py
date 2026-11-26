"""Connected building volumes with projected footprint and roof diagnostics."""

import math

from pixelai.color import brighten, darken


# x, depth, width, depth-span, wall height in canonical architectural units.
LAYOUTS = {
    "longhouse": ((0, 0, 12, 4, 5),),
    "l_wing": ((0, 0, 8, 4, 5), (0, 4, 4, 4, 5)),
    "t_plan": ((4, 0, 4, 4, 5), (0, 4, 12, 4, 5)),
    "courtyard": ((0, 0, 12, 2, 4), (0, 2, 3, 6, 5), (9, 2, 3, 6, 5), (3, 6, 6, 2, 5)),
    "stepped": ((0, 0, 6, 6, 7), (6, 1, 5, 4, 4)),
    "tower": ((0, 0, 9, 4, 4), (2, 4, 5, 6, 10)),
}


def build_architecture(width, height, options):
    if type(width) is not int or type(height) is not int or width < 64 or height < 64:
        raise ValueError("architecture requires native w>=64 and h>=64")
    if not isinstance(options, dict) or set(options) - {"profile", "rotation", "wall_height", "roof_pitch"}:
        raise ValueError("architecture accepts profile, rotation, wall_height and roof_pitch only")
    profile = options.get("profile", "longhouse")
    if not isinstance(profile, str) or profile not in LAYOUTS:
        raise ValueError(f"architecture.profile must be one of {', '.join(LAYOUTS)}")
    rotation = options.get("rotation", 0)
    if type(rotation) is not int or rotation not in (0, 90, 180, 270):
        raise ValueError("architecture.rotation must be 0, 90, 180 or 270")
    factors = {}
    for key, low, high in (("wall_height", .8, 1.2), ("roof_pitch", .7, 1.3)):
        value = options.get(key, 1)
        if type(value) not in (int, float) or not math.isfinite(value) or not low <= value <= high:
            raise ValueError(f"architecture.{key} must be between {low} and {high}")
        factors[key] = value
    volumes = []
    for index, (x, y, w, d, h) in enumerate(LAYOUTS[profile]):
        axis = "y"
        for _ in range(rotation//90):
            x, y, w, d = -y-d, x, d, w
            axis = "x" if axis == "y" else "y"
        volumes.append({"id": f"mass_{index}", "x": x, "y": y, "w": w, "d": d,
                        "height": h*factors["wall_height"], "roof_axis": axis,
                        "pitch": factors["roof_pitch"]*.65})
    min_x, min_y = min(v["x"] for v in volumes), min(v["y"] for v in volumes)
    for volume in volumes:
        volume["x"] -= min_x
        volume["y"] -= min_y
    connections = []
    for i, first in enumerate(volumes):
        for second in volumes[i+1:]:
            x_overlap = min(first["x"]+first["w"], second["x"]+second["w"])-max(first["x"], second["x"])
            y_overlap = min(first["y"]+first["d"], second["y"]+second["d"])-max(first["y"], second["y"])
            if x_overlap >= 0 and y_overlap >= 0 and x_overlap+y_overlap > 0:
                connections.append([first["id"], second["id"]])
    cells = {}
    for volume in volumes:
        for x in range(volume["x"], volume["x"]+volume["w"]):
            for y in range(volume["y"], volume["y"]+volume["d"]):
                cells[x, y] = volume
    front_y = min(y for _, y in cells)
    front = sorted(x for x, y in cells if y == front_y)
    entrance = (front[len(front)//2]+.5, front_y, 0)
    return {"profile": profile, "rotation": rotation, "volumes": volumes,
            "connections": connections, "cells": cells, "entrance": entrance}


def roof_height(volume, x, y):
    axis = volume["roof_axis"]
    start, span, value = (volume[axis], volume["w" if axis == "x" else "d"], x if axis == "x" else y)
    return volume["height"]+volume["pitch"]*max(0, min(value-start, start+span-value))


def projection(model, width, height, origin=(0, 0)):
    def raw(point):
        x, y, z = point
        return x+.55*y, -.35*y-z
    points = []
    for volume in model["volumes"]:
        x, y, w, d = (volume[key] for key in ("x", "y", "w", "d"))
        for u in (x, x+w/2, x+w):
            for v in (y, y+d/2, y+d):
                points.extend((raw((u, v, 0)), raw((u, v, roof_height(volume, u, v)))))
    left, right = min(p[0] for p in points), max(p[0] for p in points)
    top, bottom = min(p[1] for p in points), max(p[1] for p in points)
    scale = min((width-10)/(right-left), (height-10)/(bottom-top))
    dx, dy = origin[0]+(width-(right-left)*scale)/2-left*scale, origin[1]+(height-(bottom-top)*scale)/2-top*scale

    def project(point, rounded=True):
        x, y = raw(point)
        result = [dx+x*scale, dy+y*scale]
        return [round(value) for value in result] if rounded else result
    return project, scale


def architecture_graph(model, project, scale):
    ground = project(model["entrance"])
    nodes = [{"id": "ground", "parent": None, "role": "ground", "point": ground, "radius": 0},
             {"id": "entrance", "parent": "ground", "role": "entrance", "point": ground, "radius": 0}]
    footprints = []
    for volume in model["volumes"]:
        name = volume["id"]
        x, y, w, d = (volume[key] for key in ("x", "y", "w", "d"))
        center = (x+w/2, y+d/2)
        nodes.append({"id": name, "parent": "ground", "role": "mass", "point": project((*center, volume["height"]/2)), "radius": 0})
        polygon = [project((u, v, 0)) for u, v in ((x, y), (x+w, y), (x+w, y+d), (x, y+d))]
        footprints.append({"id": name, "polygon": polygon})
        for index, point in enumerate(polygon):
            nodes.append({"id": f"{name}_corner_{index}", "parent": name, "role": "footprint_corner", "point": point, "radius": 0})
        ridge = ((x, y+d/2), (x+w, y+d/2)) if volume["roof_axis"] == "y" else ((x+w/2, y), (x+w/2, y+d))
        for index, (u, v) in enumerate(ridge):
            nodes.append({"id": f"{name}_ridge_{index}", "parent": name, "role": "roof_ridge",
                          "point": project((u, v, roof_height(volume, u, v))), "radius": 0})
    return {"type": "architecture_graph", "schema_version": 1, "profile": model["profile"],
            "rotation": model["rotation"], "ground_anchor": ground, "nodes": nodes,
            "footprints": footprints, "connections": model["connections"], "volumes": model["volumes"]}


def draw_architecture(canvas, palette, op):
    from pixelai.building import _resolve
    from pixelai.schema import UNIVERSAL_OP_FIELDS
    supported = {"x", "y", "w", "h", "architecture", "massing_only", "wall_color", "roof_color", "trim_color", "windows", "door"}
    if set(op) - supported - UNIVERSAL_OP_FIELDS:
        raise ValueError("Architecture mode has inactive/unsupported fields: " + ", ".join(sorted(set(op)-supported-UNIVERSAL_OP_FIELDS)))
    for flag in ("massing_only", "windows", "door"):
        if flag in op and type(op[flag]) is not bool:
            raise ValueError(f"architecture {flag} must be a boolean")
    width, height = op.get("w", canvas.width), op.get("h", canvas.height)
    model = build_architecture(width, height, op["architecture"])
    origin = (op.get("x", 0), op.get("y", 0))
    if any(type(value) is not int for value in origin):
        raise ValueError("architecture x/y must use native integer pixels")
    project, scale = projection(model, width, height, origin)
    wall = _resolve(str(op.get("wall_color", "cream")), palette, (240, 218, 176, 255))
    roof = _resolve(str(op.get("roof_color", "roof")), palette, (194, 75, 56, 255))
    wood = _resolve(str(op.get("trim_color", "wood")), palette, (143, 92, 60, 255))
    cells = model["cells"]
    from pixelai.projected_mesh import ProjectedMesh
    mesh = ProjectedMesh(canvas, lambda point: project(point, rounded=False))

    def face(points, color, priority=0):
        mesh.face(points, color, priority)

    def opening(x, y, left, right, bottom, top, color):
        face([(x+left, y, bottom), (x+right, y, bottom), (x+right, y, top), (x+left, y, top)], color, 1)

    for (x, y), volume in sorted(cells.items(), key=lambda item: (item[0][0]-item[0][1], item[0][0])):
        corners = [(x, y), (x+1, y), (x+1, y+1), (x, y+1)]
        heights = [roof_height(volume, u, v) for u, v in corners]
        for a, b, neighbor, shade in ((0, 1, (x, y-1), 1), (1, 2, (x+1, y), .82)):
            other = cells.get(neighbor)
            bottom = [min(heights[i], roof_height(other, *corners[i])) if other else 0 for i in (a, b)]
            if max(heights[a]-bottom[0], heights[b]-bottom[1]) > 1e-9:
                face([(*corners[a], bottom[0]), (*corners[b], bottom[1]), (*corners[b], heights[b]), (*corners[a], heights[a])], darken(wall, shade))
            if a == 0 and other is None and not op.get("massing_only", False):
                if abs(x+.5-model["entrance"][0]) < .01 and y == model["entrance"][1] and op.get("door", True):
                    opening(x, y, .05, .95, 0, min(2.8, volume["height"]-.6), wood)
                    opening(x, y, .14, .86, 0, min(2.5, volume["height"]-.8), darken(wood, .65))
                elif op.get("windows", True) and x in (volume["x"]+1, volume["x"]+volume["w"]-2):
                    opening(x, y, .1, .9, 1.8, 3.1, wood)
                    opening(x, y, .22, .78, 2, 2.9, (78, 139, 157, 255))
        front_half = (y+.5 < volume["y"]+volume["d"]/2) if volume["roof_axis"] == "y" else (x+.5 < volume["x"]+volume["w"]/2)
        face([(*point, z) for point, z in zip(corners, heights)], brighten(roof, 1.06) if front_half else darken(roof, .82), 2)
    mesh.commit()
    canvas.attachments.append(architecture_graph(model, project, scale))
