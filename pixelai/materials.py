"""Small, coherent texture clusters for material-specific surface accents."""

PATTERNS = frozenset({"rock", "soil", "leaves", "bark", "water", "cloth"})


def material_accent(pattern: str, x: int, y: int, seed: int, density: float) -> bool:
    """Select whole motifs rather than independent noisy pixels."""
    cell_w, cell_h = {
        "rock": (9, 7), "soil": (6, 4), "leaves": (5, 4),
        "bark": (5, 9), "water": (12, 5), "cloth": (6, 6),
    }[pattern]
    row = y // cell_h
    shifted = x + (row % 2) * (cell_w // 2)
    col, u, v = shifted // cell_w, shifted % cell_w, y % cell_h
    code = ((row * 73856093) ^ (col * 19349663) ^ (seed * 83492791)) & 0xFFFF
    if code / 65536 >= density:
        return False
    if pattern == "rock":
        return (v == 1 and 2 <= u <= 5) or (v in (2, 3) and u == 6 - v)
    if pattern == "soil":
        return (v == 1 and u in (1, 2)) or (v == 2 and u == 4)
    if pattern == "leaves":
        return (v == 1 and u in (1, 2)) or (v == 2 and u in (2, 3))
    if pattern == "bark":
        return (u == 1 and 1 <= v <= 5) or (u == 2 and v in (5, 6))
    if pattern == "water":
        return (v == 1 and 2 <= u <= 7) or (v == 2 and u in (1, 8))
    return (u == 1 and 1 <= v <= 4) or (v == 4 and u in (2, 3))
