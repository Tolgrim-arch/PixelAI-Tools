"""Self-check for the native pine generator (run: python tests/check_pine.py)."""

from pixelai.canvas import Canvas
from pixelai.palettes import resolve_palette
from pixelai import broadleaf, conifer


def main() -> None:
    palette = resolve_palette("cozy24")
    for size in (64, 128):
        c = Canvas(size, size)
        conifer.draw_pine(c, 0, 0, palette, {"w": size, "h": size})
        assert not c.touches_border(), f"{size}px pine touches border"
        assert sum(1 for p in c.pixels if p[3] > 0) > size * size // 6, f"{size}px pine too sparse"
        for var in ("oak", "fruit"):
            b = Canvas(size, size)
            broadleaf.draw_broadleaf(b, 0, 0, palette, {"w": size, "h": size, "variant": var})
            assert not b.touches_border(), f"{size}px {var} touches border"
            assert sum(1 for p in b.pixels if p[3] > 0) > size * size // 6, f"{size}px {var} too sparse"
    a, b = Canvas(128, 128), Canvas(128, 128)
    conifer.draw_pine(a, 0, 0, palette, {"seed": 3})
    conifer.draw_pine(b, 0, 0, palette, {"seed": 3})
    assert a.pixels == b.pixels, "pine must be deterministic per seed"
    print("pine checks OK")


if __name__ == "__main__":
    main()
