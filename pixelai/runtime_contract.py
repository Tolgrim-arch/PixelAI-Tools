"""Attach explicit runtime coordinates before renderer transforms."""

from copy import deepcopy

from pixelai.manifest import _point
from pixelai.geometry import validate_polygon


def attach_runtime(canvas, spec, index, count):
    runtime = spec.get("runtime")
    if runtime is None:
        return
    allowed = {"pivot", "ground_anchor", "sort_origin", "regions", "sockets", "view", "action", "state"}
    if not isinstance(runtime, dict) or set(runtime) - allowed - {"frame_overrides"}:
        raise ValueError("runtime contains unknown fields")
    overrides = runtime.get("frame_overrides", {})
    if not isinstance(overrides, dict) or any(not isinstance(key, str) or key not in {str(i) for i in range(count)} for key in overrides):
        raise ValueError("runtime.frame_overrides must use rendered frame index strings")
    record = {key: deepcopy(value) for key, value in runtime.items() if key in allowed}
    override = overrides.get(str(index), {})
    if not isinstance(override, dict) or set(override) - allowed:
        raise ValueError("Runtime frame override contains unknown fields")
    record.update(deepcopy(override))
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
