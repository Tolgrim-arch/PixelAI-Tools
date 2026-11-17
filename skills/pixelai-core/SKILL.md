---
name: pixelai-core
description: Core CLI router, shared palettes, and base pixel primitives (pixel, line, rect, circle, ellipse, bezier, grid, polygon, fill, dither, scatter, stamp, load_png, mirror_x, mirror_y) for pixelai-tools. Use for general props/custom shapes or when routing to a specialized pixelai-* skill. DO NOT trigger directly as a substitute when a specialized skill matches (pixelai-creatures-topdown, pixelai-characters-*, pixelai-buildings-*, pixelai-portraits, pixelai-tilesets, pixelai-vfx-animations, pixelai-items-icons, pixelai-foliage-nature, pixelai-ui-hud, pixelai-vibe-palettes, pixelai-export-qa).
---

# pixelai-core (Router & Base Primitives)

## Skill Router (Load the Narrowest Match First)
- **Visual mood / game reference ("estilo Game Boy", "Stardew", "pastel"):** pair with `pixelai-vibe-palettes`
- **Items, weapons, potions, chests, gems, keys, coins:** `pixelai-items-icons`
- **Trees, bushes, rocks, ores, flowers, 4-stage crops:** `pixelai-foliage-nature`
- **UI/HUD panels, health/mana bars, hearts, buttons, inventory slots:** `pixelai-ui-hud`
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

## Prompt-to-asset workflow

1. Run `python -m pixelai --version`. If the runtime is missing, install the bundled project from the plugin root (two directories above this skill) using `python -m pip install "<plugin-root>"`. Use the same interpreter throughout.
2. Choose the closest specialized skill. Use reasonable defaults for unspecified art direction and use `python -m pixelai guide` for unfamiliar operations.
3. Write a JSON spec next to the intended assets. Run `python -m pixelai validate spec.json` and correct reported errors. Check warnings for accidental clipping.
4. Run `python -m pixelai render spec.json -o output.png --json`. Use the returned artifact paths and `inspect` to check the result. Review the actual image when the host can display it.

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

## Built-in Palettes & Universal Flags
- `cozy24`, `endesga32`, `sweetie16`, `pico8`, `gameboy`, `mistria_portrait`.
- Top-level `"auto_pad": true` prevents 1px external outline edge clipping.
- Universal op flags: `"inside": true` (clips shading inside existing opaque silhouette), `"outline": false` (excludes shadows/FX from 1px external outline).
- Primitives: `pixel`, `line`, `rect` (`bevel`, `recessed`), `circle`, `ellipse`, `bezier`, `polygon`, `fill`, `grid`, `dither`, `scatter`, `stamp`, `load_png`, `mirror_x`, `mirror_y`, `"extends"`.
