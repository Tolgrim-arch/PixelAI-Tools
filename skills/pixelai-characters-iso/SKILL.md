---
name: pixelai-characters-iso
description: Generate 2:1 isometric character and creature sprites for tactical RPGs and isometric sims (Final Fantasy Tactics, Tactics Ogre, Into the Breach, Habbo, isometric cozy sims) using pixelai-tools. Use whenever the user requests isometric characters, units, or animals facing diagonal se/sw/ne/nw directions. DO NOT trigger for top-down orthogonal characters (use pixelai-characters-topdown), platformers (use pixelai-characters-platformer), or isometric buildings (use pixelai-buildings-iso).
---

# pixelai-characters-iso

## Aesthetic Standard & CLI (Self-Contained)
- **Default (`"style": "ext_outline"`):** Lineless Interior + 1px External Outline (no internal dark lines). Optional `--lineless`.
- **Render CLI:** `python -m pixelai render - -o unit_iso.png` (or `.gif --fps 8`, or `--sheet --columns 4 --godot unit_iso.tres`).

## Isometric 2:1 Character Rules
- **Diagonal Facings:** Use `"se"` (front-right), `"sw"` (front-left), `"ne"` (back-right), `"nw"` (back-left) with `"perspective": "iso"`.
- **2:1 Foot Alignment:** Front/back feet stagger vertically along the 2:1 isometric ground plane so characters stand cleanly on `iso_tile` / `tilemap(mode="iso")` diamonds.
- **Scale Match:** Match `char_rig` `size` to tile width (`16` for `32x16` iso tiles, `32` for `64x32` iso tiles).

## Interactive Clarification Checklist
Confirm concisely with the user:
1. **Tile Footprint & Scale:** `32x16` tiles (`size: 16` or `24`) vs `64x32` tiles (`size: 32`)?
2. **Directions:** Front diagonals only (`se`, `sw`) or all 4 diagonals (`se`, `sw`, `ne`, `nw`)?
3. **Poses:** `idle`, `walk`, `run`, `work`/`attack`?
4. **Ground Shadow (`shadow`):** Include 2:1 ground contact shadow (`true`) or omit (`false`)?
5. **Tile Base Preview:** Render standalone sprite (`true` transparent background) or seated on an `iso_tile` preview?

## JSON Example (32x32 Isometric Unit Facing SE)
```json
{
  "width": 32,
  "height": 32,
  "palette": "cozy24",
  "style": "ext_outline",
  "fps": 8,
  "frames": [
    {"ops": [{"op": "char_rig", "size": 32, "perspective": "iso", "dir": "se", "pose": "walk", "frame": 0, "shirt": "water", "pants": "stone_d", "shadow": true}]},
    {"ops": [{"op": "char_rig", "size": 32, "perspective": "iso", "dir": "se", "pose": "walk", "frame": 1, "shirt": "water", "pants": "stone_d", "shadow": true}]},
    {"ops": [{"op": "char_rig", "size": 32, "perspective": "iso", "dir": "se", "pose": "walk", "frame": 2, "shirt": "water", "pants": "stone_d", "shadow": true}]},
    {"ops": [{"op": "char_rig", "size": 32, "perspective": "iso", "dir": "se", "pose": "walk", "frame": 3, "shirt": "water", "pants": "stone_d", "shadow": true}]}
  ]
}
```
