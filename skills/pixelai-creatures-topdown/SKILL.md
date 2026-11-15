---
name: pixelai-creatures-topdown
description: Generate top-down 3/4 cozy farm animals and creatures (chickens, hens, cows, livestock, pets) in Stardew Valley, Harvest Moon, or Fields of Mistria style using pixelai-tools animal_rig. Use whenever the user asks for top-down 4-direction animal sprites, walking/pecking/grazing/sleeping farm creatures, or cozy creature asset packs. DO NOT trigger for human characters (use pixelai-characters-topdown), side-scroller platformer animals (use pixelai-characters-platformer), isometric animals (use pixelai-characters-iso), or dialogue portraits (use pixelai-portraits).
---

# pixelai-creatures-topdown

## Aesthetic Standard & CLI (Self-Contained)
- **Default (`"style": "ext_outline"`):** Lineless Interior + 1px External Outline (no internal dark lines). Optional `--lineless`.
- **Render CLI:** `python -m pixelai render - -o out.png` (or `.gif --fps 8`, or `--sheet --columns 4 --godot out.tres`).
- **Full Pack Shortcut:** `python -m pixelai pack <chicken|cow> -o pack_dir/ --variant <variant>`

## Interactive Clarification Checklist (Ask Before Multi-Asset Export)
When the user requests a top-down animal (e.g., *"quiero una gallina que picotee el suelo estilo Stardew Valley"*), establish sensible defaults (`4 directions`, `idle + walk`, `shadow: true`) and **concisely ask the user to confirm these exact details**:
1. **Directions:** All 4 directions (`down`, `up`, `left`, `right`) or only side/front?
2. **Core + Extra Poses:** Do you want `idle` + `walk` as baseline, plus `run`, actions (`peck` / `graze` / `nest` / `lie` / `sleep`), or emotional reactions (`surprised`, `happy`, `sad`, `angry`, `sick`)?
3. **Ground Shadow (`"shadow"`):** Include the soft ground shadow ellipse (`true`) or omit it (`false`) if your game engine draws dynamic shadows?
4. **Floating Emotes (`"emotes"`):** Include pixel emotes (`zzz`, `heart`, `angry`, `sweat`, `sick`, `exclamation`) (`true`) or keep the sprite pure (`false`)?
5. **Ground Interaction (`"ground_prop"` for `peck` / `graze`):** Should the sprite draw physical `"seeds"` or `"grass"` blades on the ground, or `"none"` (imaginary grass/ground because your tilemap already has grass)?
6. **Sleep / Nest Surface (`"nest_prop"` for `nest` / `sleep`):** Draw a woven straw nest beneath the creature (`true`) or omit it (`false`, imaginary nest because the map already has a nest)?
7. **Breed / Color Variant:** Chicken (`white|brown|golden|dark`), Cow (`holstein|brown|cream|dark`), or custom hex/palette colors (`body`, `shade`, `deep_shade`)?

## `animal_rig` Reference (Top-Down)
- **Species:** `"chicken"` (native `24x24` grid), `"cow"` (native `32x32` grid).
- **Directions (`dir`):** `"down"` (front), `"up"` (back), `"left"`, `"right"`.
- **Poses (`pose`):**
  - Core: `"idle"` (4f), `"walk"` (4f), `"run"` (4f)
  - Actions: `"peck"` (6f), `"graze"` (6f), `"nest"` (4f), `"lie"` (4f), `"sleep"` (4f)
  - Reactions: `"surprised"` (4f), `"happy"` (4f), `"sad"` (4f), `"angry"` (4f), `"sick"` (4f)
- **Scene-Integration Flags:**
  - `"perspective": "topdown"`
  - `"shadow": true|false` (default `true`)
  - `"emotes": true|false` (default `true`)
  - `"ground_prop": "auto"|"grass"|"seeds"|"none"` (`"none"` = imaginary grass/ground)
  - `"nest_prop": true|false` (`false` = imaginary nest)

## JSON Example (Chicken Pecking Imaginary Grass, No Shadow)
```json
{
  "width": 24,
  "height": 24,
  "palette": "cozy24",
  "style": "ext_outline",
  "fps": 10,
  "frames": [
    {"ops": [{"op": "animal_rig", "species": "chicken", "variant": "brown", "dir": "right", "pose": "peck", "frame": 0, "shadow": false, "ground_prop": "none"}]},
    {"ops": [{"op": "animal_rig", "species": "chicken", "variant": "brown", "dir": "right", "pose": "peck", "frame": 1, "shadow": false, "ground_prop": "none"}]},
    {"ops": [{"op": "animal_rig", "species": "chicken", "variant": "brown", "dir": "right", "pose": "peck", "frame": 2, "shadow": false, "ground_prop": "none"}]},
    {"ops": [{"op": "animal_rig", "species": "chicken", "variant": "brown", "dir": "right", "pose": "peck", "frame": 3, "shadow": false, "ground_prop": "none"}]},
    {"ops": [{"op": "animal_rig", "species": "chicken", "variant": "brown", "dir": "right", "pose": "peck", "frame": 4, "shadow": false, "ground_prop": "none"}]},
    {"ops": [{"op": "animal_rig", "species": "chicken", "variant": "brown", "dir": "right", "pose": "peck", "frame": 5, "shadow": false, "ground_prop": "none"}]}
  ]
}
```
