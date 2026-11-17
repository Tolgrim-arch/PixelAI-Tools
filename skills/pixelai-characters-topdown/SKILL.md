---
name: pixelai-characters-topdown
description: Generate top-down 3/4 humanoid character sprites and 4-direction animations (idle, walk, run, work/tool swings) for Stardew Valley, Zelda, RPG Maker, or cozy farming RPGs using pixelai-tools char_rig. Use when asked for top-down RPG heroes, farmers, villagers, or NPCs in 16x16, 32x32, 64x64, or 128x128. DO NOT trigger for animals/creatures (use pixelai-creatures-topdown), side-scroller platformer characters (use pixelai-characters-platformer), isometric characters (use pixelai-characters-iso), or dialogue bust portraits (use pixelai-portraits).
---

# pixelai-characters-topdown

## Aesthetic Standard & CLI (Self-Contained)
- **Default (`"style": "ext_outline"`):** Lineless Interior + 1px External Outline (no internal dark lines). Optional `--lineless`.
- **Render CLI:** `python -m pixelai render - -o char.png` (or `.gif --fps 8`, or `--sheet --columns 4 --meta sheet.json --godot char.tres`).

## Art direction checklist
Use the following design choices to interpret the brief. Use sensible defaults for choices the user leaves open so a single prompt can produce a first asset. Ask one plain-language question only if a missing choice would make the result unusable.
1. **Tamaño y detalle:** ¿Personaje chiquito estilo retro clásico (16x16), tamaño estándar cozy tipo Stardew (32x32), o grande con mucho detalle (64x64)?
2. **Direcciones:** ¿Las 4 direcciones (frente, espalda, izquierda, derecha) o solo una vista?
3. **Animaciones:** ¿Quieto + caminando, o también corriendo y usando herramienta/arma?
4. **Sombra en el piso:** ¿Incluimos sombra suave bajo los pies o la dejamos sin sombra para el motor del juego?
5. **Apariencia y equipo:** ¿Color de pelo, ropa, piel, sombrero o herramienta?
6. **Globitos de emoción:** ¿Necesitas iconos flotantes aparte (corazón, enojo, sueño `ZZZ`, sorpresa)?

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
