# COMMERCIAL_ROADMAP.md — Architectural & Aesthetic Evolution Criteria for `pixelai-tools`

## 1. Executive Summary & Core Philosophy
`pixelai-tools` aims to produce **commercial-grade, top-seller itch.io pixel art asset packs** driven by AI coding agents—including **low-reasoning models**—through a deterministic, 100% Python CLI engine.

The bottleneck for superior pixel art is **not** CPU language speed, but **declarative composition, reusable structural systems, physical/stylistic material shading, intelligent post-processing FX, and batch pack orchestration**.

---

## 2. Low-Reasoning Agent Ergonomics ("High-Level Semantics, Zero Math")
Low-reasoning AI models struggle with raw spatial coordinate math (`x: 17, y: 23, rx: 5`) and complex polygon vertices, but excel at declarative intent and semantic composition.

### Design Criteria
- **Intent-Driven Specs:** Agents should specify *what* to build (`archetype`, `material`, `style_profile`, `mood`, `size`, `fx`) while the engine computes golden-ratio proportions, silhouette balance, 2D surface normals, and attachment anchors.
- **Inheritance & Overrides (`extends`):** Any spec or variant must be able to inherit from an existing spec/prefab and override only specific properties:
  ```json
  {
    "id": "golden_apple",
    "extends": "@items/apple_base",
    "material_remap": {"skin": "gold_specular", "leaf": "emerald_crystal"},
    "fx": ["sheen_sweep", "sparkle_orbit", "float_bounce"]
  }
  ```
- **Self-Correcting Guardrails:** Automatic bounding-box padding (`auto_pad`), automatic attachment snapping, and strict pre-render validation with actionable error messages so low-reasoning agents never produce clipped outlines or misaligned parts.

---

## 3. Reusable Structures, Prefabs & Smart Brushes (`library/` & `@imports`)
Currently, `defs` and `stamp` exist locally within a single JSON spec. Commercial production requires cross-file modular reuse.

### Design Criteria
- **Global Prefab Registry (`@namespace/prefab_name`):**
  - Save reusable building blocks once (e.g., `@foliage/oak_leaf_cluster`, `@foliage/pine_needles`, `@architecture/medieval_window`, `@patterns/dragon_scales`, `@weapons/hilts`) and import them across any spec or asset pack.
- **Structure-Aware Smart Stamps & Canopy/Surface Brushes:**
  - When reusing a saved leaf system on a tree crown or a bush, the engine must not merely paste flat stamps.
  - **Depth & Normal Adaptation:** Each stamped cluster must automatically shift its tone ramp index based on its `(x, y, z)` position on the host volume (e.g., top-left canopy clusters receive highlight tones `3–4`, interior/lower clusters receive shadow tones `0–1` plus ambient occlusion at overlap boundaries).
- **Reusable Hatching & Surface Weaves (Tramas):**
  - Parametric, non-noisy cluster patterns (`weave`, `scales`, `brick_course`, `wood_grain`, `fur_tuft`, `chainmail`) that wrap and clip cleanly to the target silhouette (`inside: true`) and obey local lighting zones.

---

## 4. Physical & Stylistic Material Recoloring (e.g., Normal Apple → Golden/Enchanted Apple)
A naive 1-to-1 RGB color swap fails when changing materials because organic fruit skin, polished gold, dark iron, and glowing crystal have completely different light-response curves.

### Design Criteria
- **Tone-Indexed Material Buffers:**
  - Internal rendering should track `(material_slot, tone_index 0..4, surface_normal)` in addition to or prior to final RGBA baking.
- **Material Reflectance Profiles (`reflectance`):**
  - `matte_organic` (soft broad midtones, small highlight, warm shadow shift — e.g., red apple, cloth, soil).
  - `metallic_specular` (high contrast, compressed midtones, sharp bright specular ridge, secondary bounce-light reflection on the shadow edge — e.g., golden apple, armor, coins).
  - `crystalline_translucent` (internal glow/subsurface brightness in lower-right core + sharp white facet highlights — e.g., mana gems, ice).
- **One-Line Material Swap:**
  - Converting a normal apple into a golden apple requires only `"material": "gold_ornate"` (or `"recolor": {"body": "@materials/gold_specular"}`), and the engine automatically upgrades the shading curve, adds the metallic specular ridge, and shifts the selective outline.

---

## 5. Intelligent Post-Processing FX Pipeline (`fx_pipeline` — Reusable Over Any Finished Sprite)
Agents must be able to take **any** finished static sprite, prefab, or multi-frame rig (loaded via spec or PNG) and apply modular, composable, deterministic animation effects to produce smooth GIFs and spritesheets.

### Core Reusable FX Catalog
1. **`sheen_sweep` (Diagonal Specular Glint / Resplandor Dorado o Encantado):**
   - A diagonal highlight bar (`angle: 45`, configurable width, softness, and blend mode `add` / `screen` / `tone_shift`) that sweeps across the opaque pixels of the sprite over `N` frames.
   - **Mask-Strict:** Never bleeds into transparent background pixels or ground shadows; respects the external outline (either stays inside the interior surface or brightens the outline selectively).
   - **Material-Aware:** Boosts intensity on raised/highlighted pixels for an authentic golden/enchanted lustre.
2. **`bounce` / `squash_stretch` (Sub-Pixel & Volume-Preserving Bounce):**
   - Vertical bobbing or ground-impact bounce with optional 1px squash at the lowest frame and 1px stretch at the apex, preserving pixel cluster integrity without mangling 1px details.
3. **`float_bob` (Magical Levitation):**
   - Sinusoidal vertical hover for items, pickups, ghosts, or magic crystals, synchronized with a pulsing ground shadow (shadow shrinks/fades slightly as the object rises).
