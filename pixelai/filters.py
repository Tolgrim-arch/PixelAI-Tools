"""Post-processing filters for pixel art canvases."""

from copy import deepcopy

from pixelai.canvas import Canvas
from pixelai.color import (
    MATERIAL_PRESETS,
    RGBA,
    brighten,
    darken,
    lerp_rgba,
    luminance,
    parse_color,
)


def _copy_meta(src: Canvas, dst: Canvas) -> None:
    dst.clipped_pixels = src.clipped_pixels
    dst.warnings = src.warnings.copy()
    dst.attachments = deepcopy(src.attachments)


def _transform_attachment_points(value, factor: int = 1, dx: int = 0, dy: int = 0):
    """Transform coordinate pairs in runtime attachment metadata."""
    if isinstance(value, dict):
        return {key: _transform_attachment_points(item, factor, dx, dy) for key, item in value.items()}
    if isinstance(value, list):
        if len(value) == 2 and all(isinstance(item, int) for item in value):
            return [value[0] * factor + dx, value[1] * factor + dy]
        return [_transform_attachment_points(item, factor, dx, dy) for item in value]
    return value


def pad(canvas: Canvas, size: int = 1) -> Canvas:
    """Expand canvas by `size` transparent pixels on all four sides."""
    if size <= 0:
        return canvas
    out = Canvas(canvas.width + size * 2, canvas.height + size * 2)
    _copy_meta(canvas, out)
    out.attachments = _transform_attachment_points(out.attachments, dx=size, dy=size)
    out.blit(canvas, size, size)
    return out


def _blend_selout(neighbor: RGBA, base_ink: RGBA, amount: float) -> RGBA:
    r = int(neighbor[0] * (1.0 - amount) + base_ink[0] * amount)
    g = int(neighbor[1] * (1.0 - amount) + base_ink[1] * amount)
    b = int(neighbor[2] * (1.0 - amount) + base_ink[2] * amount)
    return (max(0, min(255, r)), max(0, min(255, g)), max(0, min(255, b)), 255)


def outline(
    canvas: Canvas,
    color: RGBA,
    selout: bool = False,
    selout_amount: float = 0.55,
    auto_pad: bool = False,
    directional_selout: bool = False,
    clean_jaggies: bool = False,
) -> Canvas:
    """Add a 1px outline (flat, selective, or light-directional) around opaque pixels."""
    if canvas.touches_border():
        if auto_pad:
            canvas = pad(canvas, 1)
        else:
            canvas.warnings.append(
                "Opaque pixels touch canvas border before 'outline'; "
                "1px outline was clipped at the edge (use larger canvas, y>=1, or auto_pad=true)."
            )

    out = canvas.copy()
    out.mark_no_outline = False
    out.mark_shadow = False
    out.clip_to_opaque = False
    outline_coords: set[tuple[int, int]] = set()

    for y in range(canvas.height):
        for x in range(canvas.width):
            idx = y * canvas.width + x
            # Outline can be drawn on transparent pixels OR over ground shadow / no_outline pixels
            if (
                canvas.pixels[idx][3] != 0
                and idx not in canvas.shadow_pixels
                and idx not in canvas.no_outline
            ):
                continue
            neighbors: list[tuple[int, int, RGBA]] = [
                (dx, dy, canvas.get_pixel(x + dx, y + dy))
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))
                if canvas.is_outline_source(x + dx, y + dy)
            ]
            if not neighbors:
                continue
            if selout or directional_selout:
                darkest = min((n[2] for n in neighbors), key=lambda c: c[0] + c[1] + c[2])
                amt = selout_amount
                if directional_selout:
                    # Top-left outline pixels face the light -> softer/warmer blend;
                    # bottom-right outline pixels sit in shadow -> deeper ink blend.
                    light_score = sum(dx + dy for dx, dy, _ in neighbors)
                    if light_score > 0:
                        amt = max(0.22, selout_amount * 0.58)
                    elif light_score < 0:
                        amt = min(0.92, selout_amount * 1.38)
                out.set_pixel(x, y, _blend_selout(darkest, color, amt))
            else:
                out.set_pixel(x, y, color)
            outline_coords.add((x, y))

    if clean_jaggies and outline_coords:
        # Thin redundant 4-connected L-corner staircase pixels when diagonal
        # outline neighbors already enclose the silhouette cleanly.
        to_remove: list[tuple[int, int]] = []
        for ox, oy in outline_coords:
            for dx, dy in ((1, 1), (1, -1), (-1, 1), (-1, -1)):
                if (
                    (ox + dx, oy) in outline_coords
                    and (ox, oy + dy) in outline_coords
                    and canvas.is_outline_source(ox + dx, oy + dy)
                    and not canvas.is_outline_source(ox - dx, oy - dy)
                    and not canvas.is_outline_source(ox + dx, oy)
                    and not canvas.is_outline_source(ox, oy + dy)
                ):
                    to_remove.append((ox, oy))
                    break
        for rx, ry in to_remove:
            orig_idx = ry * canvas.width + rx
            out.set_pixel(rx, ry, canvas.pixels[orig_idx])
    return out


