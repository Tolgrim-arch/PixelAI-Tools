---
name: pixelai-tilesets
description: Generate 16-tile Wang bitmask autotilesets, seamless terrain textures (grass, soil, cobble, wood, brick, water), and orthogonal or 2:1 isometric tilemaps using pixelai-tools (autotile, tilemap, scatter, dither, iso_tile). Use whenever the user asks for terrain tilesets, Godot TileSet atlases, RPG Maker autotiles, ground textures, or tilemap mockups. DO NOT trigger for buildings (use pixelai-buildings-topdown or pixelai-buildings-iso) or characters/creatures (use pixelai-characters-* or pixelai-creatures-topdown).
---

# pixelai-tilesets

## Aesthetic Standard & CLI (Self-Contained)
- **Tilesets Usually Use Pure Lineless (`--lineless` or `"style": "lineless"`):** Ground tiles and autotile atlases tile seamlessly without external 1px black borders! Use `"style": "ext_outline"` only for standalone isolated props/islands.
- **Render CLI:** `python -m pixelai render - -o tileset.png --lineless`

## Interactive Clarification Checklist
Confirm concisely with the user:
1. **Projection:** Orthogonal/top-down (`tile_size: 16|32`) or 2:1 Isometric (`mode: "iso"`, `iso_tile`)?
2. **Asset Type:** 4x4 16-tile Wang bitmask autotile atlas (`autotile`), individual seamless tiles (`defs` + `scatter`), or full composed map (`tilemap`)?
3. **Biomes / Materials:** `inner` (e.g., `water`, `soil`, `cobble`), `outer` (e.g., `grass`, `wheat`), and border `lip` (e.g., `soil_d`, `stone_d`)?
4. **Texture Detail:** Subtle `scatter` pattern (`grass`, `cobble`, `brick`, `wood`, `noise`) + deterministic `seed`?

## `autotile` & `tilemap` Reference
- **4x4 Wang Bitmask Atlas (16 tiles = `4*tile_size x 4*tile_size`):**
  `{"op": "autotile", "x": 0, "y": 0, "tile_size": 16, "inner": "water", "outer": "grass", "lip": "soil_d", "seed": 42}`
- **Tilemap Composition (`ortho` or `iso`):**
  `{"op": "tilemap", "mode": "ortho|iso", "tile_w": 16, "tile_h": 16, "map": {"G": "grass_tile", "W": "water_tile"}, "rows": ["GGG", "GWG", "GGG"]}`

## JSON Example (64x64 Seamless 16-Tile Water-to-Grass Autotile)
```json
{
  "width": 64,
  "height": 64,
  "palette": "cozy24",
  "style": "lineless",
  "ops": [
    {"op": "autotile", "x": 0, "y": 0, "tile_size": 16, "inner": "water", "outer": "grass", "lip": "soil_d", "seed": 42}
  ]
}
```
