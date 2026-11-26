# Autonomous production implementation checkpoint

## Implemented and tested

- Persistent SQLite tasks, restart-safe ordering, idempotent start and audit events.
- Project-relative evidence files with SHA-256 identity and downstream reopening after changes.
- Content-addressed evidence snapshots preserve previous bytes after working files change; changing the brief reopens tasks without resetting consumed budgets.
- Stage-specific contract fields, six distinct proposal descriptions and eleven-criterion review completeness.
- Every pending task includes category-specific failure checks, a visual inspection protocol and targeted repair instructions; review tasks include the eleven-criterion rubric.
- Nonempty image evidence for construction/review and JSON source evidence for construction.
- Single-frame native PNG construction is rerendered from the submitted fresh source and compared pixel-for-pixel. Reviews must include that exact artifact evidence.
- Declared reviewer-context separation; these declarations are not authenticated host isolation.
- Failed review scores reopen construction and preserve review history and consumed budgets.
- Three consecutive reviews with the same failing criteria reopen structural alternatives; budget-exhaustion diagnostics retain the latest defects.
- Construction/review submission quotas and explicit blocked status on exhaustion.
- Universal manifest validation of texture hashes, actual frame regions, anchors, timing and clip references.
- Exported clip timing traces, explicitly reporting unverified runtime behaviors.
- Reference scene compositor consumes only exported manifests/textures and emits native PNGs plus timing, pivot placement and stable Y-sort traces.
- Approximate silhouette comparison normalized for padding and scale, with reflection checks.
- Empty artwork cannot pass style fidelity checks.
- PNG metadata and Godot exports preserve explicit per-frame durations and named clips; GIF previews preserve holds within GIF timing limits.
- Procedural library included in wheel/sdist builds and resolved from installed packages.
- Named assembly parts with validated parent graphs, inherited offsets, deterministic draw order, material labels and transform-aware exported origins.

## Current limits

The managed queue never approves production. Provenance currently supports self-contained single-frame native PNGs; atlas and GIF construction verification remains pending. Distinct proposal descriptions do not yet establish visible structural diversity. Reviewer declarations do not prove isolated contexts or actual perception. The reference runtime renders pivot placement and sorting but does not yet simulate collision, acting, transition blending or tile seams. These checks remain necessary before enabling release.

## Next implementation priorities

1. Strict renderer capability registry and atlas/animation source-to-image provenance.
2. Versioned semantic part graphs and transform-safe metadata.
3. Host review adapters with artifact-bound observation events.
4. Category-specific proposal images and part-level catalog comparisons.
5. Universal runtime scenes and behavioral traces.
6. Structural generator upgrades, acting and gameplay-state coverage.

See AUTONOMOUS_ROADMAP.md for the complete sequence and benchmark targets.
