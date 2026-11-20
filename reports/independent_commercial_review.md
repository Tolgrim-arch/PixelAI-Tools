# Independent commercial pixel art stress test

Six new specs use only built-in operations and declare `fresh: true`. The inventory combines the UI rig with an original header accent. The enchanted lantern uses hand-authored polygons and two ellipses to test a specialized design outside the item presets. No prior artwork was imported. Each spec passed `validate --fresh` and `render --fresh --json` with no warnings. Review covered each actual PNG at 1× and a 3× nearest-neighbor contact sheet built by `pixelai showcase`. Inspection and transparency counts support the technical observations. Visual approval is an independent judgment.

## Baseline disposition at 3a04824

| Asset | Spec and render suffix | Commercial disposition |
| --- | --- | --- |
| Gold inventory, 192 × 132 | `inventory` | Rejected as ornate inventory art. Legible component mockup. |
| Teal-roof cottage, 112 × 108 | `cottage` | Rejected as a commercial top-down cottage. Readable front elevation prototype. |
| Moss rock, 60 × 46 | `moss_rock` | Rejected. Moss color is lost and the design shares the ore rock's geometry. |
| Ore rock, 60 × 46 | `ore_rock` | Rejected as a distinctive ore node. Tiny deposits read as flecks. |
| Orchard pair, 140 × 82 | `orchard` | Rejected as a finished orchard set. Distinct crowns, but fruit character and trunk variation fall short. |
| Enchanted lantern, 48 × 48 | `enchanted_lantern` | Visual candidate at the authored size. Integration and smaller icon sizes are unverified. |

Use the shared stem `stress_commercial_` with each suffix under `specs/` for JSON and `outputs/` for PNG.

## Baseline review against eleven criteria

| Criterion | Inventory | Cottage | Rock pair | Orchard | Enchanted lantern |
| --- | --- | --- | --- | --- | --- |
| Professional attractiveness | High contrast and clear spacing. Uniform heavy gold bands and flat center look generic. | Pleasant teal and cream. Front elevation feels rigid and template-like. | Evenly weighted low slabs have little character. | Saturated clustered foliage gives good mass. Straight repeat trunks make the group mechanical. | Compact, clean silhouette with a focused mint flame. |
| Legibility | Slots separate clearly. Selected slot and all button states are distinguishable, with the hover state very bright. | Roof, entrance, dormer and flower box read at 1×. The roof structure is ambiguous. | Rock class reads. Moss identity is absent and ore type is weak. | Tree and warm fruit class read. Exact fruit species is ambiguous at native size. | Loop, cap, feet and flame are readable at 48 px. |
| Clustering | Clear slot and control groups. Border diamonds distribute the same accent weight along both rails. | Glass and shingles form groups. Flower box collapses to a strip with dots. | Primary facets form clear clusters. Grain repeats on a visible grid. | Unequal crown lobes provide larger groups, with jagged fine patches inside them. | Cap, glass, flame and base use separate contiguous color masses. |
| Lighting and color | Top/left rim light is consistent, but preset hover highlights overpower the header. | Roof light comes from the left while the main facade remains one flat plane. | Upper-left light is readable. Moss and stone share a hue, weakening both. | Green-to-teal shadow reads. Orange and red fruit are separable. | Warm top-left brass and cool glass frame the mint light coherently. |
| Material | Bevel and inlays imply metal. Flat gold rails make most of it look painted. | Window glass and timber read. Regular roof strokes and sparse chimney masonry give limited tactile detail. | Stone facets read. Moss has no green cue and ore lacks a connected mineral vein. | Bark is readable but strongly vertical. Fruit is shaded at 3×. | Glass and brass are suggested by plane contrast. Reflections are stylized and sparse. |
| Specialized design | Inventory layout and state semantics are clear. Rails remain general-purpose panel art. | Door, planter and attic window establish purpose. Roof/front intersection weakens top-down construction. | Duplicated parent geometry undermines two distinct material props. | Two colors and canopy heights suggest varieties. Fruit forms show limited specialization. | Ring handle, brass fittings and stylized magical flame support the enchanted artifact brief. |
| Detail | Corner diamonds and small rail motifs are crisp. Both vertical rails have no comparable detail. | Attic crossbar and outline stay legible. Flower box detail is tiny and evenly spaced. | Moss is one shallow cap. Ore is three small, rectangular deposits. | Stem/highlight detail exists at 3× and often merges at 1×. | Fittings, cap inlay, highlight and flame are grouped. Small details stay restrained. |
| Originality | The arrangement and header are fresh. The stock rim motif repeats at a fixed interval. | Fresh parameters generate a fixed building layout. | Same seed-independent body with variant markings. | Seeds produce genuinely different crown contours. Ground anchor and trunk language repeat. | Custom silhouette and fitted light source authored from primitives. |
| Consistency | Button states share a clear visual family. Untinted hover pushes brightness unusually far. | Trim, facade, foundation and windows use an internally coherent palette. | Material hues match across the two bodies, at the expense of moss differentiation. | Common style, shadow and planting anchor work across both variants. | Warm fittings echo the inventory palette. It fits the set at the authored scale. |
| Technical integrity | One island, no singletons, 3 px minimum margin. | One island, no singletons, 6 px minimum margin. Partial shadow alpha. | One island each, no singletons, 2 px minima. Partial shadow alpha. | Two expected islands, no singletons, 3 px minimum margin. Partial shadow alpha. | One island, no singletons, 4 px minimum margin. Transparent background. |
| Game readiness | A flattened sheet demo. Standalone components, 9-slice settings and live states remain unverified. | Atlas fit, sorting origin and collision remain unverified. | Anchors and tile readability remain unverified, and moss identity fails visually. | Separate sprites, harvest state and in-game sorting remain unverified. | Suitable for an inventory import trial at 48 px. Integration and resampling remain unverified. |

