"""Built-in curated pixel art palettes."""

from typing import Any
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
    "endesga32": {
        "0": "#be4a2f", "1": "#d77643", "2": "#ead4aa", "3": "#e4a672",
        "4": "#b86f50", "5": "#733e39", "6": "#3e2731", "7": "#a22633",
        "8": "#e43b44", "9": "#f77622", "a": "#feae34", "b": "#fee761",
        "c": "#63c74d", "d": "#3e8948", "e": "#265c42", "f": "#193c3e",
        "g": "#124e89", "h": "#0099db", "i": "#2ce8f5", "j": "#ffffff",
        "k": "#c0cbdc", "l": "#8b9bb4", "m": "#5a6988", "n": "#3a4466",
        "o": "#262b44", "p": "#181425", "q": "#ff0044", "r": "#68386c",
        "s": "#b55088", "t": "#f6757a", "u": "#e8b796", "v": "#c28569",
    },
    "cozy24": {
        "ink": "#21181b", "shadow": "#3b2d38",
        "soil_d": "#5c3c28", "soil": "#825438", "soil_l": "#a8734f",
        "wood_d": "#6e422c", "wood": "#9c603c", "wood_l": "#c98b5b",
        "grass_d": "#336840", "grass": "#589c4c", "grass_l": "#8cd660",
        "wheat_d": "#d48e3b", "wheat": "#f2bf52", "wheat_l": "#ffe680",
        "roof_d": "#8c3232", "roof": "#c24b38", "roof_l": "#e87858",
        "stone_d": "#596070", "stone": "#828c9e", "stone_l": "#b5bfd1",
        "water_d": "#326496", "water": "#4fa4c4", "water_l": "#8be0f0",
        "cream": "#fff5e4",
    },
    "mistria_portrait": {
        # Portrait-focused swatches calibrated from the supplied character
        # portrait references: warm skin, plum ink, muted workwear and straw.
        "ink": "#2b1b2b", "shadow": "#4a2d36",
        "skin": "#f2c38f", "skin_l": "#ffe0aa", "skin_d": "#b96d5c",
        "hair": "#6b3f35", "hair_l": "#925442", "hair_d": "#402538",
        "shirt": "#d9e5d2", "shirt_d": "#afc3b4",
        "garment": "#704b3b", "garment_d": "#4b302e",
        "accent": "#d69b4b", "gold": "#d69b4b", "soil": "#9a613b",
        "hat_color": "#d69b4b", "hat_light": "#fff0c9", "hat_dark": "#9a613b",
        "cream": "#fff0c9",
    },
}


def list_palettes() -> dict[str, dict[str, str]]:
    """Return all built-in palette definitions."""
    return _RAW_PALETTES


def get_palette(name: str) -> dict[str, RGBA]:
    """Return a built-in palette by name, parsed into RGBA tuples."""
    key = name.strip().lower()
    if key not in _RAW_PALETTES:
        available = ", ".join(sorted(_RAW_PALETTES))
        raise ValueError(f"Unknown palette {name!r}. Available: {available}")
    return {k: parse_color(v) for k, v in _RAW_PALETTES[key].items()}


def resolve_palette(
    raw_palette: str | dict[str, Any] | None,
    palette_ext: dict[str, Any] | None = None,
) -> dict[str, RGBA]:
    """Resolve base palette (name or dict) and merge optional palette_ext."""
    if not raw_palette:
        palette: dict[str, RGBA] = {}
    elif isinstance(raw_palette, str):
        palette = get_palette(raw_palette)
    else:
        palette = {k: parse_color(v) for k, v in raw_palette.items()}

    if palette_ext:
        for k, v in palette_ext.items():
            palette[k] = parse_color(v, palette)
    return palette
