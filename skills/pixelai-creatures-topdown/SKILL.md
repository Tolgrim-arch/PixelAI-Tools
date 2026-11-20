---
name: pixelai-creatures-topdown
description: Generate top-down 3/4 cozy farm animals and creatures (chickens, hens, cows, livestock, pets) in Stardew Valley, Harvest Moon, or Fields of Mistria style using pixelai-tools animal_rig. Use whenever the user asks for top-down 4-direction animal sprites, walking/pecking/grazing/sleeping farm creatures, or cozy creature asset packs. DO NOT trigger for human characters (use pixelai-characters-topdown), side-scroller platformer animals (use pixelai-characters-platformer), isometric animals (use pixelai-characters-iso), or dialogue portraits (use pixelai-portraits).
---

# pixelai-creatures-topdown

## Aesthetic Standard & CLI (Self-Contained)
- **Default (`"style": "ext_outline"`):** Lineless Interior + 1px External Outline (no internal dark lines). Optional `--lineless`.
- **Render CLI:** `python -m pixelai render - -o out.png` (or `.gif --fps 8`, or `--sheet --columns 4 --godot out.tres`).
- **Full Pack Shortcut:** `python -m pixelai pack <chicken|cow> -o pack_dir/ --variant <variant>`

## Art direction checklist
Use the following design choices to interpret the brief. Use sensible defaults for choices the user leaves open so a single prompt can produce a first asset. Ask one plain-language question only if a missing choice would make the result unusable.
1. **Direcciones:** ¿La quieres mirando hacia las 4 direcciones (frente, espalda, izquierda y derecha) o solo de lado?
2. **Animaciones:** Además de estar quieta (`idle`) y caminar (`walk`), ¿quieres que corra, haga acciones (picotear, pastar, dormir en el nido) o muestre reacciones (feliz, sorprendida, enojada, triste, enferma)?
3. **Sombra debajo:** ¿Le incluimos su sombra en el suelo o tu juego ya dibuja sombras aparte?
4. **Globitos de emoción:** ¿Quieres globitos arriba (como `ZZZ` al dormir, corazón o signo de sorpresa) o prefieres el animal limpio sin iconos flotantes?
5. **Suelo imaginario o dibujado (al picotear/pastar):** ¿Quieres que dibuje granos/pastito en el suelo frente al pico, o que picotee sobre el suelo imaginario porque tu mapa ya tiene pasto?
6. **Nido dibujado o imaginario (al dormir/anidar):** ¿Quieres que incluya un nido de paja debajo o que duerma sin nido porque el mapa ya lo tiene?
7. **Color / Raza:** Gallina (`white|brown|golden|dark`), vaca (`holstein|brown|cream|dark`) u otro color?

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

## Four-direction acceptance
- Default to a complete down/up/left/right set unless the user requests one view. One operation produces one direction; explicitly generate all four.
- Inspect the contact sheet: front and back must differ; left and right must preserve the requested facing in every action, including jump/surprised.
- Create fresh specs. Do not use discarded sheets as a new source. Check body proportions and animation contacts at native resolution before delivery.
- Built-in species are only chicken and cow. Other names raise an error; create an original primitive-based creature spec for unsupported species. Do not substitute a chicken.
