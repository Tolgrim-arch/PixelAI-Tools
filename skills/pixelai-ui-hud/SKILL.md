---
name: pixelai-ui-hud
description: Generate pixel art game UI and HUD components — 9-slice dialogue panels, health/mana/stamina bars, multi-state buttons (normal, hover, pressed), heart containers (full, half, empty), and inventory slots using pixelai-tools ui_rig. Use whenever the user asks for UI boxes, health bars, HUD hearts, dialogue frames, inventory grids, or clickable buttons. DO NOT trigger for inventory item icons inside slots (use pixelai-items-icons) or character dialogue portraits (use pixelai-portraits).
---

# pixelai-ui-hud

## Art direction checklist
Use the following design choices to interpret the brief. Use sensible defaults for choices the user leaves open so a single prompt can produce a first asset. Ask one plain-language question only if a missing choice would make the result unusable.
1. **Material / Estilo visual:** ¿De qué material quieres la interfaz: **madera cálida** (estilo granja), **piedra**, **borde dorado**, **pergamino/papel**, o **oscuro/moderno**?
2. **Estados que necesitas:**
   - Si es **botón**: ¿necesitas los 3 estados (**normal**, **al pasar el mouse**, **presionado**)?
   - Si es **corazón**: ¿necesitas **lleno**, **medio** y **vacío**?
   - Si es **barra (vida/maná/energía)**: ¿en qué color y con divisiones o continua?
   - Si es **caja de diálogo / panel**: ¿con relleno sólido por dentro o solo el marco?
3. **Tamaño aproximado:** ¿Pequeño para barra/icono o ancho para cuadro de diálogo?

## Aesthetic Standard & CLI (Self-Contained)
- **Default (`"style": "ext_outline"`):** Lineless Interior + 1px External Outline with crisp top/left specular bevels. Optional `--lineless` for seamless 9-slice Godot/Unity slicing.
- **Render CLI:** `python -m pixelai render - -o ui.png`

## Native size and originality
- Create a new JSON spec for each brief. Never load or present a discarded PNG as a new asset.
- Render panels directly at the final `w`/`h`. Never stretch a small panel PNG across a large container: corners, nails, bevels and runes must remain native pixels.
- For large containers, use `frame_width: 6..12`; compact panels default to 3. Keep `2 * frame_width < min(w, h)` and reserve the central content rectangle for text/icons.
- Themes have native material details: wood grain/nails, stone joints, gold corner inlays, paper folds and dark illuminated runes. `inner_fill:false` leaves content fully transparent while retaining the decorated frame.
- Inspect a fresh render at 1x and integer zoom. Compare different sizes to confirm border thickness changes only when explicitly requested.

## `ui_rig` Reference
- `"op": "ui_rig"`
- `"kind"`: `"panel" | "bar" | "button" | "heart" | "slot"`
- `"theme"`: `"wood" | "stone" | "gold" | "paper" | "dark"`
- `"state"`:
  - `button`: `"normal" | "hover" | "pressed"`
  - `heart`: `"full" | "half" | "empty"`
  - `slot`: `"normal" | "selected"`
- `"fill"`: `0.0..1.0` (for `bar`), `"fill_color"` (palette key or hex), `"segmented"`: `true | false`, `"inner_fill"`: `true | false`
- Panels: `"frame_width": 3..12` (default 3), `"w"`, `"h"` in final native pixels. Components require dimensions of at least 8px; panel borders must leave positive content space.

## JSON Example (Wood RPG Panel + Half Health Bar + Selected Slot)
```json
{
  "width": 64,
  "height": 64,
  "palette": "cozy24",
  "style": "ext_outline",
  "auto_pad": true,
  "ops": [
    {"op": "ui_rig", "x": 4, "y": 4, "w": 56, "h": 24, "kind": "panel", "theme": "wood"},
    {"op": "ui_rig", "x": 4, "y": 32, "w": 40, "h": 10, "kind": "bar", "theme": "stone", "fill": 0.65, "fill_color": "roof"},
    {"op": "ui_rig", "x": 46, "y": 30, "w": 14, "h": 14, "kind": "slot", "theme": "gold", "state": "selected"},
    {"op": "ui_rig", "x": 4, "y": 46, "w": 14, "h": 14, "kind": "heart", "state": "full"},
    {"op": "ui_rig", "x": 18, "y": 46, "w": 14, "h": 14, "kind": "heart", "state": "half"},
    {"op": "ui_rig", "x": 32, "y": 46, "w": 14, "h": 14, "kind": "heart", "state": "empty"}
  ]
}
```
