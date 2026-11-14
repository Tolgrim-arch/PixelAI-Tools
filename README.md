# pixelai-tools

**CLI-only deterministic pixel art, tileset, isometric architecture, and animation engine for AI agents (Antigravity, Claude Code, Codex).**

## Aesthetic Standard
- **Default (`style: "ext_outline"`):** **Lineless Interior + 1px External Outline**. Internal surfaces use pure color planes, specular bevels (`bevel: true`), eave/ground shadows, and recessed depth (`recessed: true`) with zero internal dark lines, wrapped in a 1px external silhouette outline.
- **Pure Lineless (`--lineless` / `style: "lineless"`):** 100% lineless (no internal or external outlines).

## CLI Commands
```powershell
# Print full LLM agent reference guide & built-in palettes
python -m pixelai.cli guide

# Render single PNG (from file or stdin '-')
python -m pixelai.cli render spec.json -o sprite.png

# Render Pure Lineless
python -m pixelai.cli render spec.json -o sprite_lineless.png --lineless

# Render Animated GIF
python -m pixelai.cli render anim.json -o walk.gif --fps 8

# Render Spritesheet + JSON Metadata + Godot 4 SpriteFrames (.tres)
python -m pixelai.cli render anim.json -o sheet.png --sheet --columns 4 --meta sheet.json --godot sheet.tres

# Inspect PNG metrics (bounding box, margins, color count) + ASCII preview
python -m pixelai.cli inspect sprite.png --ascii
```
