"""Native 32+ px top-down humans with articulated limbs and directional clothing."""

from math import ceil, hypot
from typing import Any

from pixelai.canvas import Canvas
from pixelai.color import RGBA, brighten, darken, ground_shadow_color, parse_color
from pixelai.geometry import tapered_polygon

Point = tuple[float, float]

# Hand, elbow and axe tip in the side view. The grip leads the axe through
# the windup and strike, then returns below the shoulder.
PROFILE_SWING = (
    ((18.7, 15), (20, 17.4), (23.4, 6.5)),
    ((21.5, 16.4), (20.1, 18.7), (27.5, 11.7)),
    ((22.5, 21), (20.4, 19.5), (28, 25.3)),
    ((20, 21.5), (18.4, 18.3), (24.8, 25.5)),
)
FRONT_SWING = (
    ((23, 14), (22, 17.5), (27.2, 6.5)),
    ((22.8, 16.7), (23.5, 19), (27.7, 11)),
    ((21.8, 21), (22.2, 19), (25.5, 26.7)),
    ((22.4, 21.2), (22.5, 18.6), (27.1, 25)),
)
BACK_SWING = (
    ((23, 14), (23, 17.5), (27.2, 6.5)),
    ((23.2, 16.1), (23, 18.5), (26.8, 11.3)),
    ((23.4, 19), (23, 18), (27.7, 16.1)),
    ((22.6, 20.7), (22.5, 18.7), (27.5, 19.5)),
)


def axe_geometry(hand, tip):
    dx, dy = tip[0]-hand[0], tip[1]-hand[1]
    length = hypot(dx, dy)
    if length <= 1e-9:
        raise ValueError("Tool grip and tip must differ")
    tx, ty = dx/length, dy/length

    def blade(along, across):
        return tip[0]+tx*along-ty*across, tip[1]+ty*along+tx*across

    handle = blade(-length-1.3, 0), blade(.6, 0)
    body = [blade(-1.7, -.45), blade(.1, -.55), blade(1.25, 1.05), blade(1.45, 2.2), blade(.0, 2.7), blade(-1.55, 1.7)]
    highlight = [blade(.15, .3), blade(1.15, 1.3), blade(1.2, 2.15), blade(.05, 2.4), blade(-.8, 1.9)]
    return handle, body, highlight


