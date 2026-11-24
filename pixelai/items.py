"""Parametric pixel-art items, weapons, potions, chests, and RPG loot icons."""

from typing import Any
from pixelai.canvas import Canvas
from pixelai.color import ground_shadow_color, RGBA, brighten, darken, parse_color


def _sc(val: float, s: float) -> int:
    return max(1, int(round(val * s)))


def _draw_potion(
    local: Canvas,
    size: int,
    orientation: str,
    liquid: RGBA,
    glass: RGBA,
    cork: RGBA,
    fill_level: float,
    shine: bool,
    frame: int,
) -> None:
    import math

    s = size / 24.0
    liq_hi = brighten(liquid, 1.38)
    liq_l = brighten(liquid, 1.18)
    liq_d = darken(liquid, 0.72)
    liq_dd = darken(liquid, 0.48)
    glass_hi = (255, 250, 236, 255)
    glass_l = brighten(glass, 1.22)
    glass_d = darken(glass, 0.74)
    glass_dd = darken(glass, 0.52)
    cork_l = brighten(cork, 1.24)
    cork_d = darken(cork, 0.70)

    def px(u: float) -> int:
        return int(round(u * s))

    # Tilt geometry: diagonal puts cork top-left and bulb bottom-right (classic RPG icon angle)
    if orientation == "diagonal":
        bx, by = 12.6 * s, 14.2 * s
        br = 6.6 * s
        lx, ly, lz = 0.46, -0.62, 0.64  # top-right key light
        # Chunky tilted cork (top-left)
        for dy in range(-px(4), px(4) + 1):
            for dx in range(-px(4), px(4) + 1):
                x, y = px(6.2) + dx, px(6.2) + dy
                # Rotate into cork-local frame (45 deg)
                u = (dx + dy) * 0.7071 / max(1.0, s)
                v = (-dx + dy) * 0.7071 / max(1.0, s)
                if abs(u) <= 2.2 and abs(v) <= 2.3:
                    if u < -0.5 and v < 0.8:
                        c = cork_l
                    elif u > 0.8 or v > 1.2:
                        c = cork_d
                    else:
                        c = cork
                    local.set_pixel(x, y, c)
        # Flared glass neck collar
        for dy in range(-px(4), px(4) + 1):
            for dx in range(-px(4), px(4) + 1):
                x, y = px(8.4) + dx, px(8.4) + dy
                u = (dx + dy) * 0.7071 / max(1.0, s)
                v = (-dx + dy) * 0.7071 / max(1.0, s)
                if -1.1 <= u <= 1.2 and abs(v) <= 3.1:
                    local.set_pixel(x, y, glass_l if v < 0.2 else glass_d)
    else:
        bx, by = size * 0.5, 14.8 * s
        br = 6.6 * s
        lx, ly, lz = -0.46, -0.62, 0.64  # top-left key light
        cx = size // 2
        # Upright shaded cork
        local.draw_rect(cx - _sc(2, s), px(3), _sc(4, s), _sc(3, s), cork, filled=True)
        local.draw_rect(cx - _sc(2, s), px(3), _sc(2, s), _sc(2, s), cork_l, filled=True)
        local.draw_rect(cx + _sc(1, s), px(4), _sc(1, s), _sc(2, s), cork_d, filled=True)
        # Glass neck + flared collar
        local.draw_rect(cx - _sc(2.2, s), px(6), _sc(4.4, s), _sc(4, s), glass, filled=True)
        local.draw_rect(cx - _sc(3.2, s), px(5.5), _sc(6.4, s), _sc(1.8, s), glass_l, filled=True)
        local.draw_rect(cx + _sc(1, s), px(6.5), _sc(2, s), _sc(2.5, s), glass_d, filled=True)

    # Spherical normal-mapped flask bulb + curved liquid volume + specular crescent
    fill_clamped = max(0.18, min(0.95, fill_level))
    liq_top_y = (by + br) - (2.0 * br * 0.86 * fill_clamped)
    wave_phase = (frame % 4) * (math.pi * 0.5)

    for y in range(size):
        for x in range(size):
            nx = (x + 0.5 - bx) / max(1.0, br)
            ny = (y + 0.5 - by) / max(1.0, br)
            r2 = nx * nx + ny * ny
            if r2 > 1.0:
                continue
            r_norm = math.sqrt(r2)
            nz = math.sqrt(max(0.0, 1.0 - r2))
            ndotl = nx * lx + ny * ly + nz * lz

            # Inner liquid region (inset by 1px glass wall)
            meniscus_y = liq_top_y + math.sin(nx * 2.6 + wave_phase) * (0.45 * s)
            in_liquid = r_norm <= 0.84 and (y + 0.5) >= meniscus_y

            if in_liquid:
                # Meniscus bright lip at top of liquid
                if (y + 0.5) - meniscus_y <= max(1.1, 1.15 * s):
                    c = liq_hi if ndotl > 0.15 else liq_l
                else:
                    # 4-tone spherical liquid shading + subtle bottom caustic glow
                    caustic = 1.0 if (ny > 0.35 and abs(nx - lx * 0.4) < 0.38 and r_norm < 0.72) else 0.0
                    shade = ndotl + caustic * 0.22 - (ny * 0.18)
                    if shade > 0.42:
                        c = liq_l
                    elif shade > 0.08:
                        c = liquid
                    elif shade > -0.22:
                        c = liq_d
                    else:
                        c = liq_dd
                local.set_pixel(x, y, c)
            else:
                # Glass shell shading (cool rim darkening + bright upper-lit dome)
                if r_norm > 0.86:
                    c = glass_d if ndotl > -0.1 else glass_dd
                elif ndotl > 0.45:
                    c = glass_l
                elif ndotl > -0.1:
                    c = glass
                else:
                    c = glass_d
                local.set_pixel(x, y, c)

            # Curved specular crescent on upper-lit glass surface (over both glass and liquid)
            if shine and 0.40 <= r_norm <= 0.78 and ndotl > 0.76:
                local.set_pixel(x, y, glass_hi)
            elif shine and 0.35 <= r_norm <= 0.80 and ndotl > 0.66 and not in_liquid:
                local.set_pixel(x, y, glass_l)



