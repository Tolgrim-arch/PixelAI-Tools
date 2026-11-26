"""Explicit view/action/state coverage for universal asset deliveries."""

from pixelai.manifest import load_manifest


TAGS = ("view", "action", "state")


def validate_delivery(delivery):
    if not isinstance(delivery, dict) or set(delivery) - {"views", "actions", "states", "required_combinations", "distinct_views"}:
        raise ValueError("delivery contains unsupported fields")
    for plural in ("views", "actions", "states"):
        names = delivery.get(plural, [])
        if not isinstance(names, list) or any(not isinstance(name, str) or not name.strip() for name in names) or len(set(names)) != len(names):
            raise ValueError(f"delivery.{plural} must contain unique nonempty names")
    if "distinct_views" in delivery and type(delivery["distinct_views"]) is not bool:
        raise ValueError("delivery.distinct_views must be a boolean")
    if delivery.get("distinct_views") and len(delivery.get("views", [])) < 2:
        raise ValueError("distinct_views requires at least two declared views")
    combinations = delivery.get("required_combinations", [])
    if not isinstance(combinations, list):
        raise ValueError("delivery.required_combinations must be an array")
    for combination in combinations:
        if not isinstance(combination, dict) or not combination or set(combination) - set(TAGS):
            raise ValueError("Required combinations must specify view, action and/or state")
        if any(not isinstance(value, str) or not value.strip() for value in combination.values()):
            raise ValueError("Required combination tags must be nonempty names")


def verify_delivery(manifest_path, delivery):
    validate_delivery(delivery)
    data, texture = load_manifest(manifest_path)
    reachable = {name for clip in data["clips"].values() for name in clip["frames"]}
    frames = [frame for frame in data["frames"] if frame["id"] in reachable]
    failures = []
    for tag, plural in zip(TAGS, ("views", "actions", "states")):
        actual = {frame.get(tag) for frame in frames}
        missing = set(delivery.get(plural, [])) - actual
        if missing:
            failures.append(f"Missing {plural}: {', '.join(sorted(missing))}")
    for combination in delivery.get("required_combinations", []):
        if not any(all(frame.get(tag) == value for tag, value in combination.items()) for frame in frames):
            failures.append(f"Missing required combination: {combination}")
    if delivery.get("distinct_views", False):
        groups = {}
        for frame in frames:
            if frame.get("view") not in delivery.get("views", []):
                continue
            group = (frame.get("action"), frame.get("state"))
            x, y, width, height = frame["rect"]
            image = texture.crop((x, y, x+width, y+height))
            pixels = getattr(image, "get_flattened_data", image.getdata)()
            signature = image.size, tuple(pixel if pixel[3] else (0, 0, 0, 0) for pixel in pixels)
            groups.setdefault(group, {}).setdefault(frame["view"], set()).add(signature)
        for group, views in groups.items():
            names = list(views)
            for index, name in enumerate(names):
                for other in names[index+1:]:
                    if views[name] == views[other]:
                        failures.append(f"Views {name}/{other} contain identical frame content for {group}")
    if failures:
        raise ValueError("; ".join(failures))
    return {"status": "covered", "asset_id": data["asset_id"], "delivery": delivery}
