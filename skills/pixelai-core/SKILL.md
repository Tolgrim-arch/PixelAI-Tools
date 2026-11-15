---
name: pixelai-core
description: Core CLI router, shared palettes, and base pixel primitives (pixel, line, rect, circle, ellipse, bezier, grid, polygon, fill, dither, scatter, stamp, load_png, mirror_x, mirror_y) for pixelai-tools. Use for general items, icons, props, weapons, potions, food, or when routing to a specialized pixelai-* skill. DO NOT trigger directly as a substitute when a specialized skill matches (pixelai-creatures-topdown, pixelai-characters-*, pixelai-buildings-*, pixelai-portraits, pixelai-tilesets, pixelai-vfx-animations, pixelai-export-qa).
---

# pixelai-core (Router & Base Primitives)

## Skill Router (Load the Narrowest Match First)
- **Top-down farm animals / cozy creatures (Stardew Valley, Fields of Mistria):** `pixelai-creatures-topdown`
- **Top-down 4-dir humanoid characters:** `pixelai-characters-topdown`
- **Side-scroller / platformer characters (Celeste, Metroidvania):** `pixelai-characters-platformer`
- **Isometric 2:1 characters & creatures:** `pixelai-characters-iso`
- **Top-down 3/4 buildings (cottages, barns):** `pixelai-buildings-topdown`
- **Isometric 2:1 buildings & structures:** `pixelai-buildings-iso`
- **Dialogue / character bust portraits:** `pixelai-portraits`
- **Autotiles (16-tile Wang) & ortho/iso tilemaps:** `pixelai-tilesets`
- **Keyframes, particles, weather, multi-layer animations:** `pixelai-vfx-animations`
- **Godot 4 `.tres`, spritesheets, Itch.io showcase, ASCII/PNG QA:** `pixelai-export-qa`

## Aesthetic Standard (Mandatory)
- **Default (`"style": "ext_outline"`):** Lineless Interior + 1px External Outline. Pure color planes, specular bevels (`"bevel": true`), recessed cavities (`"recessed": true`), ZERO dark internal lines.
- **Pure Lineless (`--lineless` or `"style": "lineless"`):** Zero internal or external outlines.
- **Forbidden:** Internal dark outlines (`edge`/`ridge`).

## CLI Quick Usage
```powershell
python -m pixelai render - -o output.png
python -m pixelai render - -o anim.gif --fps 8
python -m pixelai inspect output.png --ascii
python -m pixelai guide
```

## Built-in Palettes
- `cozy24`: `[ink, shadow, soil_d, soil, soil_l, wood_d, wood, wood_l, grass_d, grass, grass_l, wheat_d, wheat, wheat_l, roof_d, roof, roof_l, stone_d, stone, stone_l, water_d, water, water_l, cream]`
- `endesga32` (`0`..`v`), `sweetie16` (`0`..`f`), `pico8` (`0`..`f`), `gameboy` (`0`..`3`), `mistria_portrait`.

## Base Drawing Primitives (`ops`) & Flags
- `rect`: `{"op": "rect", "x": 4, "y": 4, "w": 8, "h": 8, "color": "wood", "filled": true, "bevel": true, "recessed": false}`
- `ellipse` / `circle` / `polygon` / `bezier` / `line` / `pixel` / `fill`
- `grid`: `{"op": "grid", "x": 0, "y": 0, "rows": ["..oo..", ".oggo."], "colors": {"o": "wood_d", "g": "grass"}}`
- `scatter`: `{"op": "scatter", "x": 0, "y": 0, "w": 16, "h": 16, "color": "wood_l", "target_color": "wood", "pattern": "noise|brick|shingle|cobble|wood|grass", "density": 0.2, "seed": 42}`
- `stamp` / `load_png` / `mirror_x` / `mirror_y` / top-level `"extends": "base.png"`
- **Universal flags:** `"inside": true` (clips shading inside existing opaque silhouette), `"outline": false` (excludes shadows/FX from 1px external outline).

## Checklist Before Generating Props/Icons
Ask only if unspecified:
1. Target canvas size (`16x16`, `24x24`, `32x32`)?
2. Outline style (`ext_outline` default vs `lineless`)?
3. Ground shadow (`"shadow": true, "outline": false`) or transparent floating icon?
