---
name: pixelai-foliage-nature
description: Generate pixel art trees (oak, pine, fruit), bushes, rocks (boulder, mossy, ore), flowers, and 4-stage farm crops (seed, sprout, growing, mature) using pixelai-tools nature_rig. Use whenever the user asks for trees, plants, bushes, boulders, ores, flowers, or farm crops. DO NOT trigger for terrain floor tilesets (use pixelai-tilesets), buildings (use pixelai-buildings-*), or animals (use pixelai-creatures-topdown).
---

# pixelai-foliage-nature

## Mandatory Non-Technical Discovery Protocol (Pause & Ask First)
When the user asks for trees, rocks, plants, or crops, **STOP and ask in simple game terms** before generating (unless already answered):
1. **Variante / Aspecto:**
   - Árboles: ¿frondoso (roble), pino o árbol con frutas?
   - Rocas: ¿piedra normal, con musgo o con veta de mineral/oro?
   - Cultivos: ¿quieres solo la planta madura o las **4 etapas de crecimiento** (semilla, brote, creciendo y lista para cosechar)?
2. **Suelo incluido o imaginario:** ¿Lo vas a colocar sobre un mapa que **ya tiene pasto/tierra dibujada** (`"ground_base": "none"`), o quieres que el sprite incluya su **propio parche de pasto o tierra**?
3. **Sombra:** ¿Incluimos la **sombra debajo** o el juego ya proyecta sombras propias?
4. **Movimiento:** ¿Estático o meciéndose suavemente con el **viento**?

## Aesthetic Standard & CLI (Self-Contained)
- **Default (`"style": "ext_outline"`):** Lineless Interior + 1px External Outline (no internal dark lines). Optional `--lineless`.
- **Render CLI:** `python -m pixelai render - -o tree.png` (or `.gif --fps 6` when `"sway": true`).

## `nature_rig` Reference
- `"op": "nature_rig"`
- `"kind"`: `"tree" | "bush" | "rock" | "flower" | "crop"`
- `"variant"`:
  - `tree`: `"oak" | "pine" | "fruit"`
  - `rock`: `"boulder" | "mossy" | "ore"`
  - `crop`: `"wheat" | "berry" | "carrot"`
- `"stage"`: `0 | 1 | 2 | 3` (for `crop`: `0`=seed, `1`=sprout, `2`=growing, `3`=mature)
- `"sway"`: `true | false` (default `false`; auto-generates 4 wind frames when animated)
- `"shadow"`: `true | false` (default `true`)
- `"ground_base"`: `"none" | "grass" | "soil"` (`"none"` = imaginary ground)

## JSON Example (Swaying Fruit Tree Without Ground Patch)
```json
{
  "width": 32,
  "height": 40,
  "palette": "cozy24",
  "style": "ext_outline",
  "fps": 6,
  "ops": [
    {"op": "nature_rig", "kind": "tree", "variant": "fruit", "sway": true, "shadow": true, "ground_base": "none"}
  ]
}
```