def _draw_sword(
    local: Canvas,
    size: int,
    orientation: str,
    blade: RGBA,
    hilt: RGBA,
    shine: bool,
    frame: int,
) -> None:
    s = size / 24.0
    blade_l = brighten(blade, 1.25)
    blade_d = darken(blade, 0.72)
    hilt_d = darken(hilt, 0.75)

    def px(u: float) -> int:
        return int(round(u * s))

    if orientation == "diagonal":
        # Blade pointing top-right, hilt bottom-left
        local.draw_line(px(7), px(17), px(19), px(5), blade)
        local.draw_line(px(8), px(17), px(19), px(6), blade_d)
        local.draw_line(px(7), px(16), px(18), px(5), blade_l)
        # Crossguard & grip
        local.draw_line(px(5), px(13), px(11), px(19), hilt)
        local.draw_line(px(4), px(20), px(7), px(17), hilt_d)
        local.draw_circle(px(4), px(20), _sc(1, s), hilt, filled=True)
        if shine:
            t = (frame % 4) * 3
            local.set_pixel(px(10 + t), px(14 - t), (255, 255, 255, 255))
        return

    cx = size // 2
    hilt_l = brighten(hilt, 1.22)
    grip_col = darken(hilt, 0.52)
    # Sharp tapered medieval broadsword tip + double-beveled blade with fuller
    local.draw_polygon(
        [
            (cx, px(2)),
            (cx + _sc(1, s), px(4)),
            (cx + _sc(1.5, s), px(6)),
            (cx + _sc(1.5, s), px(15)),
            (cx - _sc(1.5, s), px(15)),
            (cx - _sc(1.5, s), px(6)),
            (cx - _sc(1, s), px(4)),
        ],
        blade,
        filled=True,
    )
    # Bright left cutting edge and dark right bevel
    local.draw_line(cx - _sc(1.5, s), px(6), cx - _sc(1.5, s), px(14), blade_l)
    local.draw_line(cx - _sc(1, s), px(4), cx, px(2), blade_l)
    local.draw_line(cx + _sc(1.5, s), px(6), cx + _sc(1.5, s), px(14), blade_d)
    # Central fuller groove
    local.draw_line(cx, px(6), cx, px(13), blade_d)
    # Winged crossguard with upturned finials
    local.draw_rect(cx - _sc(5, s), px(15), _sc(10, s), _sc(1.5, s), hilt, filled=True)
    local.draw_line(cx - _sc(5, s), px(15), cx + _sc(4, s), px(15), hilt_l)
    local.set_pixel(cx - _sc(5, s), px(14), hilt_l)
    local.set_pixel(cx + _sc(5, s), px(14), hilt)
    # Slender wrapped leather grip
    local.draw_rect(cx - _sc(0.8, s), px(17), _sc(1.6, s), _sc(3.5, s), grip_col, filled=True)
    local.set_pixel(cx, px(18), hilt_d)
    # Crisp diamond pommel
    local.draw_polygon(
        [(cx, px(20)), (cx + _sc(1.5, s), px(21)), (cx, px(22)), (cx - _sc(1.5, s), px(21))],
        hilt,
        filled=True,
    )
    local.set_pixel(cx, px(20), hilt_l)
    if shine:
        local.set_pixel(cx - _sc(1, s), px(5 + (frame % 4) * 2), (255, 255, 255, 255))


