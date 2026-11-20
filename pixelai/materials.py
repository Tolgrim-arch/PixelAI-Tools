"""Material surfaces and compatible scatter accents."""

from math import cos, pi, sin
from random import Random

from pixelai.canvas import Canvas
from pixelai.color import brighten, darken, parse_color

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


_RAMPS = {
    "rock": ("#484552", "#605c6c", "#777885", "#9596a2", "#b3afb4"),
    "cobble": ("#666468", "#7f7b7b", "#97928c", "#a8a09a", "#c1b8aa"),
    "soil": ("#634344", "#785147", "#926347", "#a67852", "#c28e60"),
    "leaves": ("#264839", "#37603c", "#4b7544", "#709449", "#9aad53"),
    "bark": ("#56383b", "#694337", "#86563d", "#a66d49", "#bd8559"),
    "grass": ("#365f42", "#487347", "#598747", "#79a250", "#a2b954"),
    "water": ("#25576d", "#31778a", "#3e94a0", "#61afb0", "#9bd1c3"),
    "cloth": ("#593756", "#774561", "#995773", "#b87283", "#d99397"),
    "wood": ("#774740", "#8b5945", "#a46d4c", "#bd8758", "#d4a167"),
    "roof": ("#794b57", "#935454", "#b96956", "#cc7e60", "#e0956c"),
}
MATERIALS = frozenset(_RAMPS)
_ALIASES = {"trunk": "bark", "shingle": "roof"}


class _Surface:
    """Draw shapes in 64×48 design coordinates at the requested raster size."""

    def __init__(self, canvas, ramp, seed):
        self.canvas = canvas
        self.ramp = ramp
        self.rng = Random(seed)
        self.sx = canvas.width / 64
        self.sy = canvas.height / 48
        self.detail = min(canvas.width, canvas.height) >= 24

    def plane(self, tone, *points):
        self.canvas.draw_polygon(
            [(round(x * self.sx), round(y * self.sy)) for x, y in points], self.ramp[tone]
        )


def _rock(surface):
    rng = surface.rng
    a = rng.randint(16, 25)
    b = rng.randint(35, 44)
    c = rng.randint(13, 19)
    d = rng.randint(28, 35)
    surface.plane(3, (-1, -1), (b + 8, -1), (b, c), (b - 7, c + 2), (a, d), (7, d - 7), (-1, d - 6))
    surface.plane(1, (b + 8, -1), (65, -1), (65, c + 8), (b, c))
    surface.plane(1, (-1, d - 6), (7, d - 7), (a, d), (a + 13, 49), (-1, 49))
    surface.plane(0, (b, c), (65, c + 8), (65, 49), (b + 7, 49), (b + 4, d))
    surface.plane(1, (b, c), (b + 4, d), (b + 7, 49), (a + 13, 49), (a, d), (b - 7, c + 2))
    surface.plane(2, (-1, d - 8), (7, d - 9), (a - 1, d - 4), (b - 6, c + 2),
                  (b + 1, c), (b - 7, c + 5), (a, d), (7, d - 7), (-1, d - 6))
    surface.plane(4, (a - 9, 3), (a + 5, 2), (a + 13, 5), (a + 3, 8), (a - 3, 11),
                  (a - 10, 11), (a - 4, 7))
    surface.plane(2, (a + 14, d + 2), (b + 3, d - 5), (b + 1, d + 1), (a + 10, d + 7))
    if surface.detail:
        surface.plane(2, (3, 18), (12, 19), (18, 16), (25, 16), (16, 21), (2, 21))
        surface.plane(3, (47, 11), (55, 10), (59, 14), (51, 14))
        surface.plane(2, (4, d + 2), (11, d + 4), (14, d + 8), (8, d + 7))
        surface.plane(2, (52, 36), (62, 39), (63, 42), (53, 40))


def _cobble(surface):
    rng = surface.rng
    row_top = -2
    while row_top < 48:
        row_height = rng.randint(9, 15)
        right = -rng.randint(1, 11)
        while right < 64:
            left = right + 1
            right = left + rng.randint(9, 22)
            top = row_top + rng.randint(0, 2)
            bottom = row_top + row_height - rng.randint(1, 3)
            shoulder = rng.randint(2, 4)
            tone = rng.choice((2, 2, 3))
            surface.plane(1, (left, top + 3), (left + shoulder, top), (right - 3, top),
                          (right, top + 3), (right, bottom - 2), (right - 3, bottom),
                          (left + 2, bottom), (left, bottom - 2))
            surface.plane(tone, (left, top + 3), (left + shoulder, top), (right - 3, top),
                          (right, top + 3), (right - 2, bottom - 3), (left + 2, bottom - 2))
            if surface.detail and right - left > 14:
                surface.plane(tone + 1, (left + 2, top + 3), (left + shoulder + 2, top + 1),
                              (right - 5, top + 1), (right - 8, top + 3))
        row_top += row_height


