# AGENTS.md

## Overview
`pixelai-tools` is a **CLI-only** tool designed for AI agents to rapidly and deterministically generate pixel art (sprites, palettes, spritesheets, and animations) from the terminal.

## Core Constraints
- **100% CLI:** Executed directly via CLI (Python). Do **not** build, bundle, or distribute `.exe` binaries.
- **Built-in Help:** Every command and subcommand must provide clear, concise `--help` documentation so agents and users can discover usage without reading source code.
- **GUI Rule (If Applicable):** This project is strictly CLI. If a graphical interface is ever added in the future, all icons must be **SVG**.

## Architecture & Engineering Standards
- **SOLID:**
  - **Single Responsibility:** Separate canvas/pixel operations, palette management, post-processing (outlines, scaling), I/O/exporting, and CLI argument parsing.
  - **Open/Closed:** Design drawing primitives, filters, and exporters so new ones can be added without modifying core engine logic.
  - **Liskov Substitution & Interface Segregation:** Keep exporter and filter interfaces small and interchangeable.
  - **Dependency Inversion:** Core drawing logic must not depend directly on CLI parsing or specific file-system details.
- **DRY:** Never duplicate pixel math, bounds checking, color parsing, or validation logic. Extract shared helpers.
- **KISS:** Keep functions small, deterministic, and easy to test.