4. **`sparkle_glint` (Brillitos / Starburst Particles):**
   - Deterministic 4-point pixel star glints (`1px → cross 3px → diamond 5px → fade`) spawned at high-specular anchor points or orbiting the silhouette.
5. **`aura_glow` / `enchanted_pulse`:**
   - Outer or inner pulsing rim light / magical fire / dark miasma around the sprite silhouette with cycle-seamless looping.
6. **`wind_sway` (Shear & Canopy Wave):**
   - Height-graduated horizontal pixel shear + leaf cluster flutter for trees, bushes, grass tiles, banners, and capes.
7. **`hit_flash` / `status_tint`:**
   - Combat damage white/red flash, poison bubble emitter, freeze frost overlay, or burn ember rise.

### Composable FX Stack Syntax
```json
"fx": [
  {"type": "sheen_sweep", "color": "#fff6b8", "width": 4, "blend": "add", "period": 12, "pause_frames": 4},
  {"type": "sparkle_glint", "count": 3, "color": "#ffffff", "seed": 7},
  {"type": "float_bob", "amplitude": 2, "shadow_scale": true}
]
```

---

## 6. Next-Generation Intelligent Outlines & Switchable Style Profiles (`style_profile`)
While `AGENTS.md` establishes `ext_outline` (Lineless Interior + 1px External Outline) and `lineless` as the core aesthetic pillars, the outline engine and shading rules must support deeper intelligence and distinct commercial sub-styles.

### Outline Intelligence Upgrades
- **Light-Directional Selout (`directional_selout: true`):**
  - Top-left external outline pixels (facing the light source) blend more strongly toward a warm mid-dark tone of the adjacent surface, while bottom-right outline pixels (in shadow) deepen toward cool deep ink.
- **Morphological Clean-Up (`clean_jaggies: true`):**
  - Automatic detection and removal of unintentional L-corner doubles, orphan single pixels, and broken stair-step jaggies along curves.
- **Contact & Ground Integration:**
  - Bottom outline pixels resting on a ground plane can optionally soften or merge into the translucent ground shadow for weight and groundedness.

### Switchable Style Profiles (`style_profile`)
Agents can switch the visual target with a single top-level key while keeping the same geometry:
- `cozy_modern` (Default — *Fields of Mistria / Stardew* inspired: lineless interior planes, soft hue-shifted directional selout, translucent ground shadow).
- `16bit_cluster` (*SNES / Chrono / Mana* inspired: high-contrast 4–5 tone clusters, sharp speculars, deep selective outline).
- `crisp_retro` (Tight palette cap, high-readability dark external outline, structured Bayer/cluster dithering).
- `enchanted_hd` (Rich ambient occlusion, strong secondary rim light, additive bloom/sheen support).

---

## 7. Mass Commercial Pack Orchestrator (`pixelai pack` for itch.io)
To build commercial asset packs at scale (Farm Animals, Dungeon Monsters, Town NPCs, Village Houses, Castles, Volcanic/Forest/Beach/Ocean Tilesets), `pixelai-tools` needs a batch pack compiler.

### Design Criteria
- **Parametric Matrix Generation:**
  - Define an asset family once and expand across axes:
    - *Creatures/Monsters:* `species × tier/element (normal, fire, ice, golden) × 4 directions × animations (idle, walk, attack, hurt, death)`.
    - *Buildings/Castles:* `footprint × roof_material × wall_material × season/weather × damage_state`.
    - *Nature/Biomes:* `tree/bush species × growth_stage × 4 seasons × wind_sway GIF`.
    - *Tilesets:* Automatic 47-tile Blob autotile + 16-tile Wang/RPG Maker layout + animated water/lava edges + cliff elevation transitions.
- **Engine-Ready Export Bundle:**
  - Consolidated spritesheets + individual frame PNGs + GIF previews.
  - Runtime JSON manifests (`origin`, `pivot`, `y_sort`, `collision_polygon`, `hitboxes`, `frame_tags`, `attachment_sockets`) compatible with **Godot, Unity, Aseprite, and Tiled**.
- **Automated itch.io Storefront Kit (`pixelai pack showcase`):**
  - Automatically renders the commercial presentation assets required for an itch.io page:
    - Animated cover thumbnail (`630x500` GIF/PNG).
    - Mockup diorama scene combining tilesets, props, characters, and lighting.
    - Categorized showcase sheets (`itch_showcase_sheet.png` and `itch_showcase_banner.gif`) with clean layout, drop shadows, and palette badges.

---

## 8. Prioritized Implementation Roadmap

| Phase | Milestone | Key Deliverables |
| :--- | :--- | :--- |
| **Phase 1** | **Reusable Post-FX Pipeline (`pixelai/fx.py`)** | `sheen_sweep` (diagonal additive/specular bar), `bounce` / `float_bob`, `sparkle_glint`, `aura_glow`, `wind_sway`, applicable to any rendered spec or loaded PNG. |
| **Phase 2** | **Physical Material Recoloring & Smart Remap** | Tone-indexed ramps + reflectance profiles (`matte_organic`, `metallic_specular`, `crystalline`) so 1-line recolors (Apple → Golden Apple) reshape highlights and contrast automatically. |
| **Phase 3** | **Global Prefab Library & Smart Canopy/Pattern Stamps** | `@imports` registry (`library/`), normal-aware canopy/bush leaf cluster stamping, and silhouette-clipped hatching/tramas. |
| **Phase 4** | **Directional Selout, Jaggy Cleanup & Style Profiles** | Light-aware external outline shading, morphological corner cleanup, and `style_profile` presets. |
| **Phase 5** | **Batch Pack Compiler & itch.io Showcase Generator** | `pixelai pack` CLI subcommand for mass multi-variant asset packs, 47-tile autotiles, engine manifests, and itch.io storefront banners. |
