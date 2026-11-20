# Generation quality: repeatable review

This pass changes procedural generators and agent instructions. It does not
train model weights or establish universal artistic quality.

## Regression gate

```powershell
python -m unittest discover -s tests -q
```

The suite covers reuse rejection before file loading; immutable rejection by
pixel content; independent eleven-criterion commercial reviews; new material motifs,
determinism, density and silhouette clipping; native UI frame dimensions and
transparent centers; translucent building shadows; tree size and seed diversity;
readable fruit features; four creature directions during reactions; tapered human
torso; articulated four-direction humans; distinct tool/food silhouettes at
16/32/64; building placement/collision metadata; and transparent ground shadows.

The commercial gate is deliberately stricter than image metrics. Generate a
review template with `pixelai qa <image> --template <review.json>`, have a reviewer
other than the generator inspect native size and integer zoom, then record the
decision with `pixelai qa <image> --review <review.json> --catalog
reports/commercial_catalog.json --record`. A rejected pixel payload stays rejected
after renaming, metadata edits, or transparent padding.

## Visual review from scratch

Every spec below declares `fresh:true`. Run `pixelai validate <spec> --fresh`
before `pixelai render <spec> -o <output> --fresh --json`.

| Spec | Output reviewed | Focus |
| --- | --- | --- |
| `specs/quality_nature.json` | `outputs/nature_quality_seeds.png` | Two seeds each for oak, pine and fruit trees |
| `specs/quality_directions.json` | `outputs/sprite_quality_fresh.png` | Human, cow and chicken down/up/left/right |
| `specs/quality_items.json` | `outputs/items_material_quality_fresh.png` | Axe, pickaxe, carrot, bread and fish at 16/32/64 |
| `specs/quality_ui_building.json` | `outputs/quality_ui_building.png` | Native panels in five themes, button states, architecture |
| `specs/quality_materials.json` | `outputs/quality_materials.png` | Rock, soil, leaves, bark, water and cloth accents |
| `specs/quality_rocks.json` | `outputs/quality_rocks.png` | Boulder, mossy rock and ore facets |

Inspect the actual image at native size and integer zoom. Reject clipped outlines,
stretched corners, missing views, opaque ground shadows, indistinct material planes,
and fruit that reads as dots. Passing tests alone does not approve artwork.

## Current limits

- Integrated creatures are cow and chicken. Unsupported species now fail explicitly.
- Humans retain chibi proportions and the existing clothing family. Tapering the
  torso improves the silhouette without supplying an anatomy or wardrobe system.
- New axe, pickaxe, carrot, bread and fish silhouettes have fixed orientation.
- UI produces graphic components, not text layout or a complete interface system.
- Runtime attachments currently cover buildings. Humans, nature, items, and UI
  still need equivalent pivots, slicing/state manifests, and integration trials.
- Bounded material samples are not seamless autotiles; periodic edge compatibility
  remains unsupported and must not be claimed.
- Seed variation changes procedural geometry, not the generator's style family.
- Fresh mode blocks external asset imports, not hand-copied geometry. Agents must
  still distinguish rejected designs from approved assets.
- PNG preserves partial shadow alpha; GIF has binary transparency.
- Material accents are clustered motifs; they do not simulate physical materials.
- Changes are in this repository. A previously cached plugin may need refreshing
  before another chat loads these updated skill instructions.

## Commercial status of this pass

Passing tests did not approve any candidate. Independent reviews rejected the
current human sheet, lantern sheet, moss rock, ore rock, orchard, material board,
building sheet, and inventory sheet. Their hashes and evidence are retained in
`reports/commercial_catalog.json`; they are diagnostic fixtures, not deliverables.
The rejection exposed the next engine-level priority: consistent runtime manifests
and modular exports across every asset family. Buildings now emit name, origin,
y-sort, entrance, and collision polygon metadata as the first implementation of
that contract.
