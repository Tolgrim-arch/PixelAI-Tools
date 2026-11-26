# Autonomous pixel art production

Implementation status: foundation started. Managed production approval is deliberately unavailable until artifact verification and isolated host review adapters exist.

## Accepted architecture

Use the host agent for visual reasoning, with separate author, artistic reviewer and contextual reviewer contexts. Cover all 2D pixel art. Export a universal manifest and validate exported artifacts through a reference simulator. Keep basic rendering compatible. Allow per-project art direction and verified extensions. Stop at configured budgets without approving deficient work.

## Implementation sequence and acceptance gates

1. **P0 — Capability contracts:** consolidate operation metadata, reject unknown managed fields, report inactive parameters, test installed distributions, and separate style metrics from artistic judgment. Empty artwork must never pass style comparison. Status: empty artwork guard implemented; remaining work pending.
2. **P1 — Semantic design:** version ProjectBrief, ArtDirection, AssetSpec v2, AssetManifest v1, Review v2, WorkflowTask, ReleaseManifest and ExtensionManifest. Track stable part IDs, materials, structure, anchors and dependencies through transforms. Preserve original-canvas coordinates and explicit atlas offsets. Pending.
3. **P2 — Persistent director:** transactional task scheduling, idempotent next/start, resume, evidence submission, revision tracking, dependency invalidation, budgets and cycle detection. Status: experimental SQLite queue and ordered submissions implemented; artifact validation, revisions, budgets and invalidation pending.
4. **P3 — Visual evidence:** host adapters record separate reviewer contexts and viewed artifact hashes. Require localized observations at native resolution and integer zoom. Each applicable criterion needs both reviewers to score at least 3/4. Missing or conflicting evidence blocks release. Pending.
5. **P4 — Structural search:** six silhouette proposals, at most two developed candidates, whole-asset and per-part catalog comparisons. Normalize translation and padding. Separate legitimate variants from accidental duplication. Reject defects by revision and cause, permitting verified repairs. Pending.
6. **P5 — Generators:** morphology and posture graphs for characters; growth graphs for trunks and roots; building footprints and connected roof volumes; fracture-driven rocks and directional materials; compositional UI ornament grammars and nine-slice contracts. Require visible differences without recoloring or decoration. Pending.
7. **P6 — Acting:** explicit key poses, variable durations, anticipation, contact, recovery, secondary motion and expressive profiles. Track root motion, planted feet, events and interruption transitions. Intentional holds are valid. Pending.
8. **P7 — Full 2D coverage:** functional item parts and states, portrait landmarks and expressions, background composition and depth, illustration focal hierarchy, VFX phases and parallax. Category-specific requirements prevent inappropriate gameplay checks. Pending.
9. **P8 — Exported-artifact simulator:** consume only universal manifests and exported pixels. Verify pivots, collisions, sorting, directions, transitions, background readability, relative scale, gameplay states, legal Wang/Blob adjacency, spatial seams and temporal loops. Emit machine traces and visual evidence. Pending.
10. **P9 — Repair and extension:** localized repair tasks with hypotheses and expected outcomes. Prefer metadata, parts and alternative structures before reusable extensions. Require real host isolation, tests, pinned hashes and rollback; a virtual environment alone is insufficient. Pending.
11. **P10 — Catalog release:** verify coverage, diversity and project consistency. Recheck current hashes and reviews. Publish complete local bundles atomically with sources, manifests, previews and verification reports. Pending.

## Budgets and approval

Default per asset: six structural proposals, two developed candidates, 36 rendered revisions, 24 visual review tasks, two extension attempts. Three unsuccessful corrections of the same defect require a strategy change. Exhaustion retains provisional candidates and blocks approval. Task submissions alone must never produce production approval.

## Verification

Maintain engineering tests for schema validation, transform metadata, deterministic rendering, timings, events, resume, stale reviews, atomic releases and installed-package execution. Include adversarial cases: empty art, ignored parameters, one-pixel changes, recolors, padding, valid silhouette-preserving repair, intentional holds and particles.

Create 120 benchmark briefs across twelve categories, eight development and two reserved briefs per category; run each three times. Target zero approvals with known contract failures, all deterministic seeded defects detected, at least 95% seeded visual defect detection, at most 5% false rejection and at least 90% reserved task completion within budget. Report category results separately.

Final demonstration: an interactive village with two distinct characters, four trees, three buildings, three rocks/resources, six objects, five UI components, a tileset, two portraits, a background and two effects. Exercise movement, direction changes, occlusion, interaction, harvesting, damage and UI. Reference-simulator verification does not imply verification in a specific engine.

## Experimental commands

`pixelai project init DIRECTORY --brief brief.json` requires a nonempty `goal`.

`pixelai workflow start|next|status|resume PROJECT --json` exposes the persistent queue. `pixelai workflow submit PROJECT --task ID --input response.json` requires a nonempty evidence array. Evidence is currently recorded, not authenticated. Completing the queue returns `blocked`, never `approved`.
