"""Actionable inspection and repair instructions emitted with every task."""

from pixelai.quality import CRITERIA


DOMAIN_CHECKS = {
    "human": ["Compare body proportions without clothing or recoloring; require the requested morphology to read at native size.", "Inspect all required views for identity, accessory handedness, foot contacts and tool grip."],
    "creature": ["Compare anatomical graphs and locomotion rather than accepting the same biped with new ears.", "Check weight support, joint reach and species-specific features through all actions."],
    "vegetation": ["Hide crowns and compare trunk bends, forks and roots; different foliage cannot excuse repeated trunks.", "Check species, growth and harvest states at native size; wind must preserve the ground anchor."],
    "building": ["Hide materials and ornament; compare footprints, connected masses and roof construction. Use architecture massing_only and structure --full; inspect architecture_comparisons alongside silhouettes.", "Check entrances, roof intersections, ground footprint and front/back occlusion in context. Different windows or roof colors do not resolve repeated building composition."],
    "rock": ["Compare silhouette and facet topology, not noise seeds; deposits must follow and intersect stone structure.", "Check whether moss, ore and stone remain distinguishable at native size."],
    "item": ["Identify the item without its label and check functional parts, silhouette and material cues.", "Verify required open, closed, equipped, consumed or damaged states remain the same identity."],
    "material": ["Inspect macrostructure, medium planes and restrained accents; noise is not material structure.", "Inspect a large repeated field if seamless repetition is promised; a bounded swatch proves no seam contract."],
    "tile": ["Inspect every legal edge and corner neighborhood, plus a wide mosaic for visible repetition.", "Check spatial seams at every animation phase and the last-to-first temporal join."],
    "ui": ["Inspect the complete layout for focal hierarchy and decorative rest areas; repeated motifs require a purpose.", "Test normal, hover, pressed, selected, disabled and focus where required; preserve corners, text space and border thickness at all target sizes."],
    "portrait": ["Compare landmarks and facial proportions across expressions and orientations.", "Check that gestures and expressions alter acting while preserving recognizable identity."],
    "background": ["Check focal hierarchy, depth planes and traversable space using the actual character scale.", "Place interactive objects over the background and check that texture and contrast do not hide them."],
    "illustration": ["Inspect focal hierarchy, mass balance and detail rhythm at the intended viewing scale.", "Check that lighting, material cues and anatomy support the subject rather than merely satisfying raster metrics."],
    "vfx": ["Inspect anticipation, action, impact and dissipation as a complete temporal silhouette.", "Check readable direction and gameplay meaning over actual backgrounds; do not let glow hide contact or targets."],
}

RUNTIME_CHECKS = [
    "Pivot, ground anchor and sort origin must be explicit and stable through frames and atlas extraction.",
    "Collision, hit, hurt and interaction regions have different roles; validate each required role.",
    "Use exported reference scenes with collision_mode block and explicit position/contact assertions for required obstacle behavior; inspect the contact trace and failed assertions.",
    "For actions with planted feet or fixed tool contact, declare planted_contacts intervals on exported sockets and inspect every episode's world-space drift; do not omit intermediate frames or silently loosen tolerances to pass.",
    "Inspect sorting both in front of and behind occluders.",
    "Inspect required direction/action/state combinations, transitions and interruptions.",
    "For contracted scored clips, author complete beat coverage with a concrete performance purpose and timed gameplay events; require these through delivery.animation_scores so missing beats/events block construction.",
    "Use scenario event assertions to verify exact occurrence times across loops, restarts and interruptions. Beat labels and timing alone cannot prove anticipation, impact or recovery are visible.",
    "For supported top-down humans, author posture lean/crouch changes per beat and inspect chest/head/pelvis movement alongside hands/tools. Verify declared plants; a tool-only change cannot satisfy a requested whole-body performance.",
    "Inspect source-verified motion_diagnostics in review packets or run structure --motion: compare ground-relative body and limb paths, limb-only transitions and the loop join. Unavailable diagnostics require visual inspection; do not treat movement magnitude as artistic approval.",
    "Passing grid collision or planted-socket checks does not establish weight, anticipation, recovery, personality or physical support; inspect those visually and report missing verification.",
    "Compare scale and readability together with the project catalog on real backgrounds.",
    "Treat seamless tiles, nine-slice UI, static illustrations and particles according to their own contracts; do not impose character-only rules.",
]


def task_guidance(category, stage):
    return {
        "domain_checks": DOMAIN_CHECKS.get(category, ["Establish the asset category before selecting domain checks."]),
        "inspection_protocol": [
            "Open the actual artifact at native resolution and integer zoom; a filename or written claim is not visual evidence.",
            "Inspect silhouettes, major masses, materials and whole scenes before rewarding small details.",
            "Compare the current revision with rejected candidates and existing catalog members.",
            "Report uncertainty and missing tests as unverified; metrics alone never establish artistic quality.",
        ],
        "runtime_checks": RUNTIME_CHECKS if stage in ("contract", "context_review", "verification") else [],
        "review_rubric": CRITERIA if stage in ("art_review", "context_review") else {},
        "repair_protocol": [
            "Locate each defect by asset, part, frame or region and explain its visible or functional consequence.",
            "State the hypothesized cause and the smallest structural, animation or metadata change that could resolve it.",
            "Preserve successful identity and style constraints; rerender and rerun affected checks.",
            "A new seed, recolor or renamed file does not by itself resolve a structural defect.",
            "Intentional holds, shared variant silhouettes and deliberate particles are valid when the contract explains them.",
        ],
    }
