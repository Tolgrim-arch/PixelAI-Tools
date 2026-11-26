"""Named, parented native-pixel parts shared by procedural asset families."""


def resolve_parts(parts):
    """Validate a part graph and return stable draw order with absolute origins."""
    if not isinstance(parts, list) or not parts:
        raise ValueError("assembly.parts must be a nonempty array")
    indexed = {}
    for part in parts:
        if not isinstance(part, dict) or not isinstance(part.get("id"), str) or not part["id"].strip():
            raise ValueError("Each part requires a nonempty id")
        if part["id"] in indexed:
            raise ValueError("Part ids must be unique")
        allowed = {"id", "parent", "offset", "width", "height", "ops", "z", "material"}
        if set(part) - allowed:
            raise ValueError(f"Unknown part fields: {sorted(set(part) - allowed)}")
        for name in ("width", "height"):
            if type(part.get(name)) is not int or part[name] < 1:
                raise ValueError(f"part.{name} must be a positive integer")
        offset = part.get("offset", [0, 0])
        if not isinstance(offset, list) or len(offset) != 2 or any(type(v) is not int for v in offset):
            raise ValueError("part.offset must contain two native integer coordinates")
        if type(part.get("z", 0)) is not int:
            raise ValueError("part.z must be an integer")
        if not isinstance(part.get("ops"), list):
            raise ValueError("part.ops must be an array")
        parent = part.get("parent")
        if parent is not None and not isinstance(parent, str):
            raise ValueError("part.parent must be an id or null")
        indexed[part["id"]] = part
    resolved, visiting = {}, set()

    def origin(name):
        if name in resolved:
            return resolved[name]
        if name in visiting:
            raise ValueError("Part graph contains a parent cycle")
        if name not in indexed:
            raise ValueError(f"Missing parent part: {name}")
        visiting.add(name)
        part = indexed[name]
        parent = origin(part["parent"]) if part.get("parent") is not None else (0, 0)
        offset = part.get("offset", [0, 0])
        resolved[name] = (parent[0] + offset[0], parent[1] + offset[1])
        visiting.remove(name)
        return resolved[name]

    for name in indexed:
        origin(name)
    return [(part, resolved[part["id"]]) for part in sorted(parts, key=lambda part: part.get("z", 0))]
