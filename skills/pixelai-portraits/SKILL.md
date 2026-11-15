---
name: pixelai-portraits
description: Generate pixel art dialogue bust and waist-up character portraits in Fields of Mistria (90s anime cel-shaded), Stardew Valley, or cozy RPG portrait style using pixelai-tools portrait_rig. Use whenever the user asks for dialogue portraits, character busts, NPC talk sprites, or RPG dialogue boxes. DO NOT trigger for overworld walkable sprites (use pixelai-characters-topdown, pixelai-characters-platformer, or pixelai-characters-iso) or animals (use pixelai-creatures-topdown).
---

# pixelai-portraits

## Aesthetic Standard & CLI (Self-Contained)
- **Default (`"style": "ext_outline"`):** Lineless Interior + 1px External Outline (no dark internal outlines). Optional `--lineless`.
- **Render CLI:** `python -m pixelai render - -o portrait.png`

## Interactive Clarification Checklist
Confirm concisely with the user:
1. **Portrait Style / Preset:**
   - `"style": "mistria"` (`preset: "samurai|farmer"`, `120x160` waist-up 90s-anime style like Fields of Mistria)
   - `"preset": "field_farmer"` (`116x144` cozy field farmer bust)
   - Generic cozy bust (omit `style`/`preset` or `style: "cozy"`, default `64x80`, scalable)
2. **Facing & Gesture:** `face_dir` (`front`, `three_quarter_left`, `three_quarter_right`), `gesture` (`idle`, `wave`, `hip`), `expression` (`smile`, `neutral`)?
3. **Accessories & Details:** `hat` (`true|false`), `scar` (`true|false`, Mistria style), `beard` / custom colors (`skin`, `hair`, `eye_color`, `shirt`, `garment`, `accent`, `hat_color`)?
4. **Background:** Transparent (`fill_background: false`, default for dialogue UI) or solid color card (`fill_background: true`, `background`)?

## `portrait_rig` Reference
- **Mistria Preset:** `{"op": "portrait_rig", "style": "mistria", "preset": "samurai|farmer", "x": 1, "y": 1, "width": 120, "height": 160, "face_dir": "three_quarter_left|three_quarter_right", "hat": false, "scar": true}` (uses `"palette": "mistria_portrait"` or custom colors).
- **Field Farmer Preset:** `{"op": "portrait_rig", "preset": "field_farmer", "x": 0, "y": 0, "hat": true, "expression": "smile|neutral", "face_dir": "three_quarter_left|three_quarter_right"}`
- **Custom Cozy Bust:** `{"op": "portrait_rig", "style": "cozy", "width": 64, "height": 80, "face_dir": "front|three_quarter_left|three_quarter_right", "gesture": "idle|wave|hip", "skin": "#f2c38f", "hair": "#6b3f35", "shirt": "#d9e5d2", "garment": "#704b3b"}`

## JSON Example (Fields of Mistria Style Samurai Portrait)
```json
{
  "width": 122,
  "height": 162,
  "palette": "mistria_portrait",
  "style": "ext_outline",
  "ops": [
    {"op": "portrait_rig", "style": "mistria", "preset": "samurai", "x": 1, "y": 1, "width": 120, "height": 160, "face_dir": "three_quarter_left", "hat": false, "scar": true}
  ]
}
```
