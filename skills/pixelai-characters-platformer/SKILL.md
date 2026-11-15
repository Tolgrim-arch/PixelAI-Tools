---
name: pixelai-characters-platformer
description: Generate side-view 2D platformer and metroidvania character or creature sprites (idle, walk, run, jump, fall, attack) for Celeste, Hollow Knight, Mario, or Terraria style side-scrollers using pixelai-tools. Use whenever the user asks for side-view platformer sprites facing left/right with jump/fall/attack frames. DO NOT trigger for top-down 4-direction RPGs (use pixelai-characters-topdown or pixelai-creatures-topdown) or isometric 2:1 characters (use pixelai-characters-iso).
---

# pixelai-characters-platformer

## Aesthetic Standard & CLI (Self-Contained)
- **Default (`"style": "ext_outline"`):** Lineless Interior + 1px External Outline (no internal dark lines). Optional `--lineless`.
- **Render CLI:** `python -m pixelai render - -o player.png` (or `.gif --fps 10`, or `--sheet --columns 4 --godot player.tres`).

## Platformer Rules
- **Orientation:** Strictly side-profile (`"dir": "right"` or `"left"`). Usually export `right` only and mirror in-engine (`flip_h`), unless asymmetric gear requires both `left` and `right`.
- **Ground Shadow:** Usually `"shadow": false` in platformers so jump/fall sprites do not carry floating shadows in mid-air.
- **Silhouette Readability:** Keep head/legs/weapons separated on jump/fall/attack poses so action frames read cleanly at high speed.

## Interactive Clarification Checklist
Confirm concisely with the user before exporting full platformer sheets:
1. **Subject & Resolution:** Humanoid (`char_rig` at `16|32|64`) or creature (`animal_rig`) or custom rig?
2. **Facing:** Export `"right"` only (mirror in engine) or both `"left"` and `"right"`?
3. **Action States:** `idle`, `walk`, `run`, `jump`, `fall`, `attack`?
4. **Shadow:** Omit ground shadow (`"shadow": false`, recommended for platformers) or keep it?
5. **Palette & Gear:** Character colors (`skin`, `hair`, `shirt`, `pants`, `tool`)?

## JSON Reference (`perspective: "platformer"`)
- `char_rig`: `"perspective": "platformer"`, `"dir": "right|left"`, `"pose": "idle|walk|run|jump|fall|attack"`, `"shadow": false`
- `animal_rig`: `"perspective": "platformer"`, `"dir": "right|left"`, `"pose": "idle|walk|run|jump|fall"`, `"shadow": false`

## JSON Example (32x32 Side-Scroller Jump & Attack Sequence)
```json
{
  "width": 32,
  "height": 32,
  "palette": "endesga32",
  "style": "ext_outline",
  "fps": 10,
  "frames": [
    {"ops": [{"op": "char_rig", "size": 32, "perspective": "platformer", "dir": "right", "pose": "run", "frame": 0, "shadow": false}]},
    {"ops": [{"op": "char_rig", "size": 32, "perspective": "platformer", "dir": "right", "pose": "jump", "frame": 1, "shadow": false}]},
    {"ops": [{"op": "char_rig", "size": 32, "perspective": "platformer", "dir": "right", "pose": "fall", "frame": 2, "shadow": false}]},
    {"ops": [{"op": "char_rig", "size": 32, "perspective": "platformer", "dir": "right", "pose": "attack", "frame": 2, "shadow": false}]}
  ]
}
```
