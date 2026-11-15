---
name: pixelai-vfx-animations
description: Generate pixel art visual effects, weather loops (rain, snow, falling leaves, sparks, chimney smoke), animated emotes, keyframe-tweened multi-layer GIFs, and motion sequences using pixelai-tools (keyframes, particles, emote, layers, bezier, ellipse). Use whenever the user asks for pixel VFX, particles, animated spells, weather overlays, floating emotes, or multi-layer animation specs. DO NOT trigger for standard creature/character walk cycles unless adding custom VFX or keyframe motion layers.
---

# pixelai-vfx-animations

## Aesthetic Standard & CLI (Self-Contained)
- **Default (`"style": "ext_outline"`):** Lineless Interior + 1px External Outline. **IMPORTANT:** Set `"outline": false` on soft VFX, particles, shadows, and floating emotes so they stay delicate without thick ink borders!
- **Render CLI:**
  - Animated GIF: `python -m pixelai render - -o vfx.gif --fps 10`
  - Separate Layers: `python -m pixelai render - -o sheet.png --layers-dir layers/`

## Interactive Clarification Checklist
Confirm concisely with the user:
1. **Effect Type:** Looping weather/ambient (`smoke`, `leaves`, `rain`, `sparks`), floating `emote` (`heart`, `angry`, `sweat`, `zzz`, `exclamation`, `sick`), or custom `keyframes` tween?
2. **Outline Policy:** Floating soft VFX (`"outline": false`, recommended) vs bold comic impact (`"outline": true`)?
3. **Frame Count & FPS:** Loop length (`4`, `6`, `8` frames) and framerate (`8..12 fps`)?
4. **Layer Separation:** Single composite output or separate `--layers-dir` PNG layers for shader/engine compositing?

## VFX & Animation Reference
- **Looping Particles:** `{"op": "particles", "x": 0, "y": 0, "w": 32, "h": 32, "count": 12, "color": "water_l", "mode": "smoke|leaves|rain|sparks", "size": 1, "seed": 42, "outline": false}`
- **Floating Emote:** `{"op": "emote", "x": 8, "y": 4, "kind": "heart|angry|sweat|zzz|exclamation|sick", "outline": false}`
- **Keyframe Tweening:** `"keyframes": [{"steps": 4, "ops": [...]}, {"steps": 4, "ops": [...]}]` automatically interpolates numeric op coordinates/colors across steps.
- **Multi-Layer Spec:** `"layers": [{"name": "bg", "ops": [...]}, {"name": "fx", "ops": [...]}]` + `--layers-dir out_layers/`.

## JSON Example (Seamless 6-Frame Falling Leaves + Sparks Loop)
```json
{
  "width": 32,
  "height": 32,
  "palette": "cozy24",
  "style": "ext_outline",
  "fps": 10,
  "frames": [
    {"ops": [{"op": "particles", "x": 0, "y": 0, "w": 32, "h": 32, "count": 10, "color": "grass_l", "mode": "leaves", "size": 1, "seed": 7, "outline": false}]},
    {"ops": [{"op": "particles", "x": 0, "y": 0, "w": 32, "h": 32, "count": 10, "color": "grass_l", "mode": "leaves", "size": 1, "seed": 7, "outline": false}]},
    {"ops": [{"op": "particles", "x": 0, "y": 0, "w": 32, "h": 32, "count": 10, "color": "grass_l", "mode": "leaves", "size": 1, "seed": 7, "outline": false}]},
    {"ops": [{"op": "particles", "x": 0, "y": 0, "w": 32, "h": 32, "count": 10, "color": "grass_l", "mode": "leaves", "size": 1, "seed": 7, "outline": false}]},
    {"ops": [{"op": "particles", "x": 0, "y": 0, "w": 32, "h": 32, "count": 10, "color": "grass_l", "mode": "leaves", "size": 1, "seed": 7, "outline": false}]},
    {"ops": [{"op": "particles", "x": 0, "y": 0, "w": 32, "h": 32, "count": 10, "color": "grass_l", "mode": "leaves", "size": 1, "seed": 7, "outline": false}]}
  ]
}
```
