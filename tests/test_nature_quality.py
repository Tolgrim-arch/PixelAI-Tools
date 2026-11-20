import unittest
from pixelai.canvas import Canvas
from pixelai.nature import draw_nature_rig

class NatureQualityTests(unittest.TestCase):
    def render(self, variant='oak', size=64, seed=11, kind='tree', shadow=False):
        canvas = Canvas(size, size)
        draw_nature_rig(canvas, 0, 0, {}, {'kind': kind, 'variant': variant, 'seed': seed, 'shadow': shadow})
        return canvas

    def test_small_pine_uses_requested_canvas(self):
        for size in (32, 64, 128):
            canvas = self.render('pine', size)
            occupied = [(i % size, i // size) for i, c in enumerate(canvas.pixels) if c[3]]
            self.assertTrue(occupied)
            self.assertGreater(max(y for _, y in occupied), size * .75)
            self.assertLess(min(y for _, y in occupied), size * .25)

    def test_seed_changes_broadleaf_silhouette_deterministically(self):
        first = self.render(seed=1)
        second = self.render(seed=2)
        self.assertEqual(first.pixels, self.render(seed=1).pixels)
        self.assertNotEqual([bool(c[3]) for c in first.pixels], [bool(c[3]) for c in second.pixels])

    def test_pine_seeds_change_branch_silhouette(self):
        first = self.render('pine', 128, seed=1)
        second = self.render('pine', 128, seed=2)
        self.assertNotEqual([bool(c[3]) for c in first.pixels], [bool(c[3]) for c in second.pixels])

    def test_unknown_kind_and_species_do_not_fall_back(self):
        with self.assertRaisesRegex(ValueError, 'Unknown nature kind'):
            self.render(kind='unknown')
        with self.assertRaisesRegex(ValueError, 'Unknown tree variant'):
            self.render('unknown')

    def test_ground_shadows_are_translucent_and_outline_free(self):
        for variant, kind in (('oak', 'tree'), ('pine', 'tree'), ('boulder', 'rock')):
            canvas = self.render(variant, kind=kind, shadow=True)
            self.assertTrue(canvas.shadow_pixels)
            for i in canvas.shadow_pixels:
                self.assertLessEqual(canvas.pixels[i][3], 64)
                self.assertIn(i, canvas.no_outline)

    def test_fruit_has_highlight_stem_and_nontrivial_area(self):
        from pixelai.broadleaf import _draw_fruit
        canvas = Canvas(16, 16)
        _draw_fruit(canvas, 8, 8, 4, (200, 40, 30, 255), (240, 80, 60, 255), (130, 25, 30, 255), (40, 130, 40, 255))
        self.assertGreater(sum(c[3] > 0 for c in canvas.pixels), 40)
        self.assertGreaterEqual(len(set(c for c in canvas.pixels if c[3])), 6)
        self.assertEqual(canvas.get_pixel(8, 3), (112, 75, 44, 255))

if __name__ == '__main__':
    unittest.main()