class Human:
    def __init__(self, canvas: Canvas, x: int, y: int, size: int, mirror: bool, morphology=None) -> None:
        self.canvas = canvas
        self.x = x
        self.y = y
        self.scale = size / 32
        self.mirror = mirror
        self.size = size
        self.morphology = morphology
        self.centered = morphology is not None
        self.legs = []
        self.arms = []
        self.equipment_fitted = False
        self.pixel_offset = (0, 0)

    def point(self, point: Point) -> tuple[int, int]:
        if self.morphology is not None:
            point = self.morphology.point(point)
        x, y = point
        if self.centered:
            local_x = round(x*self.scale) + self.size//2 - round(15.5*self.scale)
            if self.mirror:
                local_x = 2*(self.size//2)-local_x
            return self.x + local_x + self.pixel_offset[0], self.y + round(y*self.scale) + self.pixel_offset[1]
        native_x = round(x * self.scale)
        return self.x + (self.size - 1 - native_x if self.mirror else native_x) + self.pixel_offset[0], self.y + round(y * self.scale) + self.pixel_offset[1]

    def plane(self, color: RGBA, *points: Point) -> None:
        self.canvas.draw_polygon([self.point(point) for point in points], color, filled=True)

    def dot(self, color: RGBA, x: float, y: float, rx: float, ry: float) -> None:
        if self.morphology is not None:
            rx, ry = self.morphology.radii(x, y, rx, ry)
        self.canvas.draw_ellipse(*self.point((x, y)), max(0, round(rx * self.scale)),
                                 max(0, round(ry * self.scale)), color, filled=True)

    def link(self, color: RGBA, start: Point, end: Point, root: float, tip: float) -> None:
        """Rasterize a tapered limb or handle along a pair of joints."""
        self.plane(color, *tapered_polygon(start, end, root, tip))

    def boot(self, pants: RGBA, shoes: RGBA, hip: Point, knee: Point, foot: Point,
             side: bool, far: bool) -> None:
        self.legs.append((hip, knee, foot))
        self.link(pants, hip, knee, 1.85, 1.35)
        self.link(pants, knee, foot, 1.35, 1.05)
        x, y = foot
        toe = 2.45 if side else (1.3 if far else 1.6)
        self.plane(darken(shoes, .82), (x - 1.25, y - 1.3), (x + .85, y - 1.25),
                   (x + toe, y - .35), (x + toe - .25, y + .75), (x - 1.5, y + .75))
        self.plane(shoes, (x - 1.15, y - 1.5), (x + .75, y - 1.5),
                   (x + toe, y - .35), (x + toe - .3, y + .1), (x - 1.25, y + .1))
        self.plane(brighten(shoes, 1.24), (x + .3, y - .65),
                   (x + toe, y - .2), (x + toe - .75, y + .25), (x + .15, y + .15))

    def arm(self, shirt: RGBA, skin: RGBA, shoulder: Point, elbow: Point, hand: Point) -> None:
        self.arms.append((shoulder, elbow, hand))
        self.link(shirt, shoulder, elbow, 1.35, 1.0)
        self.link(darken(shirt, .83), elbow, hand, 1.0, .7)
        # Subtle sleeve cuff accent just above the hand
        cuff_x = elbow[0] * 0.25 + hand[0] * 0.75
        cuff_y = elbow[1] * 0.25 + hand[1] * 0.75
        self.dot(brighten(shirt, 1.18), cuff_x, cuff_y, .72, .45)
        self.dot(skin, *hand, .8, .9)

    def axe(self, wood: RGBA, metal: RGBA, hand: Point, tip: Point) -> Point:
        if self.morphology is not None:
            morphology = self.morphology
            mapped = morphology.point(hand)
            delta = (round((mapped[0]-hand[0])*self.scale)/self.scale,
                     round((mapped[1]-hand[1])*self.scale)/self.scale)
            mapped = hand[0]+delta[0], hand[1]+delta[1]
            mapped_tip = tip[0]+delta[0], tip[1]+delta[1]
            handle, body, highlight = axe_geometry(mapped, mapped_tip)
            points = tapered_polygon(handle[0], handle[1], .4, .42) + body + highlight
            xs, ys = [point[0] for point in points], [point[1] for point in points]
            shift_x = (ceil(max(0, 3-min(xs))*self.scale)-ceil(max(0, max(xs)-29)*self.scale))/self.scale
            shift_y = (ceil(max(0, 2-min(ys))*self.scale)-ceil(max(0, max(ys)-29)*self.scale))/self.scale
            mapped = mapped[0]+shift_x, mapped[1]+shift_y
            self.equipment_fitted = abs(shift_x)+abs(shift_y) > 1e-9
            pixel_delta = (round((mapped[0]-hand[0])*self.scale), round((mapped[1]-hand[1])*self.scale))
            previous_offset = self.pixel_offset
            self.pixel_offset = (previous_offset[0]+pixel_delta[0]*(-1 if self.mirror else 1), previous_offset[1]+pixel_delta[1])
            self.morphology = None
            try:
                self.axe(wood, metal, hand, tip)
            finally:
                self.morphology = morphology
                self.pixel_offset = previous_offset
            target = ((round(hand[0]*self.scale)+pixel_delta[0])/self.scale,
                      (round(hand[1]*self.scale)+pixel_delta[1])/self.scale)
            return morphology.inverse_point(target)
        handle, body, highlight = axe_geometry(hand, tip)
        self.link(wood, handle[0], handle[1], .4, .42)
        self.plane(darken(metal, .72), *body)
        self.plane(metal, *highlight)
        return hand


def draw_topdown_human(canvas: Canvas, x: int, y: int, size: int, direction: str,
                       pose: str, frame: int, palette: dict[str, RGBA],
                       op: dict[str, Any]) -> None:
    """Draw one facing and one pose using 32px design coordinates."""
    side = direction in ("right", "left")
    back = direction == "up"
    morphology = None
    if "morphology" in op or "posture" in op:
        from pixelai.morphology import Morphology
        morphology = Morphology(op.get("morphology", {}))
        if "posture" in op:
            from pixelai.posture import PosturedBody
            morphology = PosturedBody(morphology, op["posture"])
    human = Human(canvas, x, y, size, direction == "left", morphology)
    p, d = human.plane, human.dot

    def color(key: str, name: str, fallback: str) -> RGBA:
        return parse_color(op.get(key, name if name in palette else fallback), palette)

    skin = color("skin", "skin", "#f5c6a5")
    hair = color("hair", "wood_d", "#6e422c")
    shirt = color("shirt", "roof", "#c24b38")
    pants = color("pants", "water_d", "#326496")
    shoes = color("shoes", "soil_d", "#4e3322")
    eye = color("eye", "ink", "#21181b")
    trim = color("trim", "cream", "#f4e8d1")
    skin_shadow = (
        max(0, min(255, int(skin[0] * 0.86))),
        max(0, min(255, int(skin[1] * 0.72))),
        max(0, min(255, int(skin[2] * 0.68))),
        skin[3],
    )
    hair_shadow = darken(hair, .70)
    hair_light = brighten(hair, 1.25)
    shade = darken(shirt, .77)
    light = brighten(shirt, 1.19)
    hair_style = op.get("hair_style", "swept")
    outfit = op.get("outfit", "overalls")
    if hair_style not in ("swept", "crop", "ponytail"):
        raise ValueError(f"Unsupported top-down hair style: {hair_style!r}")
    if outfit not in ("overalls", "coat", "apron"):
        raise ValueError(f"Unsupported top-down outfit: {outfit!r}")

    if op.get("shadow", True):
        old_shadow, old_outline = canvas.mark_shadow, canvas.mark_no_outline
        canvas.mark_shadow = canvas.mark_no_outline = True
        d(ground_shadow_color(color("shadow_color", "shadow", "#33293a")), 15.5, 28.7, 5.65, 1.4)
        canvas.mark_shadow, canvas.mark_no_outline = old_shadow, old_outline

    walking = pose in ("walk", "run")
    working = pose in ("work", "attack")
    stride = (1.0, .35, -1.0, -.35)[frame] if walking else 0
    travel = stride * (4.2 if pose == "run" else 3.1)
    jump_height = 1.6 if "hat" in op else 2.3
    bob = (-1 if walking and frame % 2 else 0) - (jump_height if pose == "jump" else .9 if pose == "fall" else 0)
    bob += (-.55, 0, .85, .55)[frame] if working else .55 if pose == "idle" and frame == 2 else 0
    shoulder_y = 14.6 + bob
    hip_y = 21.2 + bob
    hem_y = hip_y + (2.0 if outfit == "coat" else 1.15)

    for far in (True, False):
        offset = -1 if far else 1
        if side:
            upper = 15.3 + offset * .45
            foot = 15.2 + offset * (.85 + travel)
            lift = 1.5 if walking and frame % 2 and stride * offset < 0 else 0
            knee = (upper + foot) / 2 + .55
        else:
            upper = 15.5 + offset * 2.3
            foot = upper + offset * .75
            lift = max(0, stride * offset * 2.25 * (-1 if back else 1))
            knee = (upper + foot) / 2 - stride * offset * .38
        if working and not far:
            foot += (0, .55, 1.65, .8)[frame]
            knee += (0, .3, .8, .4)[frame]
            lift = .85 if back and frame == 2 else 0
        elif pose in ("jump", "fall"):
            lift = 1.4 if far else .6
        floor_y = 28 - lift + min(0, bob + 1)
        human.boot(darken(pants, .71) if far else pants, darken(shoes, .79) if far else shoes,
                   (upper, hip_y), (knee, (hip_y + floor_y) / 2), (foot, floor_y), side, far)

    left, right = (12, 19.2) if side else (10.6, 20.4)
    spread = 1.25 if outfit == "coat" else .35
    sh_far, sh_near = (left + .5, right - .6)
    if side:
        human.arm(shade, skin_shadow, (sh_near, shoulder_y + .75),
                  (18.2 - travel * .75, 18.5 + bob), (18.1 - travel, 21.1 + bob))
    else:
        free_x = left - 1.3
        human.arm(shade, skin_shadow, (sh_far, shoulder_y + .75),
                  (free_x - .15, 18.5 + bob), (free_x + .35, 21.2 + bob + stride))

    apron = darken(trim, .76)
    if outfit == "apron":
        p(apron, (left + 1.1, 19.15 + bob), (right - .7, 19.15 + bob),
          (right + .8, hem_y - .3), (right + .95, hem_y + .6),
          (left - .8, hem_y + 1.25), (left - .55, hem_y - .4))
    p(shirt, (left + 1.4, shoulder_y - .55), (right - 1.5, shoulder_y - .55),
      (right, shoulder_y + .75), (right - .8, 18.7 + bob), (right + spread, hem_y - .5),
      (right - .8, hem_y), (left + .55, hem_y), (left - spread, hem_y - 1),
      (left + .65, 18.7 + bob), (left, shoulder_y + .7))
    p(shade, (right - 1.8, shoulder_y + .25), (right, shoulder_y + .75),
      (right - .8, 18.7 + bob), (right + spread, hem_y - .5),
      (right - .8, hem_y), (right - 2.4, hem_y - .1), (right - 2.0, 18.7 + bob))
    p(light, (left + 1.1, shoulder_y + .2), (left + 3.2, shoulder_y - .45),
      (left + 3.7, shoulder_y + 1.4), (left + .85, shoulder_y + 2.1))
    if outfit == "coat":
        if back:
            p(light, (left + 1.6, 16.1 + bob), (right - 1.8, 16.1 + bob),
              (right - 2.7, 17.65 + bob), (left + 2.45, 17.5 + bob))
            p(shade, (15, 20.6 + bob), (16.3, hem_y), (14.4, hem_y))
        else:
            collar = 17.8 if side else 15.4
            p(trim, (collar - 2.1, 14.3 + bob), (collar, 15.45 + bob),
              (collar + 1.7, 14.25 + bob), (collar + .55, 17.5 + bob))
            p(shade, (collar + .12, 17.35 + bob), (collar + 1.15, 18.3 + bob),
              (collar + .8, hem_y), (collar + .2, hem_y))
            d(trim, collar - .5, 19.1 + bob, .13, .13)
    elif outfit == "apron" and back:
        human.link(apron, (13.25, 15.55 + bob), (17.6, 19.15 + bob), .37, .37)
        human.link(apron, (17.8, 15.5 + bob), (13.55, 19.2 + bob), .37, .37)
        p(apron, (left + 1, 19.25 + bob), (right - 1, 19.15 + bob),
          (right - 1.1, 20.0 + bob), (left + 1, 20.2 + bob))
        p(trim, (15, 19.05 + bob), (16.8, 19.45 + bob), (17.1, 21.5 + bob),
          (15.5, 20.2 + bob), (14.0, 21.05 + bob))
    elif outfit == "apron":
        bib = right - 1.8 if side else 15.5
        p(apron, (bib - 1.8, 16.7 + bob), (bib + 1.3, 16.45 + bob),
          (right + .15, hem_y), (left + .4, hem_y + 1.4), (left + .9, 20 + bob))
        p(trim, (bib - 1.7, 16.65 + bob), (bib + 1.2, 16.45 + bob),
          (bib + .9, 17.45 + bob), (bib - 1.85, 17.6 + bob))
        p(darken(apron, .82), (bib - 1.45, 19.2 + bob), (bib + 1.1, 19.1 + bob),
          (bib + .7, 21.05 + bob), (bib - 1.1, 21.1 + bob))
    else:
        p(pants, (left + 1.0, 19.4 + bob), (right - 1.0, 19.4 + bob),
          (right - .4, hem_y), (left + .45, hem_y))
        if not back:
            bib = right - 1.8 if side else 15.5
            p(brighten(pants, 1.14), (bib - 2.15, 15.1 + bob), (bib - 1.2, 15.1 + bob),
              (bib - 1.0, 17.35 + bob), (bib + 1.25, 17.35 + bob), (bib + 1.75, 15.2 + bob),
              (bib + 2.45, 15.2 + bob), (bib + 2.1, 19.8 + bob), (bib - 2.05, 19.8 + bob))

    if working:
        hand, elbow, tip = (PROFILE_SWING if side else BACK_SWING if back else FRONT_SWING)[frame]
        hand, elbow, tip = ((px, py + bob) for px, py in (hand, elbow, tip))
        old_hand = hand
        hand = human.axe(color("handle", "wood", "#9c603c"), color("tool", "stone_l", "#b5bfd1"), hand, tip)
        elbow = elbow[0]+(hand[0]-old_hand[0])*.5, elbow[1]+(hand[1]-old_hand[1])*.5
    elif side:
        elbow = 14.5 + travel * .72, 18.2 + bob
        hand = 14.8 + travel * 1.1, 20.9 + bob - abs(stride) * .55
    else:
        elbow = right + 1.1, 18.35 + bob
        hand = right + .8, 21.1 + bob - stride
    human.arm(shirt, skin, (14 if side else sh_near, shoulder_y + 1.15), elbow, hand)

    human.link(skin_shadow, (15.95, 12.55 + bob), (16.05, 15.55 + bob), 1.5, 1.0)
    _draw_head(human, back, side, bob, skin, skin_shadow, eye, hair, hair_light, hair_shadow, hair_style)
    if "hat" in op:
        hat = parse_color(op["hat"], palette)
        _draw_hat(human, back, side, bob, hat, shade)
    if morphology is not None:
        nodes = [{"id": "ground", "parent": None, "point": list(human.point((15.5, 28))), "role": "ground", "radius": 0},
                 {"id": "pelvis", "parent": "ground", "point": list(human.point((15.5, hip_y))), "role": "pelvis", "radius": 0},
                 {"id": "chest", "parent": "pelvis", "point": list(human.point((15.5, shoulder_y))), "role": "chest", "radius": 0},
                 {"id": "head", "parent": "chest", "point": list(human.point((15.5, 8.5+bob))), "role": "head", "radius": 0}]
        for name, parent, point, role in (
            ("head_left", "head", (10.6, 8.5+bob), "head_edge"),
            ("head_right", "head", (20.8, 8.5+bob), "head_edge"),
            ("waist_left", "pelvis", (left, 18.7+bob), "waist_edge"),
            ("waist_right", "pelvis", (right, 18.7+bob), "waist_edge"),
        ):
            nodes.append({"id": name, "parent": parent, "point": list(human.point(point)), "role": role, "radius": 0})
        for family, limbs, parent, roles in (("leg", human.legs, "pelvis", ("hip", "knee", "foot")),
                                              ("arm", human.arms, "chest", ("shoulder", "elbow", "hand"))):
            for index, points in enumerate(limbs):
                previous = parent
                for joint, point in zip(roles, points):
                    name = f"{family}_{index}_{joint}"
                    nodes.append({"id": name, "parent": previous, "point": list(human.point(point)), "role": joint, "radius": 0})
                    previous = name
        canvas.attachments.append({"type": "anatomy_graph", "schema_version": 1, "profile": morphology.body_plan,
                                   "view": direction, "action": pose, "ground_anchor": list(human.point((15.5, 28))),
                                   "proportions": morphology.values,
                                   **({"posture": morphology.posture} if hasattr(morphology, "posture") else {}),
                                   "equipment_fitted": human.equipment_fitted, "nodes": nodes})


def _draw_head(human: Human, back: bool, side: bool, bob: float, skin: RGBA,
               shadow: RGBA, eye: RGBA, hair: RGBA, light: RGBA,
               dark: RGBA, style: str) -> None:
    def p(color: RGBA, *points: Point) -> None:
        human.plane(color, *((x, y + bob) for x, y in points))

    def d(color: RGBA, x: float, y: float, rx: float, ry: float) -> None:
        human.dot(color, x, y + bob, rx, ry)

    if side:
        p(dark, (10.25, 8.0), (11.1, 5.75), (13.8, 3.9), (17.1, 4.15),
          (19.5, 5.8), (20.4, 8.5), (19.2, 12.6), (16.0, 13.7), (12.25, 12.6), (10.6, 10.9))
        p(skin, (16.5, 6.75), (19.0, 6.65), (20.3, 7.9), (20.4, 9.25),
          (21.3, 10.2), (20.35, 10.8), (20.2, 12.1), (18.6, 13.5),
          (16.4, 13.55), (14.7, 12.3), (14.2, 10.1))
        p(shadow, (15.1, 11.35), (17.45, 12.57), (20.05, 12.15),
          (18.6, 13.5), (16.4, 13.55), (14.7, 12.3))
        d(shadow, 15.3, 10.5, .65, .8)
        blush = (min(255, skin[0]), max(0, skin[1] - 34), max(0, skin[2] - 28), skin[3])
        d(blush, 17.6, 10.7, .55, .35)
        d(eye, 18.65, 9.2, .4, .54)
        p(hair, (10.6, 7.2), (12.0, 5.5), (14.05, 4.0), (17.4, 4.0),
          (19.65, 5.7), (20.35, 7.9), (18.2, 7.35), (16.7, 8.0),
          (15.55, 9.65), (13.9, 9.35), (13.9, 11.7), (11.35, 11.15), (10.25, 9.3))
        p(light, (11.4, 7.5), (13.2, 5.2), (15.9, 4.6), (18.1, 5.3),
          (15.25, 5.55), (13.35, 6.25))
    else:
        p(dark, (10.6, 7.7), (11.4, 5.7), (13.4, 4.2), (16.7, 3.75),
          (19.15, 4.55), (20.8, 6.5), (21.25, 9.15), (20.5, 11.75),
          (18.25, 13.35), (15, 13.65), (12.15, 12.75), (10.55, 10.5))
        if back:
            p(hair, (10.8, 8.1), (12.2, 5.45), (14.5, 4.35), (17.6, 4.0),
              (20.0, 5.45), (20.65, 7.6), (19.4, 10.3), (17.55, 11.8),
              (14.75, 11.3), (12.6, 10.7))
            p(light, (12.0, 6.5), (14.25, 4.75), (17.25, 4.35), (19.6, 5.65),
              (16.95, 5.45), (14.35, 6.15), (12.8, 7.35))
        else:
            d(shadow, 11, 10.45, .8, .95)
            d(shadow, 20.1, 10.45, .8, .95)
            p(skin, (11.8, 7.35), (14.25, 6.5), (17.65, 6.7), (19.55, 7.8),
              (20.1, 10.2), (19.25, 12.0), (17.4, 13.5), (14.45, 13.8),
              (12.4, 12.5), (11.35, 10.7))
            p(shadow, (15.95, 13.05), (18.2, 12.35), (19.55, 11.0),
              (19.3, 12.15), (17.4, 13.5), (14.45, 13.8), (12.95, 12.95))
            blush = (min(255, skin[0]), max(0, skin[1] - 34), max(0, skin[2] - 28), skin[3])
            d(blush, 12.55, 11.15, .55, .32)
            d(blush, 18.75, 11.15, .55, .32)
            d(eye, 13.55, 9.85, .35, .52)
            d(eye, 17.82, 9.85, .35, .52)
            d(shadow, 15.65, 11.15, .35, .22)
            fringe = 7.2 if style == "crop" else 8.25
            p(hair, (10.6, 8.85), (11.45, 6.0), (13.45, 4.25), (16.8, 3.75),
              (19.1, 4.55), (20.8, 6.65), (20.65, 9.4), (19.2, 9.05),
              (18.2, 7.25), (16.2, 7.55), (14.25, fringe), (14.65, 6.85), (11.9, 8.6), (11.5, 10))
            p(light, (11.9, 7.0), (13.8, 5.0), (16.4, 4.45),
              (18.35, 5.0), (15.75, 5.4), (13.75, 6.7))

    if style == "ponytail":
        base = 11.5 if side else 18.5 if back else 11.5
        end = base - 3.25 if side or not back else base + 3.25
        p(dark, (base - 1.15, 8.8), (base + 1.0, 9.55),
          (end + 1.0, 12.65), (end + .65, 14.2), (end - .9, 13.85),
          (end - 1.5, 12.25), (base - 2, 10.3))
        p(hair, (base - .8, 9.65), (end - .25, 11),
          (end - .65, 12.65), (end - 1.4, 11.9), (base - 1.75, 10.5))
    elif style == "swept":
        p(hair, (11.85, 6.5), (12.15, 4.3), (14.35, 3.25), (16.65, 3.0),
          (15.75, 3.85), (18.65, 3.95), (18.15, 4.65), (13.95, 5.25))


def _draw_hat(human: Human, back: bool, side: bool, bob: float, hat: RGBA, ribbon: RGBA) -> None:
    offset = .5 if side else 0
    def p(color: RGBA, *points: Point) -> None:
        human.plane(color, *((x + offset, y + bob) for x, y in points))

    p(darken(hat, .72), (9, 6.35), (11.6, 5.35), (20.4, 5.4), (22.35, 6.35),
      (21.45, 7.35), (18.65, 7.8), (12, 7.65), (9.5, 7.2))
    p(hat, (11.5, 6.5), (12.3, 3.65), (14.45, 2.75), (17.6, 2.75),
      (19.15, 3.4), (20.1, 6.3), (17.2, 7.1), (13.8, 7.0))
    p(brighten(hat, 1.22), (12.55, 4.05), (14.5, 3.0), (17.75, 3.0),
      (18.35, 3.7), (14.7, 3.8), (12.55, 4.95))
    p(ribbon, (11.9, 5.25), (14.4, 5.95), (17.9, 5.95),
      (19.65, 5.25), (19.9, 6.18), (17.4, 6.55), (13.8, 6.6), (11.65, 6.2))
    if not back:
        human.dot(brighten(hat, 1.28), 17.6 + offset, 6.15 + bob, .3, .3)