## Baseline defects

- **Rock color couples stone and moss.** `nature_rig` with `kind: rock`, `variant: mossy`, `w: 56`, `h: 42`, `color: "#7b8297"` renders the moss cap blue-gray like the rock. A read-only count found zero fully opaque pixels whose green channel exceeds both red and blue. The rock and foliage branches both read the same `color` key in `pixelai/nature.py`. The cluster is an overlay of shallow ellipses and reads as a second stone layer.
- **Rock seeds have no geometric effect.** Rerendering that same moss spec while changing only `seed` from 25 to 96 yields identical RGBA bytes. With matching size and base color, the moss and ore renders differ in only 14 fully opaque mask positions, all in the upper cap region. `nature_rig`'s rock branch builds fixed facet polygons and regular grain at 4 px horizontal and 3 px vertical steps, and gives ore three fixed 3 × 2 marks.
- **The orchard ignored the generic foliage color.** Rerendering both `nature_rig` fruit ops at the same seeds 41 and 92 while changing only `color` from `"#58905b"` to `"#c02dcc"` yields identical RGBA bytes. The broadleaf route in `pixelai/broadleaf.py` reads `band_colors` for crown overrides. The broadleaf-specific option is a usable control, while the generic option is silently discarded.
- **Fruit detail is size-sensitive.** Those same 64 × 78 fruit ops with orange and red `accent_color` values produce visibly different canopies. At 1× the small bodies read as generic yellow or coral fruit points. At 3× their light/shadow, stem and offset leaf separate, exposing the small contrast budget at native size. Both trunks remain slim, upright and exposed from a raised crown to a similar root flare. The calls in `pixelai/broadleaf.py` share the same trunk dimensions and placement logic at the same canvas size.
- **The gold panel does not scale its ornament to the brief.** `ui_rig` with `kind: panel`, `theme: gold`, `w: 184`, `h: 124`, `frame_width: 12`, `inner_fill: true` leaves broad gold rails dominated by one flat tone. The same motif repeats at a 14 px pitch on top and bottom, and the vertical rails receive corner details only. `pixelai/ui.py` draws the top/bottom accents with a fixed pitch by theme. The custom teal header helps hierarchy without improving the gold rails.
- **Cottage front gable lacks roof depth.** `building` with `roof_style: gable`, `w: 89`, `h: 78`, `roof_h: 38`, `foundation_h: 8`, `timber_frame: true`, `windows: true`, `chimney: true`, `smoke: false` places a centered triangular wall on top of one trapezoidal roof. At 3× the shingle plane ends at the triangle and no secondary pitched roof plane bridges the two forms. The facade remains an orthogonal rectangle above a shallow footing. `pixelai/building.py` draws the gable wall and bargeboards over the main roof and has no roof return geometry for this gable. The flower box has three isolated accent pixels across a continuous rectangular green strip.

## Baseline outline and ground shadows

No visible outline touches a PNG edge. The inventory and lantern have no partial alpha. The cottage shadow is a straight projected footprint with 278 pixels at alpha 46. The rocks each have 50 shadow pixels at alpha 50. The orchard pair has 368 shadow pixels at alpha 50. None show a solid outlined ground blob. Native PNG inspection and the dark showcase background were used for visual review. Light-background compositing and in-engine appearance are unverified.

## Nature rerender after generator fixes

The previous nature pass used the baseline specs embedded in the `_before.png` PNGs. Use `pixelai extract` to recover those specs for the baseline engine at `3a04824`. Both rock seeds began to drive the outline and facet junctions. The moss cap gained its own color, with optional `foliage_color`. The ore vein became a connected cluster. The orchard's explicit `color` began setting the crown's middle value, with precedence still given to explicit `band_colors` and `ramp`. The final ore and orchard PNGs use the current JSON specs and the second-pass renderer described below.