def _soil(surface):
    """Compacted earth with broad strata, pressed clods, and embedded grit."""
    rng = surface.rng
    # Uneven compacted bands establish a continuous earth body instead of polka-dot
    # islands. Their short breaks and alternating height avoid a striped fabric read.
    y = -4
    while y < 50:
        band = rng.randint(5, 10)
        tone = rng.choice((1, 2, 2, 3))
        start = rng.randint(-12, 5)
        end = rng.randint(53, 76)
        rise = rng.randint(-3, 3)
        surface.plane(tone, (start, y + 2), (start + 7, y), (end - 8, y + rise),
                      (end, y + 3), (end - 5, y + 5), (start + 10, y + 4))
        # Pressed clods overlap the bands and remain broad, low-relief clusters.
        for _ in range(rng.randint(2, 4)):
            cx = rng.randint(-5, 69)
            cy = y + rng.randint(1, max(1, band - 2))
            rx, ry = rng.randint(3, 7), rng.randint(1, 3)
            surface.plane(rng.choice((1, 2, 3)), (cx-rx, cy), (cx-rx+2, cy-ry),
                          (cx+rx-2, cy-ry), (cx+rx, cy), (cx+rx-2, cy+ry),
                          (cx-rx+1, cy+ry))
            if surface.detail:
                surface.plane(4, (cx-rx+2, cy-ry), (cx-1, cy-ry),
                              (cx+1, cy-ry+1), (cx-rx+1, cy+1))
        y += band
    if surface.detail:
        # A few tiny embedded pebbles, each nested in a darker compacted pocket.
        for _ in range(18):
            px, py = rng.randint(1, 62), rng.randint(1, 46)
            width = rng.choice((1, 2, 3))
            surface.plane(0, (px-1, py+1), (px, py-1), (px+width+1, py), (px+width, py+2))
            surface.plane(rng.choice((3, 4)), (px, py), (px+1, py-1),
                          (px+width, py), (px+width-1, py+1))


def _leaves(surface):
    rng = surface.rng
    crowns = [(5, 5), (27, 2), (51, 7), (13, 22), (36, 18), (61, 24), (27, 39), (51, 42), (4, 46)]
    for cx, cy in crowns:
        cx, cy = cx + rng.randint(-3, 3), cy + rng.randint(-3, 3)
        direction = rng.uniform(-pi, pi)
        for leaf in range(6):
            angle = direction + leaf * pi / 3 + rng.uniform(-0.2, 0.2)
            dx, dy = cos(angle), sin(angle)
            length, spread = rng.randint(8, 16), rng.randint(2, 4)
            tip = (cx + dx * length, cy + dy * length)
            shoulder = (cx + dx * length * .56, cy + dy * length * .56)
            left = (shoulder[0] + dy * spread, shoulder[1] - dx * spread)
            right = (shoulder[0] - dy * spread, shoulder[1] + dx * spread)
            tone = rng.choice((1, 2, 2, 3))
            surface.plane(tone, (cx, cy), left, tip, right)
            if surface.detail and leaf in (1, 3, 5):
                rim = min(left, right, key=lambda point: point[1])
                surface.plane(tone + 1, (cx, cy), rim, tip)


def _bark(surface):
    rng = surface.rng
    surface.plane(1, (46, -1), (65, -1), (65, 49), (43, 49), (48, 26))
    surface.plane(3, (14, -1), (31, -1), (26, 14), (29, 28), (23, 49), (8, 49), (16, 30), (12, 18))
    x = -2
    while x < 66:
        width = rng.randint(3, 8)
        y = rng.randint(10, 21)
        bend = rng.randint(-5, 5)
        root = rng.randint(-8, 5)
        surface.plane(1 if 10 < x < 33 else 0, (x, -2), (x + bend, y), (x + root, 49),
                      (x + root + width, 49), (x + bend + width, y + 5), (x + width - 1, -2))
        cut = rng.randint(3, 8)
        plane = 3 if x < 39 else 2
        surface.plane(plane, (x + 1, -2), (x + bend + 3, y + 4), (x + bend + 1, y + cut), (x + bend, y))
        surface.plane(plane, (x + bend + 3, y + cut), (x + root + 2, 43), (x + root, 38), (x + bend + 1, y + cut + 5))
        if surface.detail and width > 5 and x < 40:
            surface.plane(4, (x + 3, 2), (x + bend + 3, y), (x + bend + 3, y + 10), (x + bend + 1, y - 4))
        x += width + rng.randint(2, 7)


