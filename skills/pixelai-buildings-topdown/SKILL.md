---
name: pixelai-buildings-topdown
description: Generate top-down 3/4 cozy pixel art buildings, cottages, farmhouses, barns, shops, and village architecture in Stardew Valley, Zelda, or Fields of Mistria style using pixelai-tools building op and ortho bevels. Use whenever the user asks for top-down 3/4 buildings or village structures. DO NOT trigger for isometric 2:1 buildings (use pixelai-buildings-iso), autotiles/ground tilesets (use pixelai-tilesets), or characters/animals (use pixelai-characters-topdown / pixelai-creatures-topdown).
---

# pixelai-buildings-topdown

## Aesthetic Standard & CLI (Self-Contained)
- **Default (`"style": "ext_outline"`):** Lineless Interior + 1px External Outline. Uses pure color planes, shingle/cobble scatter, eave shadows, and recessed windows/doors with ZERO internal dark lines.
- **Render CLI:** `python -m pixelai render - -o building.png` (or `building.gif --fps 6` when `smoke: true`).

## Interactive Clarification Checklist
Confirm concisely with the user:
1. **Building Type (`roof_style`):** `"gable"` (cottage/farmhouse), `"pitched"` (shop/shed), or `"barn"` (red barn/coop)?
2. **Canvas & Footprint:** Compact (`64x64`), medium (`96x96`), or large farmhouse (`128x128`)?
3. **Materials & Colors:** `wall_color` (`cream`, `wood_l`, `stone_l`), `roof_color` (`roof`, `water_d`, `wood`), `trim_color` (`wood`), `foundation_color` (`stone`)?
4. **Architectural Features:** `timber_frame` (`true|false`), `chimney` (`true|false`), animated `smoke` (`true|false` -> export `.gif`), `door` (`true|false`)?
5. **Ground Shadow (`ground_shadow`):** Include base shadow (`true`) or omit (`false`) for engine lighting?

## `building` Op Reference (Top-Down 3/4)
- `"op": "building"`
- Position & Size: `x`, `y`, `w`, `h`, optional `roof_h`, `foundation_h`
- Style & Details: `"roof_style": "gable|pitched|barn"`, `"timber_frame": true`, `"chimney": true`, `"smoke": true`, `"door": true`, `"ground_shadow": true`, `"seed": 42`
- Customizing facades further: Add `rect` (`"bevel": true` / `"recessed": true`), `scatter` (`"pattern": "shingle|brick|cobble|wood"`), or signage props on top after `building`.

## JSON Example (Animated Cozy Farmhouse)
```json
{
  "width": 128,
  "height": 128,
  "palette": "cozy24",
  "style": "ext_outline",
  "fps": 6,
  "frames": [
    {"ops": [{"op": "building", "x": 12, "y": 18, "w": 104, "h": 96, "roof_style": "gable", "wall_color": "cream", "roof_color": "roof", "timber_frame": true, "chimney": true, "smoke": true}]},
    {"ops": [{"op": "building", "x": 12, "y": 18, "w": 104, "h": 96, "roof_style": "gable", "wall_color": "cream", "roof_color": "roof", "timber_frame": true, "chimney": true, "smoke": true}]},
    {"ops": [{"op": "building", "x": 12, "y": 18, "w": 104, "h": 96, "roof_style": "gable", "wall_color": "cream", "roof_color": "roof", "timber_frame": true, "chimney": true, "smoke": true}]},
    {"ops": [{"op": "building", "x": 12, "y": 18, "w": 104, "h": 96, "roof_style": "gable", "wall_color": "cream", "roof_color": "roof", "timber_frame": true, "chimney": true, "smoke": true}]}
  ]
}
```
