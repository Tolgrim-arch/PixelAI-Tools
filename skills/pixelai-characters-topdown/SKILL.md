---
name: pixelai-characters-topdown
description: Generate top-down 3/4 humanoid character sprites and 4-direction animations (idle, walk, run, work/tool swings) for Stardew Valley, Zelda, RPG Maker, or cozy farming RPGs using pixelai-tools char_rig. Use when asked for top-down RPG heroes, farmers, villagers, or NPCs in 16x16, 32x32, 64x64, or 128x128. DO NOT trigger for animals/creatures (use pixelai-creatures-topdown), side-scroller platformer characters (use pixelai-characters-platformer), isometric characters (use pixelai-characters-iso), or dialogue bust portraits (use pixelai-portraits).
---

# pixelai-characters-topdown

## Aesthetic Standard & CLI (Self-Contained)
- **Default (`"style": "ext_outline"`):** Lineless Interior + 1px External Outline (no internal dark lines). Optional `--lineless`.
- **Render CLI:** `python -m pixelai render - -o char.png` (or `.gif --fps 8`, or `--sheet --columns 4 --meta sheet.json --godot char.tres`).

## Interactive Clarification Checklist
Before generating full sheets, confirm concisely with the user:
1. **Resolution (`size`):** `16` (retro/Stardew tiny), `32` (detailed cozy RPG), `64`, or `128`?
2. **Directions (`dir`):** All 4 directions (`down`, `up`, `left`, `right`)?
3. **Animation Set (`pose`):** `idle` + `walk` baseline, or also `run` and `work` (tool swing)?
4. **Ground Shadow (`shadow`):** Include soft ground shadow (`true`) or omit (`false`) if engine handles shadows?
5. **Customization & Tool:** Colors (`skin`, `hair`, `shirt`, `pants`, `shoes`, `hat`), and tool/weapon colors (`tool`, `handle`) for `work`?
6. **Floating Emotes (`emote`):** Need separate/attached emotes (`heart`, `angry`, `sweat`, `zzz`, `exclamation`, `sick`) with `"outline": false`?

## `char_rig` Reference (Top-Down)
- `"op": "char_rig"`, `"perspective": "topdown"`
- `"size"`: `16 | 32 | 64 | 128`
- `"dir"`: `"down" | "up" | "left" | "right"`
- `"pose"`: `"idle" | "walk" | "run" | "work"` (`frame`: `0..3`)
- `"shadow"`: `true | false` (default `true`)
- **Colors:** `skin`, `hair`, `eye`, `shirt`, `pants`, `shoes`, `hat` (optional), `tool`, `handle`, `shadow_color`.
- **Custom Overlays:** Layer hats, scarves, or backpacks after `char_rig` using `"inside": true` (for shading/patterns) or normal ops on the same canvas.

## JSON Example (32x32 Farmer 4-Frame Walk Right, No Shadow)
```json
{
  "width": 32,
  "height": 32,
  "palette": "cozy24",
  "style": "ext_outline",
  "fps": 8,
  "frames": [
    {"ops": [{"op": "char_rig", "size": 32, "dir": "right", "pose": "walk", "frame": 0, "hat": "wheat", "shirt": "roof", "pants": "water_d", "shadow": false}]},
    {"ops": [{"op": "char_rig", "size": 32, "dir": "right", "pose": "walk", "frame": 1, "hat": "wheat", "shirt": "roof", "pants": "water_d", "shadow": false}]},
    {"ops": [{"op": "char_rig", "size": 32, "dir": "right", "pose": "walk", "frame": 2, "hat": "wheat", "shirt": "roof", "pants": "water_d", "shadow": false}]},
    {"ops": [{"op": "char_rig", "size": 32, "dir": "right", "pose": "walk", "frame": 3, "hat": "wheat", "shirt": "roof", "pants": "water_d", "shadow": false}]}
  ]
}
```