def _grass(surface):
    rng = surface.rng
    surface.plane(1, (-1, 23), (12, 18), (34, 21), (52, 14), (65, 17),
                  (65, 35), (48, 35), (29, 42), (12, 37), (-1, 40))
    surface.plane(3, (-1, -1), (37, -1), (41, 6), (28, 12), (15, 10), (-1, 17))
    for x, y in ((2, 12), (24, 8), (44, 13), (60, 5), (6, 28), (34, 28), (53, 26), (17, 43), (46, 43), (65, 41)):
        x, y = x + rng.randint(-4, 4), y + rng.randint(-3, 3)
        span = rng.randint(4, 9)
        surface.plane(1, (x - span, y), (x, y - 4), (x + span + 3, y), (x + span, y + 4), (x - 3, y + 5))
        for blade in range(rng.randint(4, 6)):
            root = x + rng.randint(-span, span)
            height = rng.randint(3, 9)
            lean = rng.randint(0, 5)
            surface.plane(2 + (blade % 3 != 0) + (blade == 1), (root, y + rng.randint(0, 2)),
                          (root + lean, y - height), (root + lean, y - height + 3), (root + 2, y + 1))


def _water(surface):
    rng = surface.rng
    phase = rng.randint(-4, 4)
    surface.plane(1, (-1, -1), (65, -1), (65, 4), (47, 11), (29, 7 + phase), (14, 14), (-1, 13))
    surface.plane(3, (-1, 16), (12, 13), (27, 14 + phase), (42, 9), (58, 12), (65, 8),
                  (65, 16), (51, 20), (38, 16), (24, 21 + phase), (10, 20), (-1, 23))
    surface.plane(0, (-1, 37), (16, 34), (31, 38 + phase), (48, 31), (65, 32), (65, 49), (-1, 49))
    surface.plane(1, (-1, 35), (16, 32), (31, 36 + phase), (48, 29), (65, 30),
                  (65, 35), (47, 34), (30, 43 + phase), (15, 38), (-1, 42))
    for y in (8, 19, 29, 41):
        x = rng.randint(-4, 20)
        span = rng.randint(17, 38)
        lift = rng.randint(-2, 2)
        surface.plane(4 if y in (19, 29) else 3, (x, y), (x + span * .34, y - 2),
                      (x + span * .70, y + lift), (x + span, y - 1),
                      (x + span * .70, y + lift + 2), (x + span * .35, y))
        if surface.detail and x + span < 58:
            surface.plane(3, (x + span + 3, y + 3), (x + span + 12, y + 2), (x + span + 15, y + 3))


