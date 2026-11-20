"""Commercial-grade 4-direction farm animal rigs: pig and sheep (32x32 native)."""

from __future__ import annotations

from typing import Any

from pixelai.canvas import Canvas
from pixelai.color import RGBA, brighten, darken, ground_shadow_color, parse_color

_PIG_PALETTES: dict[str, dict[str, str]] = {
    "pink": {
        "body": "#f2a2a8", "body_l": "#ffc7cb", "body_d": "#c96f7b",
        "snout": "#e88492", "snout_l": "#ffb3bd", "snout_d": "#a84c5c",
        "hoof": "#5e3e44", "eye": "#24171d", "spot": "#c46c78",
    },
    "spotted": {
        "body": "#f5b8b8", "body_l": "#ffd9d9", "body_d": "#c9858c",
        "snout": "#e88b96", "snout_l": "#ffb8c0", "snout_d": "#a85362",
        "hoof": "#4a3338", "eye": "#24171d", "spot": "#6e4e54",
    },
    "boar": {
        "body": "#7d5545", "body_l": "#a6755d", "body_d": "#54362d",
        "snout": "#9e6b5e", "snout_l": "#c28e7e", "snout_d": "#6e443d",
        "hoof": "#362524", "eye": "#1f1417", "spot": "#4f322a",
    },
    "golden": {
        "body": "#f2be4b", "body_l": "#ffe680", "body_d": "#bd7d24",
        "snout": "#e39d34", "snout_l": "#ffd466", "snout_d": "#965817",
        "hoof": "#6e4016", "eye": "#24171d", "spot": "#d48e2a",
    },
}

_SHEEP_PALETTES: dict[str, dict[str, str]] = {
    "white": {
        "wool": "#f2ede4", "wool_l": "#ffffff", "wool_d": "#c2bdd1",
        "face": "#473b42", "face_l": "#695a63", "face_d": "#2e242b",
        "hoof": "#33282e", "eye": "#1a1217", "ear_in": "#d4989e",
    },
    "cream": {
        "wool": "#f0dfc2", "wool_l": "#fff5e0", "wool_d": "#bfa688",
        "face": "#59433b", "face_l": "#7d6156", "face_d": "#3b2a25",
        "hoof": "#3b2a25", "eye": "#1a1217", "ear_in": "#d99b96",
    },
    "black": {
        "wool": "#423e4d", "wool_l": "#625d73", "wool_d": "#282433",
        "face": "#29242e", "face_l": "#443d4d", "face_d": "#17141c",
        "hoof": "#17141c", "eye": "#f2d26b", "ear_in": "#7a5263",
    },
    "golden": {
        "wool": "#f5c851", "wool_l": "#fff099", "wool_d": "#c48a25",
        "face": "#5c3b28", "face_l": "#855a3e", "face_d": "#3b2318",
        "hoof": "#402618", "eye": "#1a1217", "ear_in": "#e8a866",
    },
}


def _resolve_pal(table: dict[str, dict[str, str]], variant: str) -> dict[str, RGBA]:
    key = variant.strip().lower()
    raw = table.get(key, next(iter(table.values())))
    return {k: parse_color(v) for k, v in raw.items()}


def _draw_shadow(local: Canvas, cx: int, cy: int, rx: int, ry: int, palette: dict[str, RGBA]) -> None:
    old_sh, old_no = local.mark_shadow, local.mark_no_outline
    local.mark_shadow = local.mark_no_outline = True
    sh_col = ground_shadow_color(palette.get("shadow", (48, 36, 56, 64)))
    local.draw_ellipse(cx, cy, rx, ry, sh_col, filled=True)
    local.mark_shadow, local.mark_no_outline = old_sh, old_no