| Criterion | Moss rock after | Ore rock after | Orchard pair after |
| --- | --- | --- | --- |
| Professional attractiveness | Grounded wide faceted form. Moss breaks up the top span. | Taller, sharper silhouette and one central mineral accent. | Muted greens fit the set. Similar bare trunks remain conspicuous. |
| Legibility | Moss reads as a visibly green surface at 1×. | Rock reads at 1×. The warm slash suggests mineral, but still needs stronger ore character. | Canopy and fruit read. Fruit species distinction remains weak at 1×. |
| Clustering | Broad facets and one contiguous cap replace repeated stone noise. | One connected vein replaces loose flecks. | Large leaf patches still work. Fine clusters stay busy near fruit. |
| Lighting and color | Left and top planes are brighter. Moss and stone separate by hue. | Bright plane helps the warmer accent read. The darker right face stays distinct. | Requested sage-green base now participates in all crown bands. Fruit retains warm contrast. |
| Material | Green mass with broken lower edge suggests moss. The cap stays shallow. | Planar stone reads. The small straight-edged vein can still look like an applied gold mark. | Bark and vegetation remain distinct. Fruit retains a compact highlight and shadow. |
| Specialized design | Broad planted boulder shape supports a moss-covered prop. | New silhouette and exposed seam distinguish it from moss. Mineral crystal structure remains limited. | Two canopy silhouettes and two fruit hues establish variation. Trunk architecture remains shared. |
| Detail | Green facets and small hanging edges add texture without a grain pattern. | Sparse connected ore accents retain the main planes. More ore-specific form is needed for a premium prop. | Fruit stems and leaves remain most legible at 3×. |
| Originality | Seeds now alter geometry. The visible cap shape still uses a shared motif. | The seam and steeper profile are distinct from the moss rock. The seam path still uses a shared motif. | Crown silhouettes differ by seed. The fix adds color control and leaves the tree architecture intact. |
| Consistency | Scale, slate palette and upper-left light agree with the ore rock. | Warm accents and outline agree with the set. | Both trees now share the authored crown color and different warm fruit values. |
| Technical integrity | One island, no isolated pixels, 2 px minimum margin. | One island, no isolated pixels, 2 px minimum margin. | Two expected islands, no isolated pixels, 3 px minimum margin. |
| Game readiness | Visual candidate for a map import trial. Sorting and anchor behavior are unverified. | Keep as a test seed. Commercial ore readability and gameplay sorting remain unverified. | Keep as test assets. Harvest state, per-tree integration and game placement remain unverified. |

The after shadows retain alpha 50 across 75 moss-rock pixels, 78 ore-rock pixels and 368 orchard pixels. The moss rock is a visual candidate at the authored size. The ore rock and orchard need further visual work before commercial selection. Game integration remains unverified. Targeted tests cover seeded morphology, palette independence, shadow preservation and broadleaf precedence. These checks validate the fixes independently of artistic judgment.

## Ore and orchard follow-up

Two additional fresh render iterations were inspected at 1× and at 3×. The first turned the ore slash into a connected faceted body inside a darker pocket, but a smooth rim still made it look affixed to the stone. The first orchard iteration introduced a tapered, seeded trunk with independently placed branches and fruit silhouettes. The pear remained too round and the trunk feet lacked emphasis.

The second iteration introduced foreground stone shelves at the ore deposit's edges. The ore face retains a warm dark side and two differently lit planes under the shelves. The pear has a narrow neck and a lower bulge, while the apple retains a broad upper body and a shoulder cleft. Both have stems, leaves and highlight clusters. Fruit details clip to the existing sprite. The trees now have visibly different forks, bends and root spans around stable ground anchors. The orchard spec chooses `fruit: "pear"` on seed 41 and `fruit: "apple"` on seed 92. The `fruit` option is optional and defaults to apple.

