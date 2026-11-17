---
name: pixelai-items-icons
description: Generate pixel art RPG items, inventory icons, potions, swords, shields, chests, gems, keys, coins, and food using pixelai-tools item_rig. Use whenever the user asks for item icons, loot drops, weapons, potions, chests, gems, keys, or inventory sprites. DO NOT trigger for HUD bars/panels/hearts (use pixelai-ui-hud), trees/crops/rocks (use pixelai-foliage-nature), or characters/creatures (use pixelai-characters-* / pixelai-creatures-topdown).
---

# pixelai-items-icons

## Art direction checklist
Use the following design choices to interpret the brief. Use sensible defaults for choices the user leaves open so a single prompt can produce a first asset. Ask one plain-language question only if a missing choice would make the result unusable.
1. **Orientación:** ¿La quieres recta en **vertical** (ej. frasco o espada parada) o **inclinada en diagonal** a 45° (estilo clásico de inventario RPG)?
2. **Dónde se usará:** ¿Es para un **icono de inventario/menú** (sin sombra debajo) o **tirada en el suelo del mapa** para recoger (con sombra en el piso)?
3. **Detalles del objeto:**
   - Si es **poción**: ¿de qué color es el líquido (roja vida, azul maná, verde veneno) y qué tan llena está (llena, a la mitad, casi vacía)?
   - Si es **cofre**: ¿lo quieres cerrado, abierto, o ambos estados?
   - Si es **espada/llave/gema**: ¿de qué material o color principal?
4. **Animación:** ¿La quieres **estática** o con un **destello/brillo animado**?

*(Never ask technical questions like JSON op names, bitmasks, or hex codes unless the user asks.)*

## Aesthetic Standard & CLI (Self-Contained)
- **Default (`"style": "ext_outline"`):** Lineless Interior + 1px External Outline (no internal dark lines). Optional `--lineless`.
- **Render CLI:** `python -m pixelai render - -o item.png` (or `.gif --fps 6` for animated shine).
- **Safe Margins:** Use top-level `"auto_pad": true` if placing large icons near canvas edges.

## `item_rig` Reference
- `"op": "item_rig"`
- `"kind"`: `"potion" | "sword" | "shield" | "chest" | "gem" | "key" | "coin" | "apple"`
- `"orientation"`: `"vertical" | "diagonal"` (applies to `potion`, `sword`, `key`)
- `"size"`: `16 | 24 | 32` (default `24`)
- `"color"`, `"secondary_color"`, `"cork_color"` (palette key or hex)
- `"fill_level"`: `0.0..1.0` (for `potion`, default `0.78`)
- `"state"`: `"closed" | "open"` (for `chest`)
- `"shine"`: `true | false` (default `true`)
- `"shadow"`: `true | false` (default `false` for inventory icons; `true` for world loot drops)

## JSON Example (Diagonal Health Potion, Inventory Ready)
```json
{
  "width": 24,
  "height": 24,
  "palette": "cozy24",
  "style": "ext_outline",
  "auto_pad": true,
  "ops": [
    {"op": "item_rig", "kind": "potion", "orientation": "diagonal", "size": 24, "color": "roof", "secondary_color": "water_l", "fill_level": 0.8, "shine": true, "shadow": false}
  ]
}
```
