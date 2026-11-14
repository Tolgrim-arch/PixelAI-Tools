# Changelog

All notable changes to `pixelai-tools` are documented in this file.

## [0.7.1] - 2026-11-14
### Fixed
- **Isometric Auto-Snapping (`iso.py`):** Roofs, doors, windows, and chimneys automatically snap to their parent box/roof geometry, preventing floating roofs or misplaced openings.
- **Shadow Layer Ordering (`runner.py`):** Keyframe/frame shadow ellipses merge into the background layer so foreground structures are never buried.

## [0.7.0] - 2026-11-14
### Added
- **Hue-Shifted Color Ramps (`color.py`):** Consolidated `darken()` (shifts shadows toward cool indigo/violet) and `brighten()` (shifts highlights toward warm golden sunlight) + `nearest_palette_color()`, eliminating duplicate color math across modules (DRY).
- **Per-Pixel Z-Buffer (`canvas.py`, `iso.py`):** Added `z_buffer` to `Canvas` and per-pixel depth emission in `iso_tile`, `iso_box`, and `iso_structure` (`use_zbuffer: true`), solving Painter's Algorithm sorting artifacts on intersecting L-shaped walls and bridges.
- **Organic Primitives (`ellipse`, `bezier`):** Added midpoint ellipse rasterization (`rx`, `ry`) and de Casteljau Bezier curves (`points`, `thickness`) for shadows, arches, vines, and cables.
- **Keyframe Tweening & Deterministic Particles:** Added automatic keyframe interpolation (`"keyframes": [{"steps": N, "ops": [...]}]`) and seamlessly looping particle emitters (`"op": "particles"`, modes: `smoke`, `leaves`, `rain`, `sparks`).
- **Multi-Layer Rendering & Export (`layers`, `--layers-dir`):** Specs can define `"layers": [{"name": "bg", ...}, {"name": "fg", ...}]` to composite automatically or export separate transparent PNG layers via `--layers-dir`.

## [0.6.0] - 2026-11-14
### Added
- **PNG Spec Embedding & Extraction:** Every rendered `.png` embeds its source JSON spec in `tEXt` metadata (`pixelai_spec`). Added `pixelai extract <image.png>` to recover specs from any generated PNG.
- **Spec Inheritance (`extends`) & `load_png`:** Child specs can inherit `palette`, `defs`, and `ops` from an existing `.png` or `.json` file, or composite cropped regions from external PNGs.
- **Rotated Stamps:** `stamp` now supports `angle` (inverse nearest-neighbor rotation) and `pivot: [px, py]`.
- **Multi-Resolution `char_rig`:** Supports native `size` (16, 32, 64, 128+) with proportional detail and direction-coherent `work` animations (`down`, `up`, `left`, `right`).

### Fixed
- **Clean Transparent GIFs:** `export_gif` now quantizes frames to indexed `P` mode with index `0` reserved for transparency (`transparency=0, disposal=2`).

## [0.5.0] - 2026-11-14
### Added
- **16-Tile Wang Autotiler (`op: "autotile"`):** Generates seamless 4×4 bitmask transition atlases.
- **4-Direction Character Rig (`op: "char_rig"`):** Parametric character generator (`down`, `up`, `left`, `right`; `idle`, `walk`, `work`).
- **Isometric Tilemaps:** `tilemap` now supports `mode: "iso"` with automatic back-to-front projection.
- **Godot 4 Export (`--godot <file.tres>`):** Generates `SpriteFrames` `.tres` resources directly.
- **Terminal Inspector (`pixelai inspect <img.png> --ascii`):** Outputs bounding box, margins, color count, and ASCII preview.
- **`SKILL.md` & `.gitignore`:** Plug-and-play agent integration.

## [0.4.0] - 2026-11-14
### Changed
- **Mandatory Aesthetic Standard:** `ext_outline` (Lineless Interior + 1px External Outline) is now the default style; `--lineless` / `"style": "lineless"` renders Pure Lineless. Internal dark outlines (`edge`/`ridge`) are permanently disabled.
### Added
- Specular bevels (`bevel: true`), ground contact shadows (`ground_shadow`), recessed wall openings (`recessed: true`), and `drop_shadow` filter.

## [0.3.0] - 2026-11-14
### Added
- **`iso_structure`:** Automatic 3D depth-sorted (`gx + gy, gz`) isometric composition.
- **Roof Eave Shadows (`eave_shadow`)** and **Arched/Framed Walls (`arch: true`)**.
- **Selective Outlining (`selout: true`)**, `auto_pad`, and CLI border-clipping `[WARN]` diagnostics.

## [0.2.0] - 2026-11-14
### Added
- Built-in curated palettes (`pico8`, `gameboy`, `sweetie16`, `endesga32`, `cozy24`) + `palette_ext`.
- `grid` (2D ASCII pixel maps), `dither`, `scatter` (`noise`, `brick`, `wood`, `grass`), `stamp`, `iso_box`, `iso_roof`, `iso_wall_rect`.
- Multi-frame `.gif` and spritesheet (`.png` + `.json`) export, plus `pixelai guide`.

## [0.1.0] - 2026-11-13
### Added
- Initial CLI MVP (`pixelai render`) with `Canvas` primitives (`pixel`, `line`, `rect`, `circle`, `fill`, `mirror_x`, `mirror_y`), `outline`, `scale`, and PNG export.
