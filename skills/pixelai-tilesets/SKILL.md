---
name: pixelai-tilesets
description: Generate 16-tile Wang bitmask autotilesets, seamless terrain textures (grass, soil, cobble, wood, brick, water), and orthogonal or 2:1 isometric tilemaps using pixelai-tools (autotile, tilemap, scatter, dither, iso_tile). Use whenever the user asks for terrain tilesets, Godot TileSet atlases, RPG Maker autotiles, ground textures, or tilemap mockups. DO NOT trigger for buildings (use pixelai-buildings-topdown or pixelai-buildings-iso) or characters/creatures (use pixelai-characters-* or pixelai-creatures-topdown).
---

# pixelai-tilesets

## Aesthetic Standard & CLI (Self-Contained)
- **Tilesets Usually Use Pure Lineless (`--lineless` or `"style": "lineless"`):** Ground tiles and autotile atlases tile seamlessly without external 1px black borders! Use `"style": "ext_outline"` only for standalone isolated props/islands.
- **Render CLI:** `python -m pixelai render - -o tileset.png --lineless`

## Art direction checklist
Use the following design choices to interpret the brief. Use sensible defaults for choices the user leaves open so a single prompt can produce a first asset. Ask one plain-language question only if a missing choice would make the result unusable.
1. **Vista del juego:** ¿Vista desde arriba (top-down clásico) o en ángulo isométrico tipo rombo?
2. **Qué necesitas:** ¿Un set completo de bordes para unir agua/tierra con pasto automáticamente, un par de suelos repetibles, o un mapa de ejemplo ya armado?
3. **Terrenos y bordes:** ¿Qué materiales se conectan (ej. agua con pasto, camino de tierra sobre pasto, adoquín con musgo) y de qué tamaño son los cuadros del mapa (ej. 16x16 o 32x32)?

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