def _draw_chest(
    local: Canvas,
    size: int,
    wood: RGBA,
    trim: RGBA,
    state: str,
    shine: bool,
    frame: int,
) -> None:
    s = size / 24.0
    wood_d = darken(wood, 0.72)
    wood_l = brighten(wood, 1.15)
    trim_l = brighten(trim, 1.2)

    def px(u: float) -> int:
        return int(round(u * s))

    # Base box
    local.draw_rect(px(4), px(11), px(16), px(9), wood, filled=True, bevel=True)
    local.draw_rect(px(4), px(17), px(16), px(3), wood_d, filled=True)
    if state == "open":
        # Tilted open lid + recessed lid interior + trim
        local.draw_polygon([
            (px(4), px(10)), (px(5), px(5)), (px(19), px(5)), (px(20), px(10)),
        ], wood_l, filled=True)
        local.draw_rect(px(5), px(4), px(14), _sc(2, s), wood_d, filled=True)
        local.draw_rect(px(5), px(6), px(14), px(4), (66, 42, 34, 255), filled=True)
        local.draw_rect(px(6), px(4), _sc(2, s), px(6), trim, filled=True)
        local.draw_rect(px(16), px(4), _sc(2, s), px(6), trim, filled=True)
        # Box dark recessed rim & front gold rim
        local.draw_rect(px(4), px(10), px(16), _sc(1, s), trim, filled=True)
        local.draw_rect(px(5), px(10), px(14), px(2), (38, 24, 32, 255), filled=True)
        # Overflowing treasure mound: coins + bright highlight + ruby jewel
        local.draw_ellipse(px(12), px(11), px(5), px(2), trim, filled=True)
        local.draw_ellipse(px(11), px(10), px(4), _sc(1.5, s), trim_l, filled=True)
        local.draw_rect(px(13), px(9), _sc(2, s), _sc(2, s), (218, 68, 82, 255), filled=True)
        if shine and (frame % 2 == 0):
            local.set_pixel(px(9), px(9), (255, 255, 255, 255))
            local.set_pixel(px(14), px(8), (255, 255, 255, 255))
    else:
        local.draw_rect(px(4), px(7), px(16), px(5), wood_l, filled=True, bevel=True)
        local.draw_rect(px(4), px(11), px(16), px(1), trim, filled=True)
    # Metal straps & lock
    local.draw_rect(px(6), px(7 if state != "open" else 11), _sc(2, s), px(13 if state != "open" else 9), trim, filled=True)
    local.draw_rect(px(16), px(7 if state != "open" else 11), _sc(2, s), px(13 if state != "open" else 9), trim, filled=True)
    local.draw_rect(px(11), px(10 if state != "open" else 12), _sc(2, s), _sc(3, s), trim_l, filled=True)