| Criterion | Final ore rock | Final orchard |
| --- | --- | --- |
| Professional attractiveness | Focused mineral cluster within a clean, compact rock. | Leaning trunks and uneven crowns give the set character. |
| Legibility | At 1× the orange mineral body reads as an embedded resource node. The individual facets are clearer at 3×. | At 1× the yellow fruit's tall neck separates from the rounder red shapes. Stem and cleft details are clearer at 3×. |
| Clustering | One attached mineral mass and large contiguous stone faces. | Fruit is spaced into small groups with foliage between them. Upper foliage still has busy patches. |
| Lighting and color | Slate surfaces frame the warm ore. Lower rock shelves sit over the warm facets. | Four foliage tones and readable fruit highlights. A few branch shadows remain dark in the crown gaps. |
| Material | Recess shadow, metal-like facets and overlapping stone imply embedded ore. The ore alloy remains visually unspecified. | Bark and leaves separate from the glossy fruit. Trunk planes are broad, with limited bark texture. |
| Specialized design | Angular facets and foreground lips support a mining-resource prop. | Yellow pears have necks and wider bases. Red apples show a cleft and rounder body. |
| Detail | The boulder silhouette and main faces retain priority over the deposit. | Legs of the forks, root flares, fruit stems and highlight clusters remain distinct at integer zoom. |
| Originality | Fresh seeded silhouette with purposeful mineral placement beneath rock shelves. Other ore seeds still share a deposit motif. | Two bends, branch junctions and root profiles come from seeded geometry. Neither version is a simple recolor. |
| Consistency | Matches the moss boulder in scale, side shading and outline weight. | Both trees share the same footprint height, palette and light direction. |
| Technical integrity | One island, no singleton pixels, 2 px minimum margin. | Two intended islands, no singleton pixels, 3 px minimum margin. Fruit variants preserve the same alpha mask with a fixed seed. |
| Game readiness | Visual candidate at 60 × 46. Tile sorting, collision and depletion states are unverified. | Visual candidates at 64 × 78 per tree. Separate in-engine sorting anchors and harvest states are unverified. |

Both final assets are visual candidates at the reviewed sizes. The ore rock's mineral type and the orchard's small fruit details have limited readability at smaller scales. There was no smaller art or game-runtime test in this pass. The topology tests establish connected faceted ore and seed-driven lower trunk differences, with a separate test confirming apples and pears vary the fruit shape without changing the tree's silhouette.

## Independent reviews of the revised materials, buildings and inventory

An independent reviewer examined each PNG at native resolution and at 3× nearest-neighbor scale. All three received a rejection with no pending criteria. Each schema-v1 review records the eleven decisions and evidence, and the catalog binds the results to the reviewed pixels.

| Candidate | Evidence | Review |
| --- | --- | --- |
| Materials | Cobble, boards and shingles read at 1×. Cloth can read as a mineral stripe, and soil has sparse, flat spotting. The 368 × 232 preview has an intended opaque background and supplies twenty sample regions. Tile wrapping and extraction for runtime remain unverified. | [Materials review](review_commercial_materials.json) · [Serene Village reference](https://limezu.itch.io/serenevillagerevamped) |
| Buildings | The cottage and barn are distinguishable at 1×. The roof returns provide depth, while the similar dormer silhouettes and repeated slab foundations reduce architectural variety. The 238 × 120 sheet contains two expected components. Per-building anchors and tile placement remain unverified. | [Buildings review](review_commercial_buildings.json) · [Tiny Swords reference](https://pixelfrog-assets.itch.io/tiny-swords) |
| Inventory | The revised frame adds teal inlays, mitered corners and a deep inner bevel. The broad rails and repeating diamonds fall short of the ornate brief. The 192 × 132 sheet clearly depicts the selected slot and three button states, while modular exports and nine-slice behavior remain unverified. | [Inventory review](review_stress_commercial_inventory.json) · [Fantasy UI Pack reference](https://catau-games.itch.io/fantasy-ui-pack-ornate-pixel-art-gui-hud) |

## Independent review of humans, lanterns and nature candidates

The five candidates were reviewed at native size and 3× nearest-neighbor zoom, and `pixelai inspect` metrics were checked. All five were recorded as **rejected** in `commercial_catalog.json`; none has verified in-game integration. The [Sprout Lands asset pack](https://cupnooble.itch.io/sprout-lands-asset-pack) is a named comparison for its published farming-asset and four-direction animation scope. Its downloadable sprites were not visually compared in this review.

- **Humans:** Recognizable characters and directions, but small tool shapes and repeated poses limit finish. Atlas slicing, timings, pivots and runtime behavior remain unverified. [Review](commercial_humans.independent.review.json).
- **Lanterns:** Readable handles and glass, but four small lanterns repeat a silhouette, and the large purple lantern differs in scale and palette. Extraction and import remain unverified. [Review](commercial_lanterns.independent.review.json).
- **Moss rock:** Green moss is visible but forms a shallow strip on a basic slab. Tile placement and collision are unverified. [Review](stress_commercial_moss_rock.independent.review.json).
- **Ore rock:** The warm mineral cluster reads against slate but its mineral type is ambiguous. Placement and depletion behavior are unverified. [Review](stress_commercial_ore_rock.independent.review.json).
- **Orchard:** Fruit colors and crown shapes differentiate the pair, though small details compete and trunk language repeats. Separation, harvest states and sorting anchors are unverified. [Review](stress_commercial_orchard.independent.review.json).

The PNGs have no isolated singleton pixels; the sheets contain the expected multiple islands and the two rocks have one island each. These measurements do not establish commercial readiness or independently establish generator provenance.
