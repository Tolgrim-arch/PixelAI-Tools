"""Core pixel canvas and deterministic drawing primitives."""

from collections import deque
import random
from pixelai.color import RGBA, TRANSPARENT


class Canvas:
    """2D RGBA pixel grid with deterministic drawing primitives."""

    def __init__(self, width: int, height: int, fill: RGBA = TRANSPARENT) -> None:
        if width <= 0 or height <= 0:
            raise ValueError(f"Canvas dimensions must be positive, got {width}x{height}")
        self.width = width
        self.height = height
        self.pixels: list[RGBA] = [fill] * (width * height)

    def copy(self) -> "Canvas":
        out = Canvas(self.width, self.height)
        out.pixels = self.pixels.copy()
        return out

    def in_bounds(self, x: int, y: int) -> bool:
        return 0 <= x < self.width and 0 <= y < self.height

    def get_pixel(self, x: int, y: int) -> RGBA:
        if not self.in_bounds(x, y):
            return TRANSPARENT
        return self.pixels[y * self.width + x]

    def set_pixel(self, x: int, y: int, color: RGBA) -> None:
        if self.in_bounds(x, y):
            self.pixels[y * self.width + x] = color

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
        self, x: int, y: int, w: int, h: int, color: RGBA, filled: bool = True
    ) -> None:
        """Draw a filled or outlined rectangle."""
        if w <= 0 or h <= 0:
            return
        if filled:
            for py in range(y, y + h):
                for px in range(x, x + w):
                    self.set_pixel(px, py, color)
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
    ) -> None:
        """Stamp another Canvas at (x, y) with optional flip and color remapping."""
        for sy in range(other.height):
            for sx in range(other.width):
                src_x = (other.width - 1 - sx) if flip_x else sx
                src_y = (other.height - 1 - sy) if flip_y else sy
                c = other.get_pixel(src_x, src_y)
                if c[3] == 0:
                    continue
                if remap and c in remap:
                    c = remap[c]
                self.set_pixel(x + sx, y + sy, c)

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
                    offset = 2 if row % 2 == 1 else 0
                    if (py - y) % 3 == 0 or (px - x + offset) % 4 == 0:
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
                else:  # "noise"
                    if rng.random() < density:
                        self.set_pixel(px, py, color)
