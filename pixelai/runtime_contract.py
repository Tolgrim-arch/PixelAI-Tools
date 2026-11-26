"""Attach explicit runtime coordinates before renderer transforms."""

from copy import deepcopy

from pixelai.manifest import _point
from pixelai.geometry import validate_polygon


def attach_runtime(canvas, spec, index, count):
    runtime = spec.get("runtime")
    if runtime is None:
        return
    allowed = {"pivot", "ground_anchor", "sort_origin", "regions", "sockets", "view", "action", "state"}
    if not isinstance(runtime, dict) or set(runtime) - allowed - {"frame_overrides", "derive", "regions_from_structure"}:
        raise ValueError("runtime contains unknown fields")
    if "regions_from_structure" in runtime and (runtime["regions_from_structure"] != "footprints" or runtime.get("derive") != "structure"):
        raise ValueError("runtime.regions_from_structure requires footprints and derive:structure")
    overrides = runtime.get("frame_overrides", {})
    if not isinstance(overrides, dict) or any(not isinstance(key, str) or key not in {str(i) for i in range(count)} for key in overrides):
        raise ValueError("runtime.frame_overrides must use rendered frame index strings")
    record = {}
    if "derive" in runtime:
        if runtime["derive"] != "structure":
            raise ValueError("runtime.derive currently accepts structure only")
        graphs = [item for item in canvas.attachments if item.get("type") in ("anatomy_graph", "growth_graph", "architecture_graph", "fracture_graph", "ui_graph")]
        if len(graphs) != 1:
            raise ValueError("runtime.derive requires exactly one rendered structural graph; enable semantic generation and render one asset/component per spec")
        graph = graphs[0]
        record = {"pivot": deepcopy(graph["ground_anchor"]), "ground_anchor": deepcopy(graph["ground_anchor"]),
                  "sort_origin": deepcopy(graph["ground_anchor"]),
                  "sockets": {node["id"]: deepcopy(node["point"]) for node in graph["nodes"] if node["role"] in ("hand", "foot", "tip", "entrance")}}
        if "regions_from_structure" in runtime:
            if graph["type"] != "architecture_graph":
                raise ValueError("Footprint region derivation requires an architecture graph")
            record["regions"] = [{"id": f"footprint_{item['id']}", "role": "collision", "polygon": deepcopy(item["polygon"])} for item in graph["footprints"]]
        for tag in ("view", "action", "state"):
            if tag in graph:
                record[tag] = graph[tag]

    def merge(fields):
        for key, value in fields.items():
            if key == "sockets":
                if not isinstance(value, dict):
                    raise ValueError("runtime.sockets must be an object")
                record["sockets"] = {**record.get("sockets", {}), **deepcopy(value)}
            else:
                record[key] = deepcopy(value)

    merge({key: value for key, value in runtime.items() if key in allowed})
    override = overrides.get(str(index), {})
    if not isinstance(override, dict) or set(override) - allowed:
        raise ValueError("Runtime frame override contains unknown fields")
    merge(override)
    for tag in ("view", "action", "state"):
        if tag in record and (not isinstance(record[tag], str) or not record[tag].strip()):
            raise ValueError(f"runtime.{tag} must be a nonempty name")
    for name in ("pivot", "ground_anchor", "sort_origin"):
        _point(record.get(name), f"runtime.{name}")
    if not isinstance(record.get("sockets", {}), dict):
        raise ValueError("runtime.sockets must be an object")
    for name, value in record.get("sockets", {}).items():
        _point(value, f"runtime.socket.{name}")
    regions = record.get("regions", [])
    if not isinstance(regions, list):
        raise ValueError("runtime.regions must be an array")
    identifiers = set()
    for region in regions:
        if not isinstance(region, dict) or not isinstance(region.get("id"), str) or not region["id"] or region["id"] in identifiers:
            raise ValueError("Runtime regions require unique ids")
        identifiers.add(region["id"])
        if region.get("role") not in ("collision", "hit", "hurt", "interaction", "occluder"):
            raise ValueError("Runtime region has an unsupported role")
        validate_polygon(region.get("polygon"))
    canvas.attachments.append({"type": "runtime", **record})