def _draw_gem(local: Canvas, size: int, color: RGBA, shine: bool, frame: int) -> None:
    """Multi-faceted crystal gem with 5-tone hue-shifted facets and internal refraction glow."""
    s = size / 24.0
    cx, cy = size // 2, size // 2
    col_hi = brighten(color, 1.48)
    col_l = brighten(color, 1.24)
    col_d = darken(color, 0.72)
    col_dd = darken(color, 0.48)

    def px(u: float) -> int:
        return int(round(u * s))

    # Outer crystal silhouette
    outer = [
        (cx, cy - px(7.5)),
        (cx + px(6.2), cy - px(2.2)),
        (cx + px(4.4), cy + px(6.2)),
        (cx, cy + px(7.5)),
        (cx - px(4.4), cy + px(6.2)),
        (cx - px(6.2), cy - px(2.2)),
    ]
    local.draw_polygon(outer, color, filled=True)
    local.clip_to_opaque = True

    # 6 distinct planar facets (top-left light source)
    # Upper-left crown (brightest)
    local.draw_polygon([(cx, cy - px(7.5)), (cx - px(6.2), cy - px(2.2)), (cx - px(2.4), cy - px(1.5))], col_hi, filled=True)
    # Upper-right crown (light mid)
    local.draw_polygon([(cx, cy - px(7.5)), (cx + px(6.2), cy - px(2.2)), (cx + px(2.4), cy - px(1.5))], col_l, filled=True)
    # Center table facet
    local.draw_polygon([(cx, cy - px(4.5)), (cx + px(2.8), cy - px(1.0)), (cx, cy + px(3.0)), (cx - px(2.8), cy - px(1.0))], col_l, filled=True)
    # Lower-right deep shadow pavilion
    local.draw_polygon([(cx + px(6.2), cy - px(2.2)), (cx + px(4.4), cy + px(6.2)), (cx, cy + px(7.5)), (cx, cy + px(2.0))], col_dd, filled=True)
    # Lower-left mid-dark pavilion
    local.draw_polygon([(cx - px(6.2), cy - px(2.2)), (cx - px(4.4), cy + px(6.2)), (cx, cy + px(7.5)), (cx, cy + px(2.0))], col_d, filled=True)
    # Internal warm caustic bounce near bottom-left
    local.draw_polygon([(cx - px(3.2), cy + px(3.2)), (cx - px(0.5), cy + px(5.8)), (cx - px(1.2), cy + px(2.2))], col_l, filled=True)

    if shine:
        off = 1 if (frame % 4) in (1, 2) else 0
        local.set_pixel(cx - px(2) + off, cy - px(4), (255, 252, 240, 255))
        local.set_pixel(cx - px(3) + off, cy - px(3), (255, 252, 240, 255))
        local.set_pixel(cx - px(2) + off, cy - px(3), col_hi)
    local.clip_to_opaque = False


def _draw_shield(local: Canvas, size: int, primary: RGBA, trim: RGBA) -> None:
    """Convex 3D heater shield with beveled metallic rim and normal-shaded field."""
    import math

    s = size / 24.0
    cx = size // 2
    trim_l = brighten(trim, 1.28)
    trim_d = darken(trim, 0.68)
    pri_l = brighten(primary, 1.22)
    pri_d = darken(primary, 0.72)
    pri_dd = darken(primary, 0.50)

    def px(u: float) -> int:
        return int(round(u * s))

    pts = [(cx - px(6.5), px(4.5)), (cx + px(6.5), px(4.5)), (cx + px(6.5), px(12.5)), (cx, px(20.5)), (cx - px(6.5), px(12.5))]
    inner = [(cx - px(4.5), px(6.5)), (cx + px(4.5), px(6.5)), (cx + px(4.5), px(12.0)), (cx, px(17.5)), (cx - px(4.5), px(12.0))]

    # Render trim mask first, then shade bevels by position relative to top-left light
    mask_outer = Canvas(size, size)
    mask_outer.draw_polygon(pts, trim, filled=True)
    mask_inner = Canvas(size, size)
    mask_inner.draw_polygon(inner, primary, filled=True)

    for y in range(size):
        for x in range(size):
            if mask_inner.get_pixel(x, y)[3] > 0:
                nx = (x + 0.5 - cx) / max(1.0, 5.5 * s)
                ny = (y + 0.5 - 11.5 * s) / max(1.0, 7.0 * s)
                ndotl = -0.55 * nx - 0.55 * ny + 0.62 * math.sqrt(max(0.0, 1.0 - min(1.0, 0.5 * (nx * nx + ny * ny))))
                if ndotl > 0.62:
                    c = pri_l
                elif ndotl > 0.25:
                    c = primary
                elif ndotl > -0.05:
                    c = pri_d
                else:
                    c = pri_dd
                local.set_pixel(x, y, c)
            elif mask_outer.get_pixel(x, y)[3] > 0:
                # Metallic bevel rim: bright top-left, dark bottom-right
                diag = (x - cx) + (y - 11.5 * s)
                local.set_pixel(x, y, trim_l if diag < -1.5 * s else (trim_d if diag > 2.0 * s else trim))

    # Raised metallic center crest
    local.draw_rect(cx - _sc(1, s), px(7.5), _sc(2, s), px(7.5), trim_l, filled=True)
    local.draw_rect(cx, px(8.5), _sc(1, s), px(6.5), trim_d, filled=True)