def _cloth(surface):
    """Folded woven cloth with a soft silhouette, weave, and stitched hem."""
    rng = surface.rng
    left = rng.randint(5, 10)
    right = rng.randint(54, 60)
    hem = rng.randint(42, 46)
    # A single draped panel with a shallow scallop reads as cloth, not a rock slab.
    surface.plane(1, (left, -1), (right, -1), (right-2, hem-3),
                  (right-10, hem), (left+8, hem-1), (left+2, hem-4))
    surface.plane(2, (left+3, 0), (right-4, 0), (right-9, 8), (right-15, 22),
                  (right-11, 34), (right-13, hem-2), (left+11, hem-3),
                  (left+9, 31), (left+13, 18), (left+6, 8))
    # Soft folds are broad, vertical value ribbons that converge into slack folds.
    for fold in range(5):
        x = left + 8 + fold * max(5, (right-left-16)//4) + rng.randint(-2, 2)
        lean = rng.randint(-4, 4)
        tone = rng.choice((1, 1, 3))
        surface.plane(tone, (x, 4), (x+3, 5), (x+lean+4, 25),
                      (x+lean+2, hem-4), (x+lean-1, hem-3), (x+lean, 24))
        surface.plane(4 if tone == 1 else 2, (x-2, 6), (x, 5),
                      (x+lean, 24), (x+lean-2, hem-4))
    # Fine broken warp/weft glints: short, evenly scaled clusters, not long stripes.
    if surface.detail:
        for yy in range(9, hem-5, 4):
            for xx in range(left+12, right-12, 4):
                if rng.random() < .62:
                    surface.plane(3 if (xx//4 + yy//4) % 3 else 4,
                                  (xx, yy), (xx+1, yy), (xx+1, yy+1))
                if rng.random() < .52:
                    surface.plane(1, (xx+2, yy+1), (xx+2, yy+2), (xx+3, yy+2))
    # Folded lower edge and sparse stitch marks identify a sewn textile edge.
    surface.plane(0, (left+9, hem-3), (right-10, hem-4),
                  (right-10, hem-2), (left+9, hem-1))
    for sx in range(left+13, right-12, 6):
        surface.plane(4, (sx, hem-3), (sx+2, hem-3), (sx+2, hem-2), (sx, hem-2))


def _wood(surface):
    rng = surface.rng
    y = -2
    while y < 48:
        h = rng.randint(9, 16)
        tone = rng.choice((2, 2, 3))
        surface.plane(tone, (-1, y), (65, y), (65, y + h - 1), (-1, y + h - 1))
        surface.plane(tone - 1, (-1, y + h - 1), (65, y + h - 1), (65, y + h), (-1, y + h))
        knot = rng.randint(9, 53)
        center = y + h // 2
        surface.plane(tone - 1, (-1, center - 1), (knot - 9, center), (knot, center - 3), (knot + 5, center - 1),
                      (knot + 14, center + 1), (65, center), (65, center + 1), (knot + 18, center + 2),
                      (knot + 7, center + 1), (knot, center + 2), (knot - 10, center + 1))
        if surface.detail:
            surface.plane(tone - 2, (knot - 4, center), (knot, center - 1), (knot + 3, center), (knot, center + 1))
            surface.plane(tone + 1, (knot - 21, center + 3), (knot - 9, center + 2), (knot - 2, center + 4),
                          (knot + 10, center + 3), (knot + 2, center + 5), (knot - 10, center + 3))
        y += h


def _roof(surface):
    rng = surface.rng
    offset = rng.randint(0, 7)
    for row, y in enumerate(range(46, -10, -8)):
        x = -12 + (row % 2) * 7 + offset
        while x < 64:
            w = rng.randint(10, 16)
            sa = rng.randint(-1, 1)
            tone = rng.choice((2, 2, 3))
            surface.plane(0, (x, y), (x + w - 1, y), (x + w, y + 7), (x + w - 2, y + 10 + sa),
                          (x + 3, y + 10), (x, y + 8))
            surface.plane(tone, (x, y), (x + w - 1, y), (x + w - 1, y + 7), (x + w - 3, y + 9 + sa),
                          (x + 3, y + 9), (x, y + 7))
            surface.plane(tone + 1, (x + 2, y + 2), (x + 5, y + 2), (x + 6, y + 8), (x + 3, y + 8))
            x += w


_SURFACES = {
    "rock": _rock, "cobble": _cobble, "soil": _soil, "leaves": _leaves, "bark": _bark,
    "grass": _grass, "water": _water, "cloth": _cloth, "wood": _wood, "roof": _roof,
}


def draw_material(canvas, x, y, palette, op):
    """Paint a bounded material surface, optionally clipped to existing artwork."""
    kind = op.get("kind")
    kind = _ALIASES.get(kind, kind)
    if kind not in _SURFACES:
        raise ValueError(f"Unknown material: {kind!r}. Choose from {', '.join(sorted(MATERIALS))}")
    w, h = op.get("w", canvas.width - x), op.get("h", canvas.height - y)
    if type(w) is not int or type(h) is not int or w < 1 or h < 1:
        raise ValueError("material w and h must be positive integers")
    inside = op.get("inside", op.get("clip", canvas.clip_to_opaque))
    if type(inside) is not bool:
        raise ValueError("material inside must be a boolean")
    colors = op.get("colors", _RAMPS[kind])
    if "colors" in op and "color" in op:
        raise ValueError("material accepts colors or color separately")
    if "color" in op:
        color = parse_color(op["color"], palette)
        ramp = (darken(color, .66), darken(color, .84), color, brighten(color, 1.13), brighten(color, 1.28))
    else:
        if not isinstance(colors, (list, tuple)) or len(colors) != 5:
            raise ValueError("material colors must contain five colors from shadow to highlight")
        ramp = tuple(parse_color(color, palette) for color in colors)
    if any(color[3] == 0 for color in ramp):
        raise ValueError("material colors must have nonzero alpha")
    base_tone = 0 if kind == "cobble" else 2
    material = Canvas(w, h, ramp[base_tone])
    _SURFACES[kind](_Surface(material, ramp, op.get("seed", 42)))
    if inside:
        for py in range(max(0, -y), min(h, canvas.height - y)):
            for px in range(max(0, -x), min(w, canvas.width - x)):
                target = (py + y) * canvas.width + px + x
                existing = canvas.pixels[target]
                if existing[3] and target not in canvas.no_outline:
                    color = material.get_pixel(px, py)
                    canvas.set_pixel(x + px, y + py, (*color[:3], existing[3]))
    else:
        canvas.blit(material, x, y)