def recolor_material(
    canvas: Canvas,
    material: str | list[str] | tuple[str, ...],
    target_colors: list[RGBA] | None = None,
    reflectance: str | None = None,
    recolor_outline: bool = True,
) -> Canvas:
    """Recolor a finished Canvas using a 5-tone physical material ramp and reflectance curve."""
    if isinstance(material, str):
        key = material.strip().lower()
        if key not in MATERIAL_PRESETS:
            avail = ", ".join(sorted(MATERIAL_PRESETS))
            raise ValueError(f"Unknown material preset {material!r}. Available: {avail}")
        preset = MATERIAL_PRESETS[key]
        ramp = [parse_color(c) for c in preset["ramp"]]  # type: ignore[index]
        eff_reflectance = reflectance or str(preset.get("reflectance", "matte_organic"))
        outline_col = parse_color(str(preset["outline"])) if "outline" in preset else None
    else:
        if len(material) < 2:
            raise ValueError("Custom material ramp requires at least 2 colors")
        ramp = [parse_color(c) for c in material]
        eff_reflectance = reflectance or "matte_organic"
        outline_col = None

    out = canvas.copy()
    target_set = set(target_colors) if target_colors else None

    # Collect interior surface pixels (exclude ground shadows, no_outline FX, and external 1px outline)
    surface_indices: list[int] = []
    outline_indices: list[int] = []
    for y in range(canvas.height):
        for x in range(canvas.width):
            idx = y * canvas.width + x
            px = canvas.pixels[idx]
            if px[3] == 0 or idx in canvas.shadow_pixels or idx in canvas.no_outline:
                continue
            if target_set is not None and px not in target_set:
                continue
            # Detect external 1px outline pixels (very dark pixels touching transparent/shadow border)
            touches_bg = any(
                not canvas.in_bounds(x + dx, y + dy)
                or canvas.pixels[(y + dy) * canvas.width + (x + dx)][3] == 0
                or ((y + dy) * canvas.width + (x + dx)) in canvas.shadow_pixels
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))
            )
            if touches_bg and luminance(px) < 70:
                outline_indices.append(idx)
            else:
                surface_indices.append(idx)

    if not surface_indices:
        return out

    lums = [luminance(canvas.pixels[i]) for i in surface_indices]
    min_l, max_l = min(lums), max(lums)
    span = max(1.0, max_l - min_l)
    n_tones = len(ramp)

    for idx in surface_indices:
        px = canvas.pixels[idx]
        t = (luminance(px) - min_l) / span
        if eff_reflectance == "metallic_specular":
            # High-contrast S-curve + sharp specular ridge at top
            if t >= 0.84:
                tone_pos = n_tones - 1
            elif t >= 0.60:
                tone_pos = n_tones - 2
            elif t >= 0.35:
                tone_pos = max(0, n_tones - 3)
            elif t >= 0.14:
                tone_pos = min(1, n_tones - 1)
            else:
                tone_pos = 0
            # Secondary bounce light on bottom-right edge of metallic forms
            x, y = idx % canvas.width, idx // canvas.width
            if tone_pos == 0 and x > canvas.width // 2 and y > canvas.height // 2:
                tone_pos = min(2, n_tones - 1)
        elif eff_reflectance == "crystalline":
            x, y = idx % canvas.width, idx // canvas.width
            if t >= 0.88:
                tone_pos = n_tones - 1
            elif x > canvas.width * 0.45 and y > canvas.height * 0.45 and t < 0.4:
                # Subsurface internal glow in lower-right core
                tone_pos = min(2, n_tones - 1)
            else:
                tone_pos = min(n_tones - 1, max(0, int(round(t * (n_tones - 1)))))
        else:
            tone_pos = min(n_tones - 1, max(0, int(round(t * (n_tones - 1)))))

        new_c = ramp[tone_pos]
        out.pixels[idx] = (new_c[0], new_c[1], new_c[2], px[3])

    if recolor_outline and outline_col is not None:
        for idx in outline_indices:
            px = canvas.pixels[idx]
            out.pixels[idx] = (outline_col[0], outline_col[1], outline_col[2], px[3])

    return out


