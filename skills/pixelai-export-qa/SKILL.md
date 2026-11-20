---
name: pixelai-export-qa
description: Export pixelai-tools spritesheets, JSON metadata, Godot 4 SpriteFrames (.tres), Itch.io showcase banners, and perform mandatory visual/metric QA inspection (pixelai inspect, pixelai extract, pixelai showcase). Use whenever the user asks to export to Godot 4, pack spritesheets, inspect or fix pixel art defects (clipped outlines, island artifacts, duplicate frames), extract embedded specs from PNGs, or generate showcase contact sheets. DO NOT trigger for creating brand-new sprites from scratch without export/QA tasks.
---

# pixelai-export-qa

## Mandatory QA Loop After Every Generation
Before delivering any sprite or animation, run inspection and verify metrics:
```powershell
python -m pixelai inspect output.png --ascii
python -m pixelai inspect anim.gif --ascii --all-frames
```
Check these exact invariants:
- `islands`: `1` for connected single characters/buildings (no detached floating stray pixels unless floating emotes/particles).
- `min_margins`: `>= 1` on all sides (`top`, `right`, `bottom`, `left`) when using `ext_outline`, so the 1px external outline is never clipped by canvas edges.
- `duplicate_frames`: `0` on animated loops.
- `unique_colors`: stays concise and readable (no accidental color noise).

Metrics only detect technical defects. They never establish commercial quality.
For anything described as sellable, premium, production-ready, or approved, run:

```powershell
python -m pixelai qa output.png --template reviews/output.review.json
# A different reviewer inspects 1x and integer zoom, completes every field, then:
python -m pixelai qa output.png --review reviews/output.review.json --catalog reviews/catalog.json --record
```

Exit code `0` means all eleven user-facing criteria have an evidence-backed pass
and the delivery contract is satisfied. `1` is rejected; `2` needs review. The
review must name a professional comparison source, identify generator and a
different reviewer, record native and integer-zoom inspection, and provide
substantive evidence for professional quality, readability, clustering, color and
lighting, materials, specialized design, artistic detail, originality,
consistency, technical integrity, and game readiness. A clean `inspect` result
cannot convert `needs_review` into approval.

Record every rejected commercial candidate in the catalog before iteration.
Changing filename, metadata, or transparent padding does not make rejected pixels
new. Preserve the failed image/spec with a `_before` suffix when it is useful for
root-cause comparison. Never overwrite review evidence.

## Export Commands
- **Spritesheet + JSON Metadata + Godot 4 `SpriteFrames` (`.tres`):**
  ```powershell
  python -m pixelai render spec.json -o sheet.png --sheet --columns 4 --meta sheet.json --godot sheet.tres --fps 8
  ```
- **Itch.io Showcase / Contact Sheet (4x nearest-neighbor):**
  ```powershell
  python -m pixelai showcase assets_dir/ -o showcase.png --scale 4
  ```
- **Extract an explicitly approved PNG for a requested edit (`pixelai_spec` metadata):**
  ```powershell
  python -m pixelai extract sprite.png
  ```
  New artwork must use `fresh:true` and `--fresh`; never inherit a rejected candidate.

## Interactive Clarification Checklist
Confirm concisely when packaging for a game engine:
1. **Target Engine:** Godot 4 (`.tres` + `.png` sheet), Unity/Generic (`.png` + `--meta` JSON), or animated `.gif` preview?
2. **Grid Layout:** Fixed `--columns` count and playback `--fps`?
3. **Marketing Asset:** Generate an upscaled Itch.io `showcase` banner (`--scale 4` or `6`)?
