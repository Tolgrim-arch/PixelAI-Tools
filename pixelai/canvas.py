"""Core pixel canvas, per-pixel Z-buffer, and deterministic drawing primitives."""

from collections import deque
import math
import random
from pixelai.color import RGBA, TRANSPARENT, brighten, darken


class Canvas:
    """2D RGBA pixel grid with optional per-pixel Z-buffer and deterministic primitives."""

    def __init__(self, width: int, height: int, fill: RGBA = TRANSPARENT) -> None:
        if width <= 0 or height <= 0:
            raise ValueError(f"Canvas dimensions must be positive, got {width}x{height}")
        self.width = width
        self.height = height
        self.pixels: list[RGBA] = [fill] * (width * height)
        self.z_buffer: list[float] = [float("-inf")] * (width * height)
        self.no_outline: set[int] = set()
        self.shadow_pixels: set[int] = set()
        self.mark_no_outline: bool = False
        self.mark_shadow: bool = False
        self.clip_to_opaque: bool = False
        self.current_z: float | None = None
        self.last_iso_box: tuple[int, int, int, int, int] | None = None
        self.last_chimney: tuple[int, int] | None = None
        self.clipped_pixels: int = 0
        self.warnings: list[str] = []

    def copy(self) -> "Canvas":
        out = Canvas(self.width, self.height)
        out.pixels = self.pixels.copy()
        out.z_buffer = self.z_buffer.copy()
        out.no_outline = self.no_outline.copy()
        out.shadow_pixels = self.shadow_pixels.copy()
        out.mark_no_outline = self.mark_no_outline
        out.mark_shadow = self.mark_shadow
        out.clip_to_opaque = self.clip_to_opaque
        out.current_z = self.current_z
        out.last_iso_box = self.last_iso_box
        out.last_chimney = self.last_chimney
        out.clipped_pixels = self.clipped_pixels
        out.warnings = self.warnings.copy()
        return out

    def in_bounds(self, x: int, y: int) -> bool:
        return 0 <= x < self.width and 0 <= y < self.height

    def is_outline_source(self, x: int, y: int) -> bool:
        """Return True if pixel (x, y) is opaque and eligible to cast an external outline."""
        if not self.in_bounds(x, y):
            return False
        idx = y * self.width + x
        return self.pixels[idx][3] > 0 and idx not in self.no_outline

    def touches_border(self) -> bool:
        """Return True if any outline-eligible opaque pixel sits on the outer 1px border."""
        for x in range(self.width):
            if self.is_outline_source(x, 0) or self.is_outline_source(x, self.height - 1):
                return True
        for y in range(self.height):
            if self.is_outline_source(0, y) or self.is_outline_source(self.width - 1, y):
                return True
        return False

    def get_pixel(self, x: int, y: int) -> RGBA:
        if not self.in_bounds(x, y):
            return TRANSPARENT
        return self.pixels[y * self.width + x]

    def set_pixel(self, x: int, y: int, color: RGBA, z: float | None = None) -> None:
        if self.in_bounds(x, y):
            idx = y * self.width + x
            if self.clip_to_opaque:
                if self.pixels[idx][3] == 0 or idx in self.no_outline:
                    return
            eff_z = z if z is not None else self.current_z
            if eff_z is not None and color[3] > 0:
                if eff_z < self.z_buffer[idx]:
                    return
                self.z_buffer[idx] = eff_z
            self.pixels[idx] = color
            if color[3] == 0:
                self.no_outline.discard(idx)
                self.shadow_pixels.discard(idx)
            else:
                if self.mark_no_outline or self.mark_shadow:
                    self.no_outline.add(idx)
                else:
                    self.no_outline.discard(idx)
                if self.mark_shadow:
                    self.shadow_pixels.add(idx)
                else:
                    self.shadow_pixels.discard(idx)
        elif color[3] > 0 and not self.clip_to_opaque:
            self.clipped_pixels += 1

    def draw_line(self, x0: int, y0: int, x1: int, y1: int, color: RGBA) -> None:
        """Draw a 1px line using Bresenham's algorithm."""
        dx = abs(x1 - x0)
        dy = -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        while True:
            self.set_pixel(x0, y0, color)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x0 += sx
            if e2 <= dx:
                err += dx
                y0 += sy

    def draw_rect(
        self,
        x: int,
        y: int,
        w: int,
        h: int,
        color: RGBA,
        filled: bool = True,
        bevel: bool = False,
        recessed: bool = False,
    ) -> None:
        """Draw a filled or outlined rectangle with optional lineless bevel or recessed lip."""
        if w <= 0 or h <= 0:
            return
        if filled:
            for py in range(y, y + h):
                for px in range(x, x + w):
                    self.set_pixel(px, py, color)
            if recessed and w >= 2 and h >= 2:
                rec_col = darken(color, 0.72)
                self.draw_line(x, y, x + w - 1, y, rec_col)
                self.draw_line(x, y, x, y + h - 1, rec_col)
            elif bevel and w >= 2 and h >= 2:
                hl_col = brighten(color, 1.15)
                sh_col = darken(color, 0.80)
                self.draw_line(x, y, x + w - 1, y, hl_col)
                self.draw_line(x, y, x, y + h - 1, hl_col)
                if h >= 3:
                    self.draw_line(x, y + h - 1, x + w - 1, y + h - 1, sh_col)
                if w >= 3:
                    self.draw_line(x + w - 1, y + 1, x + w - 1, y + h - 1, sh_col)
        else:
            x2, y2 = x + w - 1, y + h - 1
            self.draw_line(x, y, x2, y, color)
            self.draw_line(x, y2, x2, y2, color)
            self.draw_line(x, y, x, y2, color)
            self.draw_line(x2, y, x2, y2, color)

    def draw_circle(
        self, cx: int, cy: int, r: int, color: RGBA, filled: bool = False
    ) -> None:
        """Draw a pixel-perfect circle using the midpoint algorithm."""
        if r < 0:
            return
        if r == 0:
            self.set_pixel(cx, cy, color)
            return

        x, y, err = r, 0, 1 - r
        while x >= y:
            if filled:
                self.draw_line(cx - x, cy + y, cx + x, cy + y, color)
                self.draw_line(cx - x, cy - y, cx + x, cy - y, color)
                self.draw_line(cx - y, cy + x, cx + y, cy + x, color)
                self.draw_line(cx - y, cy - x, cx + y, cy - x, color)
            else:
                for px, py in (
                    (cx + x, cy + y), (cx - x, cy + y),
                    (cx + x, cy - y), (cx - x, cy - y),
                    (cx + y, cy + x), (cx - y, cy + x),
                    (cx + y, cy - x), (cx - y, cy - x),
                ):
                    self.set_pixel(px, py, color)
            y += 1
            if err < 0:
                err += 2 * y + 1
            else:
                x -= 1
                err += 2 * (y - x) + 1

    def draw_ellipse(
        self, cx: int, cy: int, rx: int, ry: int, color: RGBA, filled: bool = True
    ) -> None:
        """Draw a filled or outlined pixel-art ellipse centered at (cx, cy)."""
        if rx < 0 or ry < 0:
            return
        if rx == 0 and ry == 0:
            self.set_pixel(cx, cy, color)
            return
        if ry == 0:
            self.draw_line(cx - rx, cy, cx + rx, cy, color)
            return
        if rx == 0:
            self.draw_line(cx, cy - ry, cx, cy + ry, color)
            return

        if filled:
            eff_ry = ry + 0.45
            for dy in range(-ry, ry + 1):
                span = int(round(rx * math.sqrt(max(0.0, 1.0 - (dy / eff_ry) ** 2))))
                self.draw_line(cx - span, cy + dy, cx + span, cy + dy, color)
        else:
            steps = max(16, int((rx + ry) * 4))
            prev: tuple[int, int] | None = None
            for i in range(steps + 1):
                theta = (2.0 * math.pi * i) / steps
                px = cx + int(round(rx * math.cos(theta)))
                py = cy + int(round(ry * math.sin(theta)))
                if prev is not None:
                    self.draw_line(prev[0], prev[1], px, py, color)
                prev = (px, py)

    def draw_bezier(
        self, points: list[tuple[int, int]], color: RGBA, thickness: int = 1
    ) -> None:
        """Draw a quadratic or N-degree Bézier curve using de Casteljau subdivision."""
        if len(points) < 2:
            return
        total_dist = sum(
            math.hypot(points[i + 1][0] - points[i][0], points[i + 1][1] - points[i][1])
            for i in range(len(points) - 1)
        )
        steps = max(8, int(total_dist * 2))
        prev: tuple[int, int] | None = None

        for step in range(steps + 1):
            t = step / steps
            work = [(float(p[0]), float(p[1])) for p in points]
            while len(work) > 1:
                work = [
                    (
                        work[i][0] * (1.0 - t) + work[i + 1][0] * t,
                        work[i][1] * (1.0 - t) + work[i + 1][1] * t,
                    )
                    for i in range(len(work) - 1)
                ]
            px, py = int(round(work[0][0])), int(round(work[0][1]))
            if prev is not None:
                self.draw_line(prev[0], prev[1], px, py, color)
                if thickness > 1:
                    self.draw_circle(px, py, thickness // 2, color, filled=True)
            prev = (px, py)

    def draw_polygon(
        self, points: list[tuple[int, int]], color: RGBA, filled: bool = True
    ) -> None:
        """Draw a filled or outlined polygon from a list of (x, y) vertices."""
        n = len(points)
        if n == 0:
            return
        if n == 1:
            self.set_pixel(points[0][0], points[0][1], color)
            return

        if filled and n >= 3:
            min_y = max(0, min(p[1] for p in points))
            max_y = min(self.height - 1, max(p[1] for p in points))
            for y in range(min_y, max_y + 1):
                xs: list[float] = []
                for i in range(n):
                    x0, y0 = points[i]
                    x1, y1 = points[(i + 1) % n]
                    if y0 == y1:
                        continue
                    if min(y0, y1) <= y < max(y0, y1):
                        x_int = x0 + (y - y0) * (x1 - x0) / (y1 - y0)
                        xs.append(x_int)
                xs.sort()
                for i in range(0, len(xs) - 1, 2):
                    self.draw_line(int(round(xs[i])), y, int(round(xs[i + 1])), y, color)

        for i in range(n):
            x0, y0 = points[i]
            x1, y1 = points[(i + 1) % n]
            self.draw_line(x0, y0, x1, y1, color)

    def flood_fill(self, x: int, y: int, color: RGBA) -> None:
        """4-way flood fill starting at (x, y)."""
        if not self.in_bounds(x, y):
            return
        target = self.get_pixel(x, y)
        if target == color:
            return
        queue = deque([(x, y)])
        while queue:
            px, py = queue.popleft()
            if not self.in_bounds(px, py) or self.get_pixel(px, py) != target:
                continue
            self.set_pixel(px, py, color)
            queue.extend(((px + 1, py), (px - 1, py), (px, py + 1), (px, py - 1)))

    def mirror_x(self) -> None:
        """Mirror left half onto right half."""
        half = self.width // 2
        for y in range(self.height):
            for x in range(half):
                c = self.get_pixel(x, y)
                if c[3] > 0:
                    self.set_pixel(self.width - 1 - x, y, c)

    def mirror_y(self) -> None:
        """Mirror top half onto bottom half."""
        half = self.height // 2
        for y in range(half):
            for x in range(self.width):
                c = self.get_pixel(x, y)
                if c[3] > 0:
                    self.set_pixel(x, self.height - 1 - y, c)

    def draw_grid(
        self, x: int, y: int, rows: list[str], color_map: dict[str, RGBA]
    ) -> None:
        """Draw pixels from an ASCII grid; '.' and ' ' are skipped (transparent)."""
        for dy, row in enumerate(rows):
            for dx, ch in enumerate(row):
                if ch in (".", " "):
                    continue
                if ch not in color_map:
                    raise ValueError(f"Grid symbol {ch!r} not found in palette/colors")
                self.set_pixel(x + dx, y + dy, color_map[ch])

    def draw_dither_rect(
        self, x: int, y: int, w: int, h: int, color_a: RGBA, color_b: RGBA
    ) -> None:
        """Fill a rectangle with a 2-color checkerboard dither pattern."""
        for py in range(y, y + h):
            for px in range(x, x + w):
                self.set_pixel(px, py, color_a if (px + py) % 2 == 0 else color_b)

    def blit(
        self,
        other: "Canvas",
        x: int,
        y: int,
        flip_x: bool = False,
        flip_y: bool = False,
        remap: dict[RGBA, RGBA] | None = None,
        angle: float = 0.0,
        pivot: tuple[float, float] | None = None,
    ) -> None:
        """Stamp another Canvas at (x, y) with optional flip, remap, and pivot rotation."""
        if abs(angle) < 1e-6:
            prev_no, prev_sh = self.mark_no_outline, self.mark_shadow
            for sy in range(other.height):
                for sx in range(other.width):
                    src_x = (other.width - 1 - sx) if flip_x else sx
                    src_y = (other.height - 1 - sy) if flip_y else sy
                    c = other.get_pixel(src_x, src_y)
                    if c[3] == 0:
                        continue
                    if remap and c in remap:
                        c = remap[c]
                    src_idx = src_y * other.width + src_x
                    self.mark_no_outline = prev_no or (src_idx in other.no_outline)
                    self.mark_shadow = prev_sh or (src_idx in other.shadow_pixels)
                    self.set_pixel(x + sx, y + sy, c)
            self.mark_no_outline, self.mark_shadow = prev_no, prev_sh
            return

        px, py = pivot if pivot is not None else ((other.width - 1) / 2.0, (other.height - 1) / 2.0)
        rad = math.radians(angle)
        cos_a, sin_a = math.cos(rad), math.sin(rad)
        radius = int(math.ceil(math.hypot(other.width, other.height)))
        cx_dst, cy_dst = x + px, y + py

        for dy in range(-radius, radius + 1):
            for dx in range(-radius, radius + 1):
                sx_f = px + dx * cos_a + dy * sin_a
                sy_f = py - dx * sin_a + dy * cos_a
                sx, sy = int(round(sx_f)), int(round(sy_f))
                if not other.in_bounds(sx, sy):
                    continue
                src_x = (other.width - 1 - sx) if flip_x else sx
                src_y = (other.height - 1 - sy) if flip_y else sy
                c = other.get_pixel(src_x, src_y)
                if c[3] == 0:
                    continue
                if remap and c in remap:
                    c = remap[c]
                self.set_pixel(int(round(cx_dst + dx)), int(round(cy_dst + dy)), c)

    def scatter(
        self,
        x: int,
        y: int,
        w: int,
        h: int,
        color: RGBA,
        density: float = 0.15,
        seed: int = 42,
        target_color: RGBA | None = None,
        pattern: str = "noise",
    ) -> None:
        """Apply a deterministic procedural texture within (x, y, w, h)."""
        rng = random.Random(seed)
        for py in range(y, y + h):
            for px in range(x, x + w):
                if not self.in_bounds(px, py):
                    continue
                if target_color is not None and self.get_pixel(px, py) != target_color:
                    continue
                if pattern == "brick":
                    row = (py - y) // 3
                    offset = 3 if row % 2 == 1 else 0
                    col = (px - x + offset) // 6
                    cell_hash = ((row * 73856093) ^ (col * 19349663) ^ seed) & 0xFFFF
                    if density >= 1.0 or (cell_hash / 65535.0) <= density:
                        is_h_mortar = (py - y) % 3 == 2 and (px - x + offset) % 6 != 0
                        is_v_mortar = (px - x + offset) % 6 == 0 and (py - y) % 3 != 2
                        if is_h_mortar or is_v_mortar:
                            self.set_pixel(px, py, color)
                elif pattern == "shingle":
                    row = (py - y) // 4
                    offset = 3 if row % 2 == 1 else 0
                    col = (px - x + offset) // 6
                    tx = (px - x + offset) % 6
                    ty = (py - y) % 4
                    cell_hash = ((row * 83492791) ^ (col * 2971215073) ^ seed) & 0xFFFF
                    if density >= 1.0 or (cell_hash / 65535.0) <= min(1.0, density * 1.8):
                        if (ty == 3 and 1 <= tx <= 4) or (ty == 2 and tx in (0, 5)):
                            self.set_pixel(px, py, color)
                elif pattern == "cobble":
                    row = (py - y) // 4
                    offset = 4 if row % 2 == 1 else 0
                    col = (px - x + offset) // 8
                    tx = (px - x + offset) % 8
                    ty = (py - y) % 4
                    cell_hash = ((row * 49979693) ^ (col * 86028121) ^ seed) & 0xFFFF
                    if density >= 1.0 or (cell_hash / 65535.0) <= density:
                        if (ty == 3 and 2 <= tx <= 6) or (ty in (1, 2) and tx == 1):
                            self.set_pixel(px, py, color)
                elif pattern == "wood":
                    if (px - x) % 3 == 0 or ((py - y + (px - x) * 2) % 7 == 0 and rng.random() < 0.5):
                        self.set_pixel(px, py, color)
                elif pattern == "grass":
                    if rng.random() < density:
                        self.set_pixel(px, py, color)
                        if (
                            py - 1 >= y
                            and (target_color is None or self.get_pixel(px, py - 1) == target_color)
                        ):
                            self.set_pixel(px, py - 1, color)
                else:
                    if rng.random() < density:
                        self.set_pixel(px, py, color)

    def draw_particles(
        self,
        x: int,
        y: int,
        w: int,
        h: int,
        count: int,
        color: RGBA,
        frame: int = 0,
        total_frames: int = 4,
        mode: str = "smoke",
        size: int = 1,
        seed: int = 42,
    ) -> None:
        """Render a deterministic looping particle system (smoke, leaves, rain, sparks)."""
        if w <= 0 or h <= 0 or count <= 0:
            return
        rng = random.Random(seed)
        phase = (frame % max(1, total_frames)) / max(1, total_frames)

        for i in range(count):
            base_x = rng.random()
            base_y = rng.random()
            p_phase = (base_y + phase) % 1.0

            if mode == "smoke":
                # Rises upward and drifts sideways in a sine wave
                py = y + int((1.0 - p_phase) * (h - 1))
                sway = math.sin((p_phase + i * 0.3) * math.pi * 2.0) * (w * 0.25)
                px = x + int(w * 0.5 + sway)
                r = max(1, int(size + p_phase * 1.5))
                self.draw_circle(px, py, r - 1, color, filled=True)
            elif mode == "leaves":
                # Drifts down and right with flutter
                py = y + int(p_phase * (h - 1))
                sway = math.sin((p_phase + i * 0.5) * math.pi * 2.0) * 3.0
                px = x + int(((base_x * w) + p_phase * (w * 0.4) + sway) % w)
                self.draw_rect(px, py, size, size, color)
            elif mode == "rain":
                py = y + int(p_phase * (h - 1))
                px = x + int((base_x * w) % w)
                self.draw_line(px, py, px - 1, py + max(1, size), color)
            else:  # "sparks"
                angle = base_x * math.pi * 2.0
                dist = p_phase * min(w, h) * 0.5
                px = x + w // 2 + int(math.cos(angle) * dist)
                py = y + h // 2 + int(math.sin(angle) * dist)
                self.draw_rect(px, py, size, size, color)
