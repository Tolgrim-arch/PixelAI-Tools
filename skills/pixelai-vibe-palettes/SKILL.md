---
name: pixelai-vibe-palettes
description: Translate non-technical visual references, game vibes, and aesthetic inspirations ("estilo Game Boy", "estilo Stardew Valley", "retro 8-bit", "oscuro metroidvania", "pastel cozy", "sin bordes / lineless") into exact pixelai-tools palette, outline style, resolution, and FPS settings. Use whenever a user describes a mood or game reference without knowing pixel art terminology, alongside the matching asset skill. DO NOT use as a replacement for asset creation ops; pair it with the domain skill (creatures, characters, items, buildings, nature, ui).
---

# pixelai-vibe-palettes (Traductor de Estilo para No-Artistas)

Use this lookup table to silently translate vague or game-inspired prompts into technical `pixelai-tools` settings — **never ask the user to pick palette keys or render flags**:

| Si el usuario dice... | `palette` | `style` | Resolución sugerida | FPS |
| :--- | :--- | :--- | :--- | :--- |
| "Cozy", "Stardew Valley", "Fields of Mistria", "granja cálida" | `cozy24` | `ext_outline` | `24x24` / `32x32` (buildings `96..128`) | `8` |
| "Game Boy clásico", "verde retro", "4 colores" | `gameboy` | `ext_outline` | `16x16` | `6` |
| "Retro PICO-8", "indie vibrante", "arcade colorido" | `pico8` | `ext_outline` | `16x16` / `24x24` | `8` |
| "RPG 16-bit", "SNES / GBA", "vibrante pero suave" | `sweetie16` | `ext_outline` | `24x24` / `32x32` | `8..10` |
| "Rico en detalle", "Celeste / Metroidvania", "acción moderna" | `endesga32` | `ext_outline` | `32x32` / `48x48` | `10..12` |
| "Sin líneas negras", "pintado", "moderno suave", "suelo/mapa" | `cozy24` o `sweetie16` | `lineless` (`--lineless`) | Según asset | `8` |
| "Retrato anime 90s / Fields of Mistria" | `mistria_portrait` | `ext_outline` | `120x160` | Estático |

## Reglas para Hablar con Usuarios No-Artistas
1. **Nunca preguntes tecnicismos** ("¿qué paleta?", "¿qué bitmask?", "¿lineless o ext_outline?", "¿auto_pad?"). Tradúcelos tú usando esta tabla.
2. **Traduce estilo a preguntas de juego:**
   - En lugar de *"¿quieres ext_outline o lineless?"*, pregunta: *"¿Lo prefieres con un borde definido tipo dibujo clásico o sin bordes para que se mezcle suave?"*
   - En lugar de *"¿qué FPS y resolución?"*, pregunta: *"¿Es para un juego retro chiquito o con más detalle?"*
3. **Siempre aplica `"auto_pad": true`** cuando el sprite sea personalizado para evitar bordes cortados sin molestar al usuario.
