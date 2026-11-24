"""Regression coverage for distinct directions and readable icon silhouettes."""
import unittest
from pixelai.canvas import Canvas
from pixelai.items import draw_item_rig
from pixelai.runner import run_spec


def sprite(op, size=64):
    return run_spec({'width': size, 'height': size, 'palette': 'cozy24',
                     'style': 'lineless', 'ops': [op]})


class SpriteQualityTests(unittest.TestCase):
    def test_reaction_keeps_all_four_animal_directions(self):
        for species in ('cow', 'chicken'):
            for pose in ('idle', 'walk', 'jump', 'surprised'):
                views = [tuple(sprite({'op': 'animal_rig', 'species': species,
                                      'dir': direction, 'pose': pose, 'frame': 1,
                                      'shadow': False, 'emotes': False}).pixels)
                         for direction in ('down', 'up', 'left', 'right')]
                self.assertEqual(len(set(views)), 4, (species, pose))

    def test_unknown_animal_does_not_silently_render_chicken(self):
        from pixelai.creatures import draw_animal_rig
        with self.assertRaisesRegex(ValueError, 'Unsupported animal species'):
            draw_animal_rig(Canvas(32, 32), 0, 0, {}, {'species': 'dragon'})

    def test_unknown_item_does_not_silently_render_apple(self):
        with self.assertRaisesRegex(ValueError, 'Unsupported item kind'):
            draw_item_rig(Canvas(32, 32), 0, 0, {}, {'kind': 'unknown'})

    def test_new_items_have_distinct_native_silhouettes(self):
        for size in (16, 32, 64):
            shapes = []
            for kind in ('axe', 'pickaxe', 'carrot', 'bread', 'fish'):
                canvas = Canvas(size, size)
                draw_item_rig(canvas, 0, 0, {}, {'kind': kind, 'size': size})
                self.assertGreater(sum(p[3] > 0 for p in canvas.pixels), size)
                self.assertEqual(canvas.clipped_pixels, 0)
                shapes.append(tuple(p[3] > 0 for p in canvas.pixels))
            self.assertEqual(len(set(shapes)), 5)

    def test_ground_shadows_are_translucent_and_not_outline_sources(self):
        from pixelai.creatures import draw_animal_rig
        from pixelai.rig import draw_char_rig
        from pixelai.palettes import get_palette
        palette = get_palette('cozy24')
        cases = [(draw_char_rig, {'size': 32, 'perspective': view, 'shadow': True})
                 for view in ('topdown', 'iso')]
        cases += [(draw_animal_rig, {'species': species, 'perspective': view,
                                    'dir': direction, 'shadow': True, 'emotes': False})
                  for species in ('chicken', 'cow') for view in ('topdown', 'iso')
                  for direction in ('down', 'right')]
        cases += [(draw_item_rig, {'kind': 'apple', 'size': 32, 'shadow': True})]
        for draw, op in cases:
            with self.subTest(op=op):
                canvas = Canvas(64, 64)
                draw(canvas, 8, 8, palette, op)
                self.assertTrue(canvas.shadow_pixels)
                for idx in canvas.shadow_pixels:
                    self.assertLessEqual(canvas.pixels[idx][3], 64)
                    self.assertIn(idx, canvas.no_outline)

    def test_human_shoulders_taper_instead_of_rectangle(self):
        canvas = sprite({'op': 'char_rig', 'size': 64, 'dir': 'down', 'shadow': False})
        shirt = (194, 75, 56, 255)
        widths = [sum(canvas.get_pixel(x, y) == shirt for x in range(64)) for y in (32, 35, 39)]
        self.assertGreater(len(set(widths)), 1)

    def test_apple_has_crown_notch_and_gloss(self):
        canvas = sprite({'op': 'item_rig', 'kind': 'apple', 'size': 48})
        self.assertEqual(canvas.get_pixel(21, 12)[3], 0)
        self.assertGreater(canvas.get_pixel(18, 12)[3], 0)
        self.assertGreater(len(set(p for p in canvas.pixels if p[3])), 5)

    def test_special_lantern_has_glass_metal_flame_and_four_frames(self):
        for size in (16, 32, 64):
            frames = []
            for frame in range(4):
                canvas = sprite({"op": "item_rig", "kind": "lantern", "size": size,
                                 "frame": frame, "shadow": False}, size)
                self.assertEqual(canvas.clipped_pixels, 0)
                self.assertGreater(len({p for p in canvas.pixels if p[3]}), 7)
                self.assertGreater(sum(p[3] for p in canvas.pixels), size * 255)
                frames.append(tuple(canvas.pixels))
            self.assertGreaterEqual(len(set(frames)), {16: 2, 32: 3, 64: 4}[size])