def _draw_key(local: Canvas, size: int, orientation: str, color: RGBA) -> None:
    s = size / 24.0
    col_l = brighten(color, 1.2)
    col_d = darken(color, 0.75)

    def px(u: float) -> int:
        return int(round(u * s))

    if orientation == "diagonal":
        local.draw_circle(px(8), px(16), _sc(3.5, s), color, filled=True)
        local.draw_circle(px(8), px(16), _sc(1.5, s), col_d, filled=True)
        local.draw_line(px(10), px(14), px(18), px(6), col_l)
        local.draw_line(px(11), px(14), px(19), px(6), color)
        local.draw_rect(px(16), px(8), _sc(2, s), _sc(2, s), col_d, filled=True)
        return

    cx = size // 2
    local.draw_circle(cx, px(7), _sc(3.5, s), col_l, filled=True)
    local.draw_circle(cx, px(7), _sc(1.5, s), col_d, filled=True)
    local.draw_rect(cx - _sc(1, s), px(10), _sc(2, s), px(9), color, filled=True)
    local.draw_rect(cx + _sc(1, s), px(15), _sc(3, s), _sc(1.5, s), col_d, filled=True)
    local.draw_rect(cx + _sc(1, s), px(18), _sc(2, s), _sc(1.5, s), col_d, filled=True)


