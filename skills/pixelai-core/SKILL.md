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

## Regla de Oro para Usuarios No-Artistas
Cuando el usuario pida un pixel art sin especificar detalles de juego, **detente un momento antes de renderizar** y haz 3–5 preguntas cortas **en lenguaje natural de juego, cero tecnicismos** (ej. *"¿vertical o en diagonal?"*, *"¿con sombra debajo o sin sombra?"*, *"¿sobre pasto ya dibujado o incluido?"*). Nunca preguntes sobre JSON, bitmasks o nombres internos de paletas.

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
