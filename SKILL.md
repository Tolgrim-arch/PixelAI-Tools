---
name: pixelai-tools
description: Generate deterministic pixel art sprites, isometric buildings, 16-tile autotiles, 4-direction character rigs, spritesheets, GIFs, and Godot 4 SpriteFrames (.tres) from the CLI. Use whenever asked to create pixel art, game sprites, tilesets, or animations.
---

# pixelai-tools Skill

## Fresh generation and acceptance
- For a new asset, write a new spec with `"fresh": true`; validate and render with `--fresh`. Do not import an old PNG, inherit an old spec, or copy a rejected design into a new deliverable. Existing files are references only unless the user requests editing an accepted asset.
- Use a new explicit seed for a requested variation and compare silhouettes, not just colors. Keep rejected work separate and never present it as a new result.
- Render UI at its final native `w`/`h`; preserve corner and border pixel thickness. A small panel stretched across a large container is a failed result.
- For top-down humans and creatures, generate and inspect all four views (down/up/left/right), including action poses. A mirrored side view does not supply a front or back view.
- Inspect actual pixels at native size and integer zoom. Tests verify contracts, not artistic excellence. Check material readability, silhouette, anatomy, clipping, transparent shadows, and fruit detail before claiming success.
- This is a deterministic renderer, not a trained image model. Improve generators and regression tests when outputs fail; never imply that changing code trains model weights.

## Quick Start for AI Agents
1. Run `python -m pixelai.cli guide` to view the full JSON DSL and palette keys (`cozy24`, `endesga32`, `sweetie16`, `pico8`, `gameboy`).
2. Render a sprite or animation in a single CLI call via stdin (`-`):
   ```powershell
   python -m pixelai.cli render - -o output.png
   ```

## Aesthetic Standard (Mandatory)
- **Default (`style: "ext_outline"`):** **Lineless Interior + 1px External Outline**. Internal surfaces use pure color planes, specular bevels (`bevel: true`), eave/ground shadows, and recessed depth (`recessed: true`) with **zero internal dark outlines**, wrapped in a 1px external silhouette outline.
- **Pure Lineless (`--lineless` or `"style": "lineless"`):** Zero internal or external outlines.
- **Forbidden:** Never use dark internal outlines.

## Key Capabilities
- **Top-Down 3/4 Cozy Architecture (`building`):** `{"op": "building", "x": 12, "y": 14, "w": 104, "h": 98, "roof_style": "gable|pitched|barn", "wall_color": "cream", "roof_color": "roof", "timber_frame": true, "chimney": true, "smoke": true}` — generates complete farmhouses, cottages, or barns with shingle roofs, gable dormers, timber framing, shutters, flowerboxes, and chimney smoke in 1 op.
- **Isometric 3D Architecture (with Per-Pixel Z-Buffer):** `iso_structure` (per-pixel Z-buffering + depth sorting by `gx + gy, gz`), `iso_box`, `iso_roof` (`pyramid`, `gable_left`, `gable_right`), `iso_wall_rect` (`arch: true`, `recessed: true`).
- **Ortho Bevels & Procedural Textures:** `rect` supports `"bevel": true` and `"recessed": true`; `scatter` supports `"pattern": "noise|brick|shingle|cobble|wood|grass"` with deterministic `density` and `seed`.
- **Organic Primitives & Particles:** `ellipse` (`rx`, `ry`), `bezier` (`points`, `thickness`), and looping `particles` (`smoke`, `leaves`, `rain`, `sparks`).
- **Keyframe Tweening & Multi-Layer Export:** Automatic interpolation via `"keyframes": [{"steps": 4, "ops": [...]}]` and separate layer export via `"layers": [...]` + `--layers-dir <dir>`.
- **Auto-Tilesets (16-tile Wang Bitmask):** `{"op": "autotile", "tile_size": 16, "inner": "water", "outer": "grass", "lip": "soil_d"}`
- **4-Direction Character & Cozy Creature Rigs:**
  - `{"op": "char_rig", "size": 16, "dir": "down|up|left|right", "pose": "idle|walk|work", "frame": 0..3}`
  - `{"op": "animal_rig", "species": "chicken", "dir": "down|up|left|right", "pose": "walk|peck|nest|sleep|surprised|happy|sad|angry|sick"}`
  - `{"op": "emote", "x": 18, "y": 2, "kind": "heart|angry|sweat|zzz|exclamation|sick", "outline": false}`
  - Universal silhouette masks: `"inside": true` (clips internal shading to opaque silhouette) and `"outline": false` (excludes floating emotes/particles/shadows from external outline).
- **Isometric & Ortho Tilemaps:** `{"op": "tilemap", "mode": "iso|ortho", "tile_w": 16, "tile_h": 16, "rows": [...]}`
- **Exporters, Showcase & Introspection:** `.png` (with embedded `pixelai_spec` metadata), `.gif` (`--fps`), Spritesheet + JSON (`--sheet --meta`), Godot 4 `.tres` (`--godot`), Itch.io Showcase (`pixelai showcase <dir> -o showcase.png --scale 4`), `pixelai extract <img.png>`, and multi-frame `pixelai inspect <img.png|anim.gif> --ascii --all-frames`.