def _draw_coin_or_apple(local: Canvas, size: int, kind: str, color: RGBA, stem: RGBA, shine: bool, frame: int) -> None:
    import math

    s = size / 24.0
    cx, cy = size // 2, size // 2
    col_hi = brighten(color, 1.45)
    col_l = brighten(color, 1.20)
    col_d = darken(color, 0.72)
    col_dd = darken(color, 0.48)

    def px(u: float) -> int:
        return int(round(u * s))

    if kind == "coin":
        rx = max(2, _sc(5.5, s) - (2 if (frame % 4) in (1, 3) else 0))
        ry = _sc(6.5, s)
        for y in range(size):
            for x in range(size):
                nx = (x + 0.5 - cx) / max(1.0, float(rx))
                ny = (y + 0.5 - cy) / max(1.0, float(ry))
                r2 = nx * nx + ny * ny
                if r2 > 1.0:
                    continue
                r = math.sqrt(r2)
                ndotl = -0.55 * nx - 0.65 * ny + 0.52 * math.sqrt(max(0.0, 1.0 - r2))
                if r > 0.78:
                    c = col_l if ndotl > 0.3 else col_d
                elif ndotl > 0.68:
                    c = col_hi
                elif ndotl > 0.30:
                    c = col_l
                elif ndotl > -0.05:
                    c = color
                else:
                    c = col_d
                local.set_pixel(x, y, c)
        if rx >= 3:
            local.draw_rect(cx - max(1, rx // 4), cy - _sc(2.5, s), max(1, rx // 2), _sc(5, s), col_d, filled=True)
            local.draw_rect(cx - max(1, rx // 4), cy - _sc(2.5, s), 1, _sc(4, s), col_hi, filled=True)
        return

    # 3D bilobed spherical normal-mapped Apple
    apple_mask = Canvas(size, size)
    apple_mask.draw_polygon([
        (px(6), px(8)), (px(9), px(6)), (px(12), px(7.5)),
        (px(15), px(6)), (px(18), px(8)), (px(19), px(12.5)),
        (px(17), px(17.5)), (px(14), px(19.5)), (px(12), px(18.5)),
        (px(10), px(19.5)), (px(7), px(17.5)), (px(5), px(12.5)),
    ], color, filled=True)

    for y in range(size):
        for x in range(size):
            if apple_mask.get_pixel(x, y)[3] == 0:
                continue
            nx = (x + 0.5 - cx) / max(1.0, 7.2 * s)
            ny = (y + 0.5 - 12.8 * s) / max(1.0, 6.8 * s)
            r2 = min(0.99, nx * nx + ny * ny)
            nz = math.sqrt(max(0.0, 1.0 - r2))
            ndotl = -0.52 * nx - 0.64 * ny + 0.56 * nz
            # Subtle bottom-right bounce light
            bounce = 0.18 if (ny > 0.45 and nx > 0.15) else 0.0
            shade = ndotl + bounce
            if shine and 0.25 <= math.sqrt(r2) <= 0.72 and ndotl > 0.78:
                c = (255, 248, 232, 255)
            elif shade > 0.52:
                c = col_l
            elif shade > 0.18:
                c = color
            elif shade > -0.12:
                c = col_d
            else:
                c = col_dd
            local.set_pixel(x, y, c)

    # Shaded stem and curved leaf
    local.draw_rect(cx, cy - px(6.5), _sc(1, s), _sc(3, s), stem, filled=True)
    local.set_pixel(cx, cy - px(6.5), brighten(stem, 1.25))
    leaf = parse_color("grass", {"grass": (92, 168, 76, 255)})
    local.draw_polygon([(cx + _sc(1, s), cy - px(5.5)), (cx + _sc(4, s), cy - px(6.5)), (cx + _sc(3, s), cy - px(3.5))], leaf, filled=True)
    local.set_pixel(cx + _sc(2, s), cy - px(5.5), brighten(leaf, 1.25))


def _draw_tool_or_food(local: Canvas, size: int, kind: str, color: RGBA, secondary: RGBA, shine: bool) -> None:
    """Native-resolution silhouettes: forged heads, tapered produce and organic food."""
    def point(x: float, y: float) -> tuple[int, int]:
        return round(x * size / 24), round(y * size / 24)

    def polygon(points: list[tuple[float, float]], fill: RGBA) -> None:
        local.draw_polygon([point(x, y) for x, y in points], fill, filled=True)

    def line(a: tuple[float, float], b: tuple[float, float], fill: RGBA) -> None:
        local.draw_line(*point(*a), *point(*b), fill)

    light, shade = brighten(color, 1.25), darken(color, .76)
    if kind in ("axe", "pickaxe"):
        polygon([(11, 7), (13, 7), (13, 21), (11, 21)], secondary)
        line((11, 10), (11, 20), brighten(secondary, 1.22))
        for y in (13, 16, 19):
            line((12, y), (13, y + .5), darken(secondary, .8))
        if kind == "axe":
            polygon([(7, 4), (13, 5), (15, 8), (12, 12), (6, 12), (4, 10), (4, 6)], color)
            polygon([(4, 6), (6, 5), (6, 11), (4, 10)], light)
            polygon([(7, 10), (12, 9), (14, 7), (12, 12), (6, 12)], shade)
        else:
            polygon([(3, 10), (6, 5), (11, 3), (16, 4), (21, 8), (17, 6), (12, 6), (7, 7)], color)
            line((6, 5), (11, 3), light)
            line((12, 4), (17, 5), light)
            line((6, 7), (3, 10), shade)
    elif kind == "carrot":
        polygon([(8, 8), (14, 7), (17, 10), (14, 15), (8, 21), (7, 18), (6, 12)], color)
        polygon([(13, 10), (17, 10), (14, 15), (8, 21), (10, 16)], shade)
        line((8, 10), (7, 15), light)
        for a, b in (((8, 12), (10, 13)), ((11, 15), (13, 15)), ((8, 17), (9, 18))):
            line(a, b, shade)
        polygon([(11, 8), (8, 3), (9, 2), (12, 6), (13, 1), (15, 2), (14, 6), (19, 3), (19, 5), (14, 9)], secondary)
        line((13, 3), (12, 7), brighten(secondary, 1.25))
    elif kind == "bread":
        polygon([(3, 13), (5, 8), (9, 5), (15, 4), (19, 6), (21, 11), (20, 16), (15, 19), (8, 20), (4, 18)], color)
        polygon([(3, 14), (7, 17), (15, 16), (20, 12), (20, 16), (15, 19), (8, 20), (4, 18)], shade)
        for x, y in ((7, 9), (11, 7), (15, 6)):
            polygon([(x, y), (x + 1, y), (x + 3, y + 5), (x + 2, y + 6)], secondary)
            line((x, y), (x + 2, y + 4), light)
    else:  # Fish: separate caudal fin, dorsal fin, belly plane, gill and eye.
        polygon([(6, 10), (3, 6), (2, 7), (3, 12), (2, 17), (4, 18), (7, 14)], secondary)
        polygon([(10, 7), (11, 4), (15, 7), (16, 9)], secondary)
        polygon([(6, 10), (10, 7), (15, 7), (20, 10), (22, 12), (19, 15), (14, 17), (9, 16), (6, 14)], color)
        polygon([(7, 13), (13, 14), (20, 12), (19, 15), (14, 17), (9, 16)], light)
        polygon([(10, 15), (12, 19), (15, 16)], secondary)
        line((17, 10), (16, 13), shade)
        local.set_pixel(*point(19, 10), (30, 38, 54, 255))
        if shine:
            line((10, 9), (14, 9), brighten(color, 1.55))
            for x, y in ((10, 12), (13, 11), (13, 13)):
                local.set_pixel(*point(x, y), light)


def _draw_lantern(local: Canvas, size: int, metal: RGBA, glass: RGBA,
                  flame: RGBA, shine: bool, frame: int) -> None:
    """Draw a fitted fantasy lantern with handle, glass chamber and living flame."""
    def point(x: float, y: float) -> tuple[int, int]:
        return round(x * size / 24), round(y * size / 24)

    def polygon(points, color):
        local.draw_polygon([point(x, y) for x, y in points], color, filled=True)

    metal_l, metal_d = brighten(metal, 1.28), darken(metal, .72)
    glass_l, glass_d = brighten(glass, 1.25), darken(glass, .66)
    flame_l, flame_d = brighten(flame, 1.35), darken(flame, .76)
    polygon([(9, 6), (9, 4), (10.5, 2.5), (13.5, 2.5), (15, 4), (15, 7),
             (13.5, 7), (13.5, 4.5), (13, 4), (11, 4), (10.5, 5), (10.5, 6)], metal_d)
    polygon([(9.5, 4), (11, 2.5), (13.5, 2.5), (14, 3.5), (11.25, 3), (10, 4.5)], metal_l)
    polygon([(8.5, 6), (15, 6), (18, 9), (17, 10.5), (7, 10.5), (6, 9)], metal)
    polygon([(8.5, 6), (15, 6), (17, 8.75), (13.5, 8.25), (11.5, 7), (9, 7), (7, 9), (6, 9)], metal_l)
    polygon([(7.5, 10), (16.5, 10), (16.5, 16), (14.5, 19), (9.5, 19), (7.5, 16.5)], glass)
    polygon([(8.5, 11), (15.5, 11), (15.5, 16), (13.5, 18), (10, 18), (8.5, 16)], glass_d)
    polygon([(9, 11), (14.5, 11), (13.5, 14), (13.5, 17), (12, 18), (10, 16.5), (9, 15)], glass_l)
    polygon([(7, 10), (8.5, 10), (8.5, 16), (10, 18.5), (9.5, 19.5), (7.5, 17), (7, 16)], metal_l)
    polygon([(15.5, 10), (17, 10), (17, 16), (15, 19), (14, 19), (15.5, 16)], metal_d)
    sway = (-.6, .2, .8, -.1)[frame % 4]
    polygon([(11, 17), (10, 14.5), (10.7, 13.2), (11.7, 14),
             (13.2 + sway, 11.8), (13.7, 14.5), (13, 16.5), (12, 17.5)], flame_d)
    polygon([(11.4, 16.5), (11, 14.6), (11.6, 13.7), (12.2 + sway / 2, 14.5),
             (13, 13.1), (13, 15.2), (12.2, 16.8)], flame)
    if shine:
        polygon([(11.7, 15.7), (11.9, 14.8), (12.5, 14), (12.4, 15.5)], flame_l)
        local.set_pixel(*point(9.3, 12), brighten(glass_l, 1.2))
    polygon([(9.5, 18), (14.5, 18), (17, 19.5), (15.5, 21), (8, 21), (7, 19.5)], metal_d)
    polygon([(9.5, 18), (14, 18), (15, 18.6), (9.5, 19), (8, 20), (7.5, 19.5)], metal_l)


def draw_item_rig(
    canvas: Canvas,
    x: int,
    y: int,
    palette: dict[str, RGBA],
    op: dict[str, Any],
    frame_idx: int = 0,
    total_frames: int = 1,
) -> None:
    """Render a parametric RPG item/loot icon with optional orientation and world shadow."""
    _ = total_frames
    kind = str(op.get("kind", op.get("item", "potion"))).lower()
    orientation = str(op.get("orientation", "vertical")).lower()
    size = max(16, int(op.get("size", 24)))
    shine = bool(op.get("shine", True))
    draw_shadow = bool(op.get("shadow", False))
    frame = int(op.get("frame", frame_idx))

    local = Canvas(size, size)

    if draw_shadow:
        sh_col = ground_shadow_color(parse_color(op.get("shadow_color", "shadow" if "shadow" in palette else "#33293a"), palette))
        local.mark_shadow = True
        local.mark_no_outline = True
        local.draw_ellipse(size // 2, size - max(2, size // 10), max(3, size // 4), max(1, size // 12), sh_col, filled=True)
        local.mark_shadow = False
        local.mark_no_outline = False

    def col(key: str, default_pal: str, fallback_hex: str) -> RGBA:
        return parse_color(op.get(key, default_pal if default_pal in palette else fallback_hex), palette)

    if kind == "potion":
        glass_key = "secondary_color" if "secondary_color" in op else ("glass_color" if "glass_color" in op else "secondary_color")
        _draw_potion(
            local,
            size,
            orientation,
            col("color", "roof", "#c24b38"),
            col(glass_key, "water_l", "#b4e3f2"),
            col("cork_color", "wood", "#9c603c"),
            float(op.get("fill_level", 0.78)),
            shine,
            frame,
        )
    elif kind == "sword":
        _draw_sword(local, size, orientation, col("color", "stone_l", "#c5d1e0"), col("secondary_color", "wheat", "#d99b38"), shine, frame)
    elif kind == "chest":
        _draw_chest(local, size, col("color", "wood", "#9c603c"), col("secondary_color", "wheat", "#e0ab43"), str(op.get("state", "closed")).lower(), shine, frame)
    elif kind == "gem":
        _draw_gem(local, size, col("color", "water", "#4fa4c4"), shine, frame)
    elif kind == "shield":
        _draw_shield(local, size, col("color", "water_d", "#326496"), col("secondary_color", "stone_l", "#c5d1e0"))
    elif kind == "key":
        _draw_key(local, size, orientation, col("color", "wheat", "#e0ab43"))
    elif kind in ("axe", "pickaxe", "carrot", "bread", "fish"):
        defaults = {"axe": ("stone_l", "wood", "#c5d1e0", "#9c603c"),
                    "pickaxe": ("stone_l", "wood", "#c5d1e0", "#9c603c"),
                    "carrot": ("#e98a31", "grass", "#e98a31", "#589c4c"),
                    "bread": ("wheat", "wheat_l", "#d99445", "#f2d287"),
                    "fish": ("water", "water_d", "#4fa4c4", "#326496")}
        primary, secondary, primary_fallback, secondary_fallback = defaults[kind]
        _draw_tool_or_food(local, size, kind, col("color", primary, primary_fallback),
                           col("secondary_color", secondary, secondary_fallback), shine)
    elif kind in ("coin", "apple"):
        _draw_coin_or_apple(local, size, kind, col("color", "wheat" if kind == "coin" else "roof", "#e0ab43"), col("secondary_color", "wood_d", "#6e422c"), shine, frame)
    elif kind == "lantern":
        _draw_lantern(local, size, col("color", "wood", "#946349"),
                      col("secondary_color", "water_d", "#3b7980"),
                      col("flame_color", "grass_l", "#a8edac"), shine, frame)

    else:
        raise ValueError(f"Unsupported item kind: {kind!r}; choose potion, sword, chest, gem, shield, key, coin, apple, axe, pickaxe, carrot, bread, fish, lantern")

    canvas.blit(local, x, y)
