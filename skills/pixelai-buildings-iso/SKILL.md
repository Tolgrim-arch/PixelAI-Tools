---
name: pixelai-buildings-iso
description: Generate 2:1 isometric pixel art buildings, towers, walls, roofs, and multi-block 3D structures with per-pixel Z-buffering using pixelai-tools (iso_structure, iso_box, iso_roof, iso_wall_rect, iso_tile). Use when asked for isometric cottages, castles, shops, rooms, or architectural blocks in Habbo, Tactics, or isometric builder style. DO NOT trigger for top-down 3/4 buildings (use pixelai-buildings-topdown), isometric characters (use pixelai-characters-iso), or autotiles (use pixelai-tilesets).
---

# pixelai-buildings-iso

## Aesthetic Standard & CLI (Self-Contained)
- **Default (`"style": "ext_outline"`):** Lineless Interior + 1px External Outline. Uses 3-plane 2:1 shading (`top` lightest, `left` mid, `right` darkest), specular `bevel: true`, `eave_shadow: true`, and `recessed: true` doors/windows with ZERO dark internal lines.
- **Render CLI:** `python -m pixelai render - -o iso_building.png`

## Interactive Clarification Checklist
Confirm concisely with the user:
1. **Structure Type:** Single cottage/tower or multi-wing `iso_structure`?
2. **Roof Style:** `"pyramid"`, `"gable_left"`, or `"gable_right"`?
3. **Dimensions & Scale:** Tile half-width `rx` (e.g., `12` or `16`, `ry = rx / 2`) and wall height `h`?
4. **Architectural Openings:** Doors (`arch: true|false`) and windows on `"left"` / `"right"` walls?
5. **Ground Shadow & Chimney:** `ground_shadow` thickness (`0..3`) and chimney/smoke?

## 2:1 Isometric Primitives (`ops`)
- `iso_structure` (recommended for multi-part buildings — sorts by `gx + gy, gz` with per-pixel Z-buffer):
  - `origin_x`, `origin_y`, `bevel: true`, `ground_shadow: 2`, `items: [{"type": "box|roof", "gx": 0, "gy": 0, "gz": 0, "rx": 12, "h": 10, ...}]`
- `iso_box`: `cx`, `cy`, `rx`, `ry`, `h`, `top`, `left`, `right`, `bevel`, `ground_shadow`, optional `door`, `windows`, `roof`
- `iso_roof`: `cx`, `cy`, `rx`, `ry`, `h`, `style` (`pyramid|gable_left|gable_right`), `left`, `right`, `gable`, `eave_shadow`, `bevel`, `chimney`
- `iso_wall_rect`: `face: "left|right"`, `w`, `h`, `color`, `arch: true|false`, `recessed: true` (auto-snaps onto `last_iso_box`!)
- `iso_tile`: `cx`, `cy`, `rx`, `ry`, `color`

## JSON Example (2:1 Isometric Stone & Timber Cottage)
```json
{
  "width": 64,
  "height": 64,
  "palette": "cozy24",
  "style": "ext_outline",
  "ops": [
    {
      "op": "iso_structure",
      "origin_x": 32,
      "origin_y": 38,
      "bevel": true,
      "ground_shadow": 2,
      "items": [
        {"type": "box", "gx": 0, "gy": 0, "gz": 0, "rx": 14, "ry": 7, "h": 14, "top": "cream", "left": "cream", "right": "stone_l", "door": {"face": "left", "w": 5, "h": 8, "color": "wood_d", "arch": true}, "windows": [{"face": "right", "w": 4, "h": 4, "color": "water"}]},
        {"type": "roof", "gx": 0, "gy": 0, "gz": 14, "rx": 15, "ry": 8, "h": 10, "style": "gable_left", "left": "roof_l", "right": "roof_d", "gable": "wood", "eave_shadow": true, "chimney": true}
      ]
    }
  ]
}
```
