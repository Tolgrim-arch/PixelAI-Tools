"""Built-in curated pixel art palettes."""

from pixelai.color import RGBA, parse_color

_RAW_PALETTES: dict[str, dict[str, str]] = {
    "pico8": {
        "0": "#000000", "1": "#1d2b53", "2": "#7e2553", "3": "#008751",
        "4": "#ab5236", "5": "#5f574f", "6": "#c2c3c7", "7": "#fff1e8",
        "8": "#ff004d", "9": "#ffa300", "a": "#ffec27", "b": "#00e436",
        "c": "#29adff", "d": "#83769c", "e": "#ff77a8", "f": "#ffccaa",
    },
    "gameboy": {
        "0": "#0f380f", "1": "#306230", "2": "#8bac0f", "3": "#9bbc0f",
    },
    "sweetie16": {
        "0": "#1a1c2c", "1": "#5d275d", "2": "#b13e53", "3": "#ef7d57",
        "4": "#ffcd75", "5": "#a7f070", "6": "#38b764", "7": "#257179",
        "8": "#29366f", "9": "#3b5dc9", "a": "#41a6f6", "b": "#73eff7",
        "c": "#f4f4f4", "d": "#94b0c2", "e": "#566c86", "f": "#333c57",
    },
}


def get_palette(name: str) -> dict[str, RGBA]:
    """Return a built-in palette by name, parsed into RGBA tuples."""
    key = name.strip().lower()
    if key not in _RAW_PALETTES:
        available = ", ".join(sorted(_RAW_PALETTES))
        raise ValueError(f"Unknown palette {name!r}. Available: {available}")
    return {k: parse_color(v) for k, v in _RAW_PALETTES[key].items()}