def draw_pig(
    canvas: Canvas,
    x: int,
    y: int,
    palette: dict[str, RGBA],
    direction: str,
    pose: str,
    frame: int,
    op: dict[str, Any],
) -> None:
    """Render a 32x32 4-direction cozy pig with snout, flopping ears, curly tail, and walk/graze/sleep poses."""
    local = Canvas(32, 32)
    pal = _resolve_pal(_PIG_PALETTES, str(op.get("variant", "pink")))
    body, body_l, body_d = pal["body"], pal["body_l"], pal["body_d"]
    snout, snout_l, snout_d = pal["snout"], pal["snout_l"], pal["snout_d"]
    hoof, eye, spot = pal["hoof"], pal["eye"], pal["spot"]
    is_spotted = str(op.get("variant", "pink")).lower() == "spotted"

    f = frame % 4
    walking = pose in ("walk", "run")
    grazing = pose in ("graze", "peck", "eat")
    sleeping = pose in ("sleep", "lie", "nest")
    happy = pose in ("happy", "jump")

    bob = -1 if (walking and f % 2 == 1) else (-2 if (happy and f % 2 == 1) else 0)
    if sleeping:
        bob = 3
    stride = (-1, 0, 1, 0)[f] if walking else 0

    if op.get("shadow", True):
        sh_rx = 9 if direction in ("left", "right") else 7
        _draw_shadow(local, 16, 26, sh_rx, 2, palette)

    if direction in ("down", "up"):
        # Legs (4 trotters, back/front pair)
        if not sleeping:
            ly_l = 23 + (stride if f % 2 else 0)
            ly_r = 23 - (stride if f % 2 else 0)
            local.draw_rect(11, 20 + bob, 3, max(2, ly_l - (20 + bob)), body_d, filled=True)
            local.draw_rect(18, 20 + bob, 3, max(2, ly_r - (20 + bob)), body_d, filled=True)
            local.draw_rect(11, ly_l, 3, 2, hoof, filled=True)
            local.draw_rect(18, ly_r, 3, 2, hoof, filled=True)

        # Plump rounded torso
        local.draw_ellipse(16, 17 + bob, 7, 6, body_d, filled=True)
        local.draw_ellipse(16, 16 + bob, 7, 5, body, filled=True)
        local.draw_ellipse(15, 13 + bob, 5, 2, body_l, filled=True)
        if is_spotted:
            local.draw_ellipse(19, 15 + bob, 2, 2, spot, filled=True)

        if direction == "up":
            # Ears peeking at top + curly tail on rump
            local.draw_polygon([(10, 12 + bob), (12, 9 + bob), (14, 12 + bob)], body_d, filled=True)
            local.draw_polygon([(18, 12 + bob), (20, 9 + bob), (22, 12 + bob)], body_d, filled=True)
            # Curly tail spiral
            tx = 16 + (1 if f in (1, 2) else 0)
            local.set_pixel(tx, 18 + bob, snout_d)
            local.set_pixel(tx + 1, 17 + bob, snout)
            local.set_pixel(tx + 1, 16 + bob, snout_l)
            local.set_pixel(tx, 16 + bob, snout)
        else:
            # Front head + flopping ears + oval snout
            hy = 16 + bob + (2 if grazing and f % 2 == 1 else 0)
            local.draw_ellipse(16, hy, 6, 5, body, filled=True)
            local.draw_ellipse(15, hy - 3, 4, 2, body_l, filled=True)
            # Flopping ears
            local.draw_polygon([(9, hy - 2), (11, hy - 6), (13, hy - 3)], body, filled=True)
            local.set_pixel(11, hy - 4, snout)
            local.draw_polygon([(23, hy - 2), (21, hy - 6), (19, hy - 3)], body, filled=True)
            local.set_pixel(21, hy - 4, snout)
            # Eyes (closed when sleeping)
            if sleeping:
                local.draw_line(12, hy - 1, 13, hy - 1, eye)
                local.draw_line(19, hy - 1, 20, hy - 1, eye)
            else:
                local.set_pixel(13, hy - 1, eye)
                local.set_pixel(19, hy - 1, eye)
                local.set_pixel(13, hy - 2, (255, 255, 255, 255))
                local.set_pixel(19, hy - 2, (255, 255, 255, 255))
            # Oval pig snout with 2 nostrils
            local.draw_ellipse(16, hy + 2, 3, 2, snout, filled=True)
            local.draw_line(15, hy + 1, 17, hy + 1, snout_l)
            local.set_pixel(15, hy + 2, snout_d)
            local.set_pixel(17, hy + 2, snout_d)
    else:
        # Side view (drawn facing right, flipped if left)
        if not sleeping:
            # Far legs
            local.draw_rect(10 - stride, 21 + bob, 2, 3, body_d, filled=True)
            local.draw_rect(10 - stride, 24 + bob, 2, 2, hoof, filled=True)
            local.draw_rect(19 + stride, 21 + bob, 2, 3, body_d, filled=True)
            local.draw_rect(19 + stride, 24 + bob, 2, 2, hoof, filled=True)

        # Plump side torso
        local.draw_ellipse(15, 17 + bob, 8, 5, body_d, filled=True)
        local.draw_ellipse(15, 16 + bob, 8, 4, body, filled=True)
        local.draw_ellipse(14, 13 + bob, 5, 2, body_l, filled=True)
        if is_spotted:
            local.draw_ellipse(13, 15 + bob, 3, 2, spot, filled=True)

        # Curly tail on left rump
        ty = 15 + bob + (1 if f in (1, 2) else 0)
        local.set_pixel(6, ty, snout)
        local.set_pixel(5, ty - 1, snout_l)
        local.set_pixel(6, ty - 2, snout)
        local.set_pixel(7, ty - 1, snout_d)

        if not sleeping:
            # Near legs
            local.draw_rect(12 + stride, 21 + bob, 2, 3, body, filled=True)
            local.draw_rect(12 + stride, 24 + bob, 2, 2, hoof, filled=True)
            local.draw_rect(17 - stride, 21 + bob, 2, 3, body, filled=True)
            local.draw_rect(17 - stride, 24 + bob, 2, 2, hoof, filled=True)

        # Head + snout facing right
        hy = 15 + bob + (3 if grazing and f % 2 == 1 else 0)
        hx = 21 + (1 if grazing and f % 2 == 1 else 0)
        local.draw_ellipse(hx, hy, 4, 4, body, filled=True)
        local.draw_ellipse(hx - 1, hy - 2, 3, 1, body_l, filled=True)
        # Flopping ear
        local.draw_polygon([(hx - 3, hy - 2), (hx - 1, hy - 5), (hx + 1, hy - 3)], body, filled=True)
        local.set_pixel(hx - 1, hy - 3, snout)
        # Protruding flat snout
        local.draw_rect(hx + 3, hy, 3, 3, snout, filled=True)
        local.draw_line(hx + 3, hy, hx + 5, hy, snout_l)
        local.set_pixel(hx + 5, hy + 1, snout_d)
        # Eye
        if sleeping:
            local.draw_line(hx + 1, hy - 1, hx + 2, hy - 1, eye)
        else:
            local.set_pixel(hx + 2, hy - 1, eye)
            local.set_pixel(hx + 2, hy - 2, (255, 255, 255, 255))

        canvas.blit(local, x, y, flip_x=(direction == "left"))
        return

    canvas.blit(local, x, y)