def scale(canvas: Canvas, factor: int) -> Canvas:
    """Scale canvas by an integer factor using nearest-neighbor."""
    if factor < 1:
        raise ValueError(f"Scale factor must be >= 1, got {factor}")
    if factor == 1:
        return canvas
    out = Canvas(canvas.width * factor, canvas.height * factor)
    _copy_meta(canvas, out)
    out.attachments = _transform_attachment_points(out.attachments, factor=factor)
    for y in range(canvas.height):
        for x in range(canvas.width):
            c = canvas.get_pixel(x, y)
            if c[3] == 0:
                continue
            for sy in range(factor):
                for sx in range(factor):
                    out.set_pixel(x * factor + sx, y * factor + sy, c)
    return out


def _adjust(c: RGBA, factor: float) -> RGBA:
    r, g, b, a = c
    return (
        max(0, min(255, int(r * factor))),
        max(0, min(255, int(g * factor))),
        max(0, min(255, int(b * factor))),
        a,
    )


def shade(canvas: Canvas, amount: float = 0.25, hue_shift: bool = False) -> Canvas:
    """Apply top-left directional edge shading to non-transparent pixels."""
    out = Canvas(canvas.width, canvas.height)
    _copy_meta(canvas, out)
    for y in range(canvas.height):
        for x in range(canvas.width):
            c = canvas.get_pixel(x, y)
            if c[3] == 0:
                continue
            top_empty = canvas.get_pixel(x, y - 1)[3] == 0
            left_empty = canvas.get_pixel(x - 1, y)[3] == 0
            bottom_empty = canvas.get_pixel(x, y + 1)[3] == 0
            right_empty = canvas.get_pixel(x + 1, y)[3] == 0
            if top_empty or left_empty:
                c = brighten(c, 1.0 + amount) if hue_shift else _adjust(c, 1.0 + amount)
            elif bottom_empty or right_empty:
                c = darken(c, 1.0 - amount) if hue_shift else _adjust(c, 1.0 - amount)
            out.set_pixel(x, y, c)
    return out


def drop_shadow(
    canvas: Canvas, dx: int = 1, dy: int = 2, color: RGBA = (33, 24, 27, 96)
) -> Canvas:
    """Cast a silhouette drop shadow onto transparent background pixels."""
    out = Canvas(canvas.width, canvas.height)
    _copy_meta(canvas, out)
    for y in range(canvas.height):
        for x in range(canvas.width):
            if canvas.get_pixel(x, y)[3] > 0:
                out.set_pixel(x + dx, y + dy, color)
    for y in range(canvas.height):
        for x in range(canvas.width):
            c = canvas.get_pixel(x, y)
            if c[3] > 0:
                out.set_pixel(x, y, c)
    return out


def _rgb_dist2(a: RGBA, b: RGBA) -> int:
    dr = a[0] - b[0]
    dg = a[1] - b[1]
    db = a[2] - b[2]
    return dr * dr + dg * dg + db * db


