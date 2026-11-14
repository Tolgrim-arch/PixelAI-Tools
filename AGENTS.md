# AGENTS.md

## Overview & Primary Mission
`pixelai-tools` is a **CLI-only** tool currently under active development and intense polishing, built specifically so that AI coding agents (Claude, ChatGPT/Codex, Google Antigravity/Gemini) can generate high-grade pixel art (sprites, palettes, spritesheets, and animations) for the user from a **single prompt**.

**Your sole and absolute priority as the agent working on this repository is to elevate, refine, and perfect `pixelai-tools`.**

## Relentless Self-Correction & Tool Evolution Protocol
- **Brutally Meticulous Auditing:** Dig critically and exhaustively into the codebase and generated outputs. Identify every flaw, limitation, or missing primitive that prevents sprites and animations from looking aesthetically superior, and fix it immediately in the tool itself.
- **User Generation Requests = Live Diagnostics:** Whenever the user asks you to generate a sprite or animation during development, treat that request primarily as a **stress test for `pixelai-tools`**. Prioritize uncovering every error, aesthetic defect, or workflow friction encountered during generation, and immediately patch `pixelai-tools` at the root cause so that class of failure can never happen again.
- **Instant Historical Error Resolution:** Any mistake or aesthetic shortcoming made in previous sprite/animation requests must be analyzed and resolved directly in the engine with extreme precision (better bevels, cleaner silhouettes, smarter shading/anti-aliasing/sub-pixel animation helpers, stricter validation, etc.).
- **Zero Workarounds:** Never work around a limitation of `pixelai-tools` by writing ad-hoc one-off scripts. If the tool limits you or produces subpar art, upgrade the tool.

## Git & GitHub Workflow (Mandatory)
- **Repository:** https://github.com/Tolgrim-arch/pixelai-tools
- **Continuous Sync:** Commit, push, open Pull Requests, and merge **constantly** throughout development to keep the remote repository up to date with every improvement.
- **Required Co-Author Trailers:** Every single commit message and Pull Request body **must** include the following trailers at the end:
  ```text
  Co-authored-by: Claude <noreply@anthropic.com>
  Co-authored-by: Codex <noreply@openai.com>
  ```

## Core Constraints
- **100% CLI:** Executed directly via CLI (Python). Do **not** build, bundle, or distribute `.exe` binaries.
- **Built-in Help:** Every command and subcommand must provide clear, concise `--help` documentation so agents and users can discover usage without reading source code.
- **GUI Rule (If Applicable):** This project is strictly CLI. If a graphical interface is ever added in the future, all icons must be **SVG**.
- **Aesthetic Standard (Mandatory):**
  - **Default (`style: "ext_outline"`):** **Lineless Interior + External Outline Only**. Internal surfaces must use pure color planes, specular bevels (`bevel: true`), eave/ground shadows, and recessed depth (`recessed: true`) with **zero internal dark outlines**, wrapped in a 1px external silhouette outline.
  - **Optional (`style: "lineless"` / `--lineless`):** **Pure Lineless** (zero internal or external outlines), used when requested by the user.
  - **Forbidden:** Internal + external dark outlines are permanently discarded for aesthetic reasons.

## Architecture & Engineering Standards
- **SOLID:**
  - **Single Responsibility:** Separate canvas/pixel operations, palette management, post-processing (outlines, scaling), I/O/exporting, and CLI argument parsing.
  - **Open/Closed:** Design drawing primitives, filters, and exporters so new ones can be added without modifying core engine logic.
  - **Liskov Substitution & Interface Segregation:** Keep exporter and filter interfaces small and interchangeable.
  - **Dependency Inversion:** Core drawing logic must not depend directly on CLI parsing or specific file-system details.
- **DRY:** Never duplicate pixel math, bounds checking, color parsing, or validation logic. Extract shared helpers.
- **KISS:** Keep functions small, deterministic, and easy to test.
