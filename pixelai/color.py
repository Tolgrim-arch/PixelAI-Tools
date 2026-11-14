"""Color parsing and palette resolution utilities."""

from typing import Mapping

RGBA = tuple[int, int, int, int]
TRANSPARENT: RGBA = (0, 0, 0, 0)


def parse_color(
    value: str | list[int] | tuple[int, ...],
    palette: Mapping[str, RGBA] | None = None,
) -> RGBA:
    """Parse a hex string, 'transparent', RGBA tuple/list, or palette key into RGBA."""
    if isinstance(value, (list, tuple)):
        if len(value) == 3:
            return (int(value[0]), int(value[1]), int(value[2]), 255)
        if len(value) == 4:
            return (int(value[0]), int(value[1]), int(value[2]), int(value[3]))
        raise ValueError(f"Invalid RGBA sequence: {value!r}")

    if not isinstance(value, str):
        raise ValueError(f"Unsupported color type: {type(value).__name__}")

    if palette and value in palette:
        return palette[value]

    lower = value.strip().lower()
    if lower in ("transparent", "none", ""):
        return TRANSPARENT

    hex_str = lower.lstrip("#")
    if len(hex_str) == 6:
        r, g, b = int(hex_str[0:2], 16), int(hex_str[2:4], 16), int(hex_str[4:6], 16)
        return (r, g, b, 255)
    if len(hex_str) == 8:
        r, g, b, a = (
            int(hex_str[0:2], 16),
            int(hex_str[2:4], 16),
            int(hex_str[4:6], 16),
            int(hex_str[6:8], 16),
        )
        return (r, g, b, a)

    raise ValueError(f"Invalid color value: {value!r}")
