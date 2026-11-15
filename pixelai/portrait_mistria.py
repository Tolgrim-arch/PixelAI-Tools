"""Cozy 90s-anime / Fields of Mistria style pixel-art character portrait generator.

Renders clean, proportional waist-up or chest-up portraits with smooth jawlines,
clean chin shadows (zero neck scratch marks), large anime eyes with specular
catchlights, voluminous layered hair bangs, and hue-shifted cel planes.
"""

from __future__ import annotations

from typing import Any

from pixelai.canvas import Canvas
from pixelai.color import RGBA, TRANSPARENT, brighten, darken, parse_color


def _fill_tapered_polygon(
    canvas: Canvas,
    pts: list[tuple[float, float]],
    color: RGBA,
) -> None:
    canvas.draw_polygon([(round(x), round(y)) for x, y in pts], color, filled=True)


def _draw_anime_eye(
    canvas: Canvas,
    cx: int,
    cy: int,
    ew: int,
    eh: int,
    iris_col: RGBA,
    lash_col: RGBA,
    sclera_col: RGBA,
    skin_d: RGBA,
    iris_dir: int = 1,
) -> None:
    """Draw a high-craft pixel-art anime eye with curved upper lash, shaded iris, and catchlights."""
    x0 = cx - ew // 2
    y0 = cy - eh // 2
    # Sclera core
    canvas.draw_rect(x0, y0 + 1, ew, max(2, eh - 1), sclera_col, filled=True)
    # Soft upper-corner eyelid crease
    canvas.draw_line(x0, y0 - 1, x0 + ew - 1, y0 - 1, skin_d)
    # Curved dark upper eyelash arch (2px center, winged outer tip)
    canvas.draw_line(x0 - 1, y0 + 1, x0 + ew, y0 + 1, lash_col)
    canvas.draw_line(x0, y0, x0 + ew - 1, y0, lash_col)

    # Colored iris with deep upper pupil and vibrant lower rim
    iw = max(3, ew - 2)
    ih = max(3, eh - 1)
    ix = cx - iw // 2 + iris_dir
    ix = max(x0, min(x0 + ew - iw, ix))
    iy = y0 + 1
    iris_d = darken(iris_col, 0.62)
    iris_l = brighten(iris_col, 1.38)
    canvas.draw_rect(ix, iy, iw, ih, iris_col, filled=True)
    canvas.draw_rect(ix, iy, iw, max(1, ih // 2), iris_d, filled=True)
    canvas.draw_rect(ix + 1, iy + ih - 1, max(1, iw - 2), 1, iris_l, filled=True)

    # Pure white catchlight (top-left of iris) + subtle pinpoint sparkle
    glint = (255, 255, 255, 255)
    canvas.set_pixel(ix, iy + 1, glint)
    if iw >= 4:
        canvas.set_pixel(ix + 1, iy + 1, glint)
        canvas.set_pixel(ix, iy + 2, glint)
    canvas.set_pixel(ix + iw - 1, iy + ih - 2, glint)

    # Subtle lower rim anchor
    canvas.set_pixel(cx, y0 + eh, skin_d)


def draw_mistria_portrait(
    canvas: Canvas,
    x: int,
    y: int,
    palette: dict[str, RGBA],
    op: dict[str, Any],
) -> None:
    """Render a clean 90s-anime / cozy RPG bust portrait into `canvas`."""
    w = max(48, int(op.get("width", canvas.width - x)))
    h = max(64, int(op.get("height", canvas.height - y)))
    local = Canvas(w, h)

    preset = str(op.get("preset", "villager")).lower()
    face_dir = str(op.get("face_dir", op.get("dir", "three_quarter_right"))).lower()
    flip_left = face_dir in ("left", "three_quarter_left", "3q_left")
    expression = str(op.get("expression", "smile")).lower()
    gesture = str(op.get("gesture", "idle")).lower()
    has_hat = bool(op.get("hat", preset == "farmer"))
    has_scar = bool(op.get("scar", False))
    has_beard = bool(op.get("beard", False))

    def col(key: str, default_key: str, fallback: str) -> RGBA:
        val = op.get(key)
        if val is not None:
            return parse_color(val, palette)
        if preset == "villager" and default_key in palette:
            return palette[default_key]
        return parse_color(fallback, palette)

    # Cohesive cozy palette defaults per preset (hue-shifted shadows)
    if preset == "samurai":
        skin = col("skin", "skin", "#f7cba8")
        skin_l = col("skin_l", "skin_l", "#ffe4cc")
        skin_d = col("skin_d", "skin_d", "#cf8c6e")
        hair = col("hair", "hair", "#2b3048")
        hair_l = col("hair_l", "hair_l", "#4e5c82")
        hair_d = col("hair_d", "hair_d", "#1b1d2e")
        shirt = col("shirt", "shirt", "#eef2f5")
        shirt_d = darken(shirt, 0.80)
        garment = col("garment", "garment", "#355c7d")
        garment_l = brighten(garment, 1.20)
        garment_d = col("garment_d", "garment_d", "#21364f")
        accent = col("accent", "accent", "#d64545")
        iris = col("eye_color", "eye_color", "#4c6b94")
        hat_col = col("hat_color", "wheat", "#d9a95b")
        hat_l = col("hat_light", "wheat_l", "#f5d793")
        hat_d = col("hat_dark", "soil", "#9e6b38")
    elif preset == "farmer":
        skin = col("skin", "skin", "#f5c49e")
        skin_l = col("skin_l", "skin_l", "#ffe1c4")
        skin_d = col("skin_d", "skin_d", "#cc8867")
        hair = col("hair", "hair", "#7a4430")
        hair_l = col("hair_l", "hair_l", "#ad6746")
        hair_d = col("hair_d", "hair_d", "#4f281f")
        shirt = col("shirt", "shirt", "#ece4d3")
        shirt_d = darken(shirt, 0.80)
        garment = col("garment", "garment", "#486b99")
        garment_l = brighten(garment, 1.22)
        garment_d = col("garment_d", "garment_d", "#2e4466")
        accent = col("accent", "accent", "#e3aa42")
        iris = col("eye_color", "eye_color", "#4c7850")
        hat_col = col("hat_color", "wheat", "#e0b35a")
        hat_l = col("hat_light", "wheat_l", "#fae096")
        hat_d = col("hat_dark", "soil", "#a67537")
    else:
        skin = col("skin", "skin", "#f7caa6")
        skin_l = col("skin_l", "skin_l", "#ffe4cb")
        skin_d = col("skin_d", "skin_d", "#cf8c6e")
        hair = col("hair", "hair", "#6b3e37")
        hair_l = col("hair_l", "hair_l", "#995c4b")
        hair_d = col("hair_d", "hair_d", "#422325")
        shirt = col("shirt", "shirt", "#f2ece1")
        shirt_d = darken(shirt, 0.82)
        garment = col("garment", "garment", "#4d8c80")
        garment_l = brighten(garment, 1.22)
        garment_d = col("garment_d", "garment_d", "#2e5957")
        accent = col("accent", "accent", "#e09f43")
        iris = col("eye_color", "eye_color", "#3e8275")
        hat_col = col("hat_color", "wheat", "#dfb056")
        hat_l = col("hat_light", "wheat_l", "#fae096")
        hat_d = col("hat_dark", "soil", "#a67338")

    ink = col("ink", "ink", "#261b24")
    sclera = (252, 246, 240, 255)
    blush = (min(255, skin[0] + 5), max(0, skin[1] - 58), max(0, skin[2] - 48), 255)
    mouth_col = (max(0, skin_d[0] - 24), max(0, skin_d[1] - 34), max(0, skin_d[2] - 28), 255)
    beard_col = col("beard_color", "hair_d", "#4f281f")

    if op.get("fill_background", False):
        bg = col("background", "bg", "#d7e6cf")
        local.mark_no_outline = True
        local.draw_rect(0, 0, w, h, bg, filled=True)
        local.mark_no_outline = False

    # Uniform scale anchored so square (96x96) and tall (120x160) portraits keep crisp head ratios
    s = min(w, h) / 96.0
    cx = w * 0.48
    head_cy = h * 0.36 if h > w * 1.15 else h * 0.40

    def gx(dx: float) -> float:
        return cx + dx * s

    def gy(dy: float) -> float:
        return head_cy + dy * s

    # --- 1. Back Hair Silhouette (behind shoulders and neck) ---
    _fill_tapered_polygon(local, [
        (gx(-24), gy(-10)),
        (gx(-16), gy(-27)),
        (gx(0), gy(-30)),
        (gx(17), gy(-26)),
        (gx(23), gy(-8)),
        (gx(22), gy(18)),
        (gx(14), gy(24)),
        (gx(-16), gy(24)),
        (gx(-23), gy(14)),
    ], hair_d)

    if preset == "samurai":
        # Swept high ponytail silhouette tucked behind right/back head
        _fill_tapered_polygon(local, [
            (gx(-20), gy(-18)),
            (gx(-32), gy(-22)),
            (gx(-38), gy(-10)),
            (gx(-34), gy(4)),
            (gx(-24), gy(8)),
            (gx(-16), gy(-4)),
        ], hair_d)
        _fill_tapered_polygon(local, [
            (gx(-22), gy(-16)),
            (gx(-31), gy(-18)),
            (gx(-34), gy(-8)),
            (gx(-28), gy(2)),
            (gx(-18), gy(-4)),
        ], hair)

    # --- 2. Broad, Cleanly Sloped Bust / Shoulders ---
    sh_top = gy(26)
    bot_y = h - 1
    _fill_tapered_polygon(local, [
        (gx(-33), bot_y),
        (gx(-32), gy(40)),
        (gx(-27), gy(31)),
        (gx(-12), sh_top),
        (gx(12), sh_top),
        (gx(27), gy(31)),
        (gx(33), gy(40)),
        (gx(34), bot_y),
    ], garment)
    # Shoulder sunlit bevel & side shading
    _fill_tapered_polygon(local, [
        (gx(-31), gy(40)),
        (gx(-27), gy(31)),
        (gx(-12), sh_top),
        (gx(-8), gy(30)),
        (gx(-22), gy(36)),
        (gx(-26), gy(46)),
    ], garment_l)
    _fill_tapered_polygon(local, [
        (gx(21), gy(32)),
        (gx(27), gy(31)),
        (gx(33), gy(40)),
        (gx(34), bot_y),
        (gx(24), bot_y),
        (gx(23), gy(44)),
    ], garment_d)

    # Inner Shirt V-Collar & Clean Garment Lapels (no scratch lines!)
    _fill_tapered_polygon(local, [
        (gx(-12), sh_top),
        (gx(12), sh_top),
        (gx(14), gy(36)),
        (gx(2), gy(47)),
        (gx(-13), gy(36)),
    ], shirt)
    _fill_tapered_polygon(local, [
        (gx(-11), gy(31)),
        (gx(-5), gy(38)),
        (gx(2), gy(44)),
        (gx(7), gy(37)),
        (gx(12), gy(30)),
        (gx(10), gy(39)),
        (gx(2), gy(48)),
        (gx(-9), gy(39)),
    ], shirt_d)
    # Crisp lapel folds & clasp/pocket accent
    _fill_tapered_polygon(local, [
        (gx(-14), sh_top),
        (gx(-8), gy(32)),
        (gx(-2), gy(47)),
        (gx(-10), gy(49)),
        (gx(-17), gy(35)),
    ], garment_d)
    _fill_tapered_polygon(local, [
        (gx(14), sh_top),
        (gx(17), gy(35)),
        (gx(11), gy(49)),
        (gx(3), gy(47)),
        (gx(8), gy(32)),
    ], garment_l if preset != "samurai" else garment_d)
    # Decorative sash / scarf / brass brooch
    _fill_tapered_polygon(local, [
        (gx(-18), gy(49)),
        (gx(18), gy(49)),
        (gx(16), gy(54)),
        (gx(-16), gy(54)),
    ], accent)
    local.draw_rect(round(gx(-2)), round(gy(46)), max(3, round(5 * s)), max(3, round(5 * s)), accent, filled=True, bevel=True)

    # Optional Wave Gesture (smooth, proportionate raised arm with rounded mitt hand)
    if gesture == "wave":
        _fill_tapered_polygon(local, [
            (gx(25), gy(34)),
            (gx(33), gy(26)),
            (gx(37), gy(10)),
            (gx(43), gy(12)),
            (gx(40), gy(32)),
            (gx(31), gy(45)),
        ], garment_l)
        _fill_tapered_polygon(local, [
            (gx(36), gy(11)),
            (gx(36), gy(3)),
            (gx(41), gy(0)),
            (gx(45), gy(4)),
            (gx(44), gy(12)),
        ], skin)
        # Cute thumb tucked neatly against palm
        _fill_tapered_polygon(local, [
            (gx(34), gy(8)),
            (gx(36), gy(5)),
            (gx(38), gy(10)),
            (gx(36), gy(12)),
        ], skin_l)

    # --- 3. Slender Neck + Clean Chin Cast Shadow (Zero Scratch Marks) ---
    _fill_tapered_polygon(local, [
        (gx(-7), gy(16)),
        (gx(7), gy(16)),
        (gx(8), gy(31)),
        (gx(1), gy(35)),
        (gx(-8), gy(31)),
    ], skin)
    _fill_tapered_polygon(local, [
        (gx(-7), gy(16)),
        (gx(7), gy(16)),
        (gx(7), gy(24)),
        (gx(1), gy(27)),
        (gx(-7), gy(23)),
    ], skin_d)

    # --- 4. Smooth 3/4 Anime Head & Cheekbone/Ear Silhouette ---
    # Left ear tucked gently by temple
    _fill_tapered_polygon(local, [
        (gx(-21), gy(-2)),
        (gx(-16), gy(-4)),
        (gx(-15), gy(8)),
        (gx(-19), gy(9)),
        (gx(-22), gy(3)),
    ], skin)
    local.draw_ellipse(round(gx(-18)), round(gy(3)), max(1, round(1.5 * s)), max(2, round(2.5 * s)), skin_d, filled=True)

    # Main 3/4 jaw & face plane
    _fill_tapered_polygon(local, [
        (gx(-17), gy(-10)),
        (gx(-11), gy(-21)),
        (gx(6), gy(-22)),
        (gx(16), gy(-12)),
        (gx(17), gy(2)),
        (gx(14), gy(13)),
        (gx(5), gy(20)),
        (gx(-5), gy(19)),
        (gx(-15), gy(11)),
        (gx(-18), gy(0)),
    ], skin)
    # Soft sunlit cheek highlight & subtle left jaw shadow (clipped cleanly on skin)
    _fill_tapered_polygon(local, [
        (gx(-15), gy(-8)),
        (gx(-8), gy(-18)),
        (gx(3), gy(-18)),
        (gx(-4), gy(-10)),
        (gx(-9), gy(-2)),
    ], skin_l)
    _fill_tapered_polygon(local, [
        (gx(-16), gy(8)),
        (gx(-14), gy(12)),
        (gx(-5), gy(19)),
        (gx(5), gy(20)),
        (gx(4), gy(17)),
        (gx(-5), gy(16)),
        (gx(-13), gy(9)),
    ], skin_d)

    # --- 5. Crisp 90s-Anime Eyes, Brows, Blush, Nose & Mouth ---
    eye_y = round(gy(0))
    eye_w = max(5, round(6.5 * s))
    eye_h = max(5, round(6.5 * s))
    left_ex = round(gx(-5.5))
    right_ex = round(gx(9.5))

    _draw_anime_eye(local, left_ex, eye_y, eye_w, eye_h, iris, ink, sclera, skin_d, iris_dir=1)
    _draw_anime_eye(local, right_ex, eye_y, max(4, eye_w - 1), eye_h, iris, ink, sclera, skin_d, iris_dir=0)

    # Expressive Eyebrows
    brow_y = round(gy(-7))
    local.draw_line(left_ex - eye_w // 2, brow_y + 1, left_ex + eye_w // 2, brow_y, hair_d)
    local.draw_line(right_ex - eye_w // 2 + 1, brow_y, right_ex + eye_w // 2, brow_y + 1, hair_d)

    # Warm Cheek Blush
    local.draw_ellipse(round(gx(-8)), round(gy(6)), max(2, round(2.5 * s)), max(1, round(1.3 * s)), blush, filled=True)
    local.draw_ellipse(round(gx(11)), round(gy(6)), max(2, round(2.2 * s)), max(1, round(1.2 * s)), blush, filled=True)

    # Subtle 1px Nose Shade
    nx, ny = round(gx(3.5)), round(gy(5))
    local.set_pixel(nx, ny - 1, skin_d)
    local.set_pixel(nx + 1, ny, skin_d)
    local.set_pixel(nx, ny + 1, skin_d)
    local.set_pixel(nx - 1, ny + 1, skin_l)

    # Optional Cheek Scar
    if has_scar:
        sx0, sy0 = round(gx(-10)), round(gy(3))
        local.draw_line(sx0, sy0, sx0 + round(4 * s), sy0 + round(5 * s), skin_d)
        local.set_pixel(sx0 + 1, sy0, skin_l)

    # Optional Neat Cozy Beard (kept clean along jawline so mouth remains readable)
    if has_beard:
        _fill_tapered_polygon(local, [
            (gx(-13), gy(10)),
            (gx(-5), gy(15)),
            (gx(5), gy(15)),
            (gx(13), gy(11)),
            (gx(12), gy(16)),
            (gx(4), gy(22)),
            (gx(-4), gy(22)),
            (gx(-12), gy(16)),
        ], beard_col)

    # Mouth Expression
    mx, my = round(gx(2)), round(gy(12))
    mw = max(2, round(2.5 * s))
    if expression == "surprised":
        local.draw_ellipse(mx, my, max(1, mw // 2), max(1, round(1.5 * s)), mouth_col, filled=True)
    elif expression == "neutral":
        local.draw_line(mx - mw, my, mx + mw, my, mouth_col)
    else:
        local.draw_line(mx - mw, my - 1, mx - 1, my, mouth_col)
        local.draw_line(mx - 1, my, mx + mw - 1, my, mouth_col)
        local.set_pixel(mx + mw, my - 1, mouth_col)

    # --- 6. Voluminous Front Hair Crown, Specular Band & Swept Bangs ---
    # Crown hair mass
    _fill_tapered_polygon(local, [
        (gx(-21), gy(-6)),
        (gx(-19), gy(-19)),
        (gx(-8), gy(-27)),
        (gx(7), gy(-26)),
        (gx(19), gy(-18)),
        (gx(20), gy(-4)),
        (gx(15), gy(-8)),
        (gx(5), gy(-13)),
        (gx(-8), gy(-12)),
        (gx(-17), gy(-4)),
    ], hair)
    # Specular 90s-anime zig-zag hair halo across crown
    _fill_tapered_polygon(local, [
        (gx(-16), gy(-16)),
        (gx(-9), gy(-22)),
        (gx(3), gy(-21)),
        (gx(13), gy(-15)),
        (gx(10), gy(-12)),
        (gx(1), gy(-17)),
        (gx(-8), gy(-18)),
        (gx(-13), gy(-13)),
    ], hair_l)

    # Flowing Front Bangs (tapered organic strands framing eyes)
    _fill_tapered_polygon(local, [
        (gx(-17), gy(-13)),
        (gx(-11), gy(-12)),
        (gx(-10), gy(-2)),
        (gx(-15), gy(4)),
        (gx(-18), gy(-3)),
    ], hair)
    _fill_tapered_polygon(local, [
        (gx(-8), gy(-15)),
        (gx(-1), gy(-14)),
        (gx(-2), gy(-4)),
        (gx(-6), gy(-1)),
        (gx(-8), gy(-6)),
    ], hair)
    _fill_tapered_polygon(local, [
        (gx(1), gy(-15)),
        (gx(8), gy(-13)),
        (gx(6), gy(-2)),
        (gx(2), gy(-6)),
    ], hair)
    _fill_tapered_polygon(local, [
        (gx(12), gy(-14)),
        (gx(19), gy(-10)),
        (gx(20), gy(4)),
        (gx(16), gy(10)),
        (gx(14), gy(-1)),
    ], hair_d)
    # Cheek framing side locks
    _fill_tapered_polygon(local, [
        (gx(-22), gy(-2)),
        (gx(-17), gy(-4)),
        (gx(-15), gy(12)),
        (gx(-18), gy(20)),
        (gx(-23), gy(12)),
    ], hair_d)
    _fill_tapered_polygon(local, [
        (gx(-21), gy(0)),
        (gx(-18), gy(0)),
        (gx(-17), gy(13)),
        (gx(-20), gy(16)),
    ], hair)

    # --- 7. Optional Cozy Straw Hat or Samurai Kasa ---
    if has_hat:
        hat_y = gy(-22)
        if preset == "samurai":
            # Wide sloped bamboo jingasa cone
            _fill_tapered_polygon(local, [
                (gx(0), gy(-35)),
                (gx(32), gy(-17)),
                (gx(28), gy(-14)),
                (gx(0), gy(-22)),
                (gx(-28), gy(-14)),
                (gx(-32), gy(-17)),
            ], hat_col)
            _fill_tapered_polygon(local, [
                (gx(0), gy(-35)),
                (gx(-2), gy(-22)),
                (gx(-26), gy(-15)),
                (gx(-30), gy(-17)),
            ], hat_l)
            _fill_tapered_polygon(local, [
                (gx(4), gy(-32)),
                (gx(30), gy(-17)),
                (gx(26), gy(-14)),
                (gx(4), gy(-21)),
            ], hat_d)
        else:
            # Cozy farmer straw sunhat with crown, wide brim & ribbon
            _fill_tapered_polygon(local, [
                (gx(-15), hat_y + 4 * s),
                (gx(-12), hat_y - 10 * s),
                (gx(11), hat_y - 10 * s),
                (gx(15), hat_y + 4 * s),
            ], hat_col)
            _fill_tapered_polygon(local, [
                (gx(-12), hat_y - 10 * s),
                (gx(4), hat_y - 10 * s),
                (gx(0), hat_y - 3 * s),
                (gx(-13), hat_y - 2 * s),
            ], hat_l)
            _fill_tapered_polygon(local, [
                (gx(-15), hat_y),
                (gx(15), hat_y),
                (gx(15), hat_y + 4 * s),
                (gx(-15), hat_y + 4 * s),
            ], accent)
            _fill_tapered_polygon(local, [
                (gx(-32), hat_y + 5 * s),
                (gx(-16), hat_y + 1 * s),
                (gx(16), hat_y + 1 * s),
                (gx(32), hat_y + 5 * s),
                (gx(26), hat_y + 9 * s),
                (gx(0), hat_y + 7 * s),
                (gx(-26), hat_y + 9 * s),
            ], hat_d)
            _fill_tapered_polygon(local, [
                (gx(-29), hat_y + 4 * s),
                (gx(-15), hat_y + 1 * s),
                (gx(14), hat_y + 1 * s),
                (gx(28), hat_y + 4 * s),
                (gx(0), hat_y + 5 * s),
            ], hat_col)

    canvas.blit(local, x, y, flip_x=flip_left)