def cleanup(canvas: Canvas, tol: float = 60.0, keep_lone: bool = False) -> Canvas:
    """Remove isolated 1px orphan pixels and smooth low-contrast stray pixels.

    Preserves intentional high-contrast 1px details (such as eyes or specular dots)
    whose RGB distance from the surrounding majority color exceeds `tol`.
    """
    out = canvas.copy()
    w, h = canvas.width, canvas.height
    tol2 = tol * tol

    for y in range(h):
        for x in range(w):
            idx = y * w + x
            c = canvas.pixels[idx]
            if c[3] == 0 or idx in canvas.shadow_pixels:
                continue
            n4 = [
                canvas.get_pixel(x - 1, y),
                canvas.get_pixel(x + 1, y),
                canvas.get_pixel(x, y - 1),
                canvas.get_pixel(x, y + 1),
            ]
            solid = [v for v in n4 if v[3] > 0]
            if not solid:
                if not keep_lone:
                    out.pixels[idx] = (0, 0, 0, 0)
                    out.no_outline.discard(idx)
                    out.shadow_pixels.discard(idx)
                continue
            n8_diag = [
                canvas.get_pixel(x - 1, y - 1),
                canvas.get_pixel(x + 1, y - 1),
                canvas.get_pixel(x - 1, y + 1),
                canvas.get_pixel(x + 1, y + 1),
            ]
            if c in n4 or c in n8_diag:
                continue
            votes: dict[RGBA, int] = {}
            for v in solid:
                votes[v] = votes.get(v, 0) + 1
            top = max(votes.items(), key=lambda item: item[1])[0]
            if _rgb_dist2(c, top) <= tol2:
                out.pixels[idx] = top
    return out


def pixel_perfect(canvas: Canvas) -> Canvas:
    """Remove redundant L-step corner pixels on 1px diagonal strokes and silhouettes."""
    out = canvas.copy()
    w, h = canvas.width, canvas.height

    def _opaque(px: int, py: int) -> bool:
        if px < 0 or py < 0 or px >= w or py >= h:
            return False
        i = py * w + px
        return out.pixels[i][3] > 0 and i not in out.shadow_pixels

    for y in range(h):
        for x in range(w):
            if not _opaque(x, y):
                continue
            l = 1 if _opaque(x - 1, y) else 0
            r = 1 if _opaque(x + 1, y) else 0
            u = 1 if _opaque(x, y - 1) else 0
            d = 1 if _opaque(x, y + 1) else 0
            if l + r != 1 or u + d != 1:
                continue
            sx = -1 if l else 1
            sy = -1 if u else 1
            if not _opaque(x + sx, y + sy) and not _opaque(x - sx, y) and not _opaque(x, y - sy):
                idx = y * w + x
                out.pixels[idx] = (0, 0, 0, 0)
                out.no_outline.discard(idx)
                out.shadow_pixels.discard(idx)
    return out


def rim_light(
    canvas: Canvas,
    ramp: list[RGBA] | None = None,
    direction: tuple[int, int] = (-1, -1),
    steps: int = 1,
) -> Canvas:
    """Brighten light-facing silhouette edge pixels before outlining/selout.

    When `ramp` is provided, pixels matching a color in `ramp` are shifted `steps`
    entries lighter along `ramp`. When `ramp` is omitted, light-facing edge pixels
    are hue-shifted brighter via `brighten()`.
    """
    out = canvas.copy()
    w, h = canvas.width, canvas.height
    dx, dy = int(direction[0]), int(direction[1])
    step_count = max(1, int(steps))

    def _solid(px: int, py: int) -> bool:
        if px < 0 or py < 0 or px >= w or py >= h:
            return False
        i = py * w + px
        return canvas.pixels[i][3] > 0 and i not in canvas.shadow_pixels and i not in canvas.no_outline

    ramp_index = {c: i for i, c in enumerate(ramp)} if ramp else None

    for y in range(h):
        for x in range(w):
            if not _solid(x, y):
                continue
            blocked_x = (dx == 0) or _solid(x + dx, y)
            blocked_y = (dy == 0) or _solid(x, y + dy)
            if blocked_x and blocked_y:
                continue
            idx = y * w + x
            c = canvas.pixels[idx]
            if ramp and ramp_index is not None:
                pos = ramp_index.get(c)
                if pos is not None:
                    out.pixels[idx] = ramp[min(len(ramp) - 1, pos + step_count)]
            else:
                lit = c
                for _ in range(step_count):
                    lit = brighten(lit, 1.14)
                out.pixels[idx] = lit
    return out