def draw_sheep(
    canvas: Canvas,
    x: int,
    y: int,
    palette: dict[str, RGBA],
    direction: str,
    pose: str,
    frame: int,
    op: dict[str, Any],
) -> None:
    """Render a 32x32 4-direction fluffy sheep with layered cloud-wool clusters and dark face/hooves."""
    local = Canvas(32, 32)
    pal = _resolve_pal(_SHEEP_PALETTES, str(op.get("variant", "white")))
    wool, wool_l, wool_d = pal["wool"], pal["wool_l"], pal["wool_d"]
    face, face_l, face_d = pal["face"], pal["face_l"], pal["face_d"]
    hoof, eye, ear_in = pal["hoof"], pal["eye"], pal["ear_in"]

    f = frame % 4
    walking = pose in ("walk", "run")
    grazing = pose in ("graze", "peck", "eat")
    sleeping = pose in ("sleep", "lie", "nest")
    happy = pose in ("happy", "jump")

    bob = -1 if (walking and f % 2 == 1) else (-2 if (happy and f % 2 == 1) else 0)
    if sleeping:
        bob = 3
    stride = (-1, 0, 1, 0)[f] if walking else 0

    if op.get("shadow", True):
        sh_rx = 9 if direction in ("left", "right") else 7
        _draw_shadow(local, 16, 26, sh_rx, 2, palette)

    def _wool_puff(cx: int, cy: int, r: int) -> None:
        local.draw_circle(cx, cy + 1, r, wool_d, filled=True)
        local.draw_circle(cx, cy, r, wool, filled=True)
        if r >= 3:
            local.draw_circle(cx - 1, cy - 1, max(1, r - 2), wool_l, filled=True)

    if direction in ("down", "up"):
        # Layered fluffy wool clusters
        _wool_puff(12, 15 + bob, 4)
        _wool_puff(20, 15 + bob, 4)
        _wool_puff(16, 17 + bob, 5)
        _wool_puff(16, 12 + bob, 5)
        _wool_puff(13, 11 + bob, 3)
        _wool_puff(19, 11 + bob, 3)

        if not sleeping:
            ly_l = 23 + (stride if f % 2 else 0)
            ly_r = 23 - (stride if f % 2 else 0)
            local.draw_rect(12, 20 + bob, 2, max(3, ly_l - (20 + bob) + 2), hoof, filled=True)
            local.draw_rect(18, 20 + bob, 2, max(3, ly_r - (20 + bob) + 2), hoof, filled=True)

        if direction == "up":
            # Fluffy stubby tail on back
            _wool_puff(16, 18 + bob, 2)
        else:
            hy = 16 + bob + (2 if grazing and f % 2 == 1 else 0)
            # Drooping ears
            local.draw_ellipse(10, hy - 1, 2, 1, face_d, filled=True)
            local.draw_ellipse(22, hy - 1, 2, 1, face_d, filled=True)
            local.set_pixel(10, hy - 1, ear_in)
            local.set_pixel(22, hy - 1, ear_in)
            # Dark oval face
            local.draw_ellipse(16, hy + 1, 4, 4, face_d, filled=True)
            local.draw_ellipse(16, hy, 4, 3, face, filled=True)
            local.draw_line(14, hy - 1, 18, hy - 1, face_l)
            # Fluffy wool forelock tuft on top of head
            _wool_puff(16, hy - 4, 3)
            # Cute nose & expressive eyes
            local.set_pixel(16, hy + 2, ear_in)
            if sleeping:
                local.draw_line(13, hy, 14, hy, eye)
                local.draw_line(18, hy, 19, hy, eye)
            else:
                local.set_pixel(14, hy, (255, 255, 255, 255))
                local.set_pixel(18, hy, (255, 255, 255, 255))
                local.set_pixel(14, hy + 1, eye)
                local.set_pixel(18, hy + 1, eye)
    else:
        if not sleeping:
            local.draw_rect(10 - stride, 21 + bob, 2, 5, face_d, filled=True)
            local.draw_rect(19 + stride, 21 + bob, 2, 5, face_d, filled=True)

        # Layered side wool puffs (organic cloud silhouette)
        _wool_puff(10, 16 + bob, 4)
        _wool_puff(15, 17 + bob, 5)
        _wool_puff(19, 16 + bob, 4)
        _wool_puff(13, 13 + bob, 4)
        _wool_puff(18, 13 + bob, 4)
        # Fluffy tail on left
        _wool_puff(6, 16 + bob, 2)

        if not sleeping:
            local.draw_rect(12 + stride, 21 + bob, 2, 5, hoof, filled=True)
            local.draw_rect(17 - stride, 21 + bob, 2, 5, hoof, filled=True)

        # Dark face peeking out on right
        hy = 15 + bob + (3 if grazing and f % 2 == 1 else 0)
        hx = 22 + (1 if grazing and f % 2 == 1 else 0)
        local.draw_ellipse(hx, hy, 3, 3, face_d, filled=True)
        local.draw_ellipse(hx, hy - 1, 3, 2, face, filled=True)
        local.set_pixel(hx + 1, hy - 2, face_l)
        # Wool tuft on forehead + drooping ear
        _wool_puff(hx - 2, hy - 3, 2)
        local.draw_ellipse(hx - 2, hy, 2, 1, face_d, filled=True)
        local.set_pixel(hx - 2, hy, ear_in)
        # Eye
        if sleeping:
            local.draw_line(hx + 1, hy - 1, hx + 2, hy - 1, eye)
        else:
            local.set_pixel(hx + 1, hy - 1, (255, 255, 255, 255))
            local.set_pixel(hx + 2, hy - 1, eye)

        canvas.blit(local, x, y, flip_x=(direction == "left"))
        return

    canvas.blit(local, x, y)
