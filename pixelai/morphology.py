"""Piecewise body proportions anchored to the native character ground line."""

import math


BODY_PLANS = {
    "balanced": (1, 1, 1, 1, 1, 1, 1),
    "stocky": (1.05, 1.00, 1.28, 1.25, 1.18, .95, .80),
    "slender": (.88, .90, .82, .76, .86, 1.02, 1.10),
    "compact": (1.08, 1.08, .94, .96, .96, .85, .78),
    "long_legged": (.88, .86, .94, .86, .90, .88, 1.24),
    "broad_shouldered": (.95, .88, 1.35, 1.02, .94, 1.08, .92),
    "heavy": (1.02, .95, 1.27, 1.35, 1.26, 1.02, .85),
}
FIELDS = ("head_width", "head_height", "shoulder_width", "waist_width", "pelvis_width", "torso_length", "leg_length")


class Morphology:
    def __init__(self, options):
        if not isinstance(options, dict) or set(options) - {"body_plan", *FIELDS}:
            raise ValueError("morphology contains unknown body proportion fields")
        self.body_plan = options.get("body_plan", "balanced")
        if not isinstance(self.body_plan, str) or self.body_plan not in BODY_PLANS:
            raise ValueError(f"Unknown body_plan; choose {', '.join(BODY_PLANS)}")
        self.values = dict(zip(FIELDS, BODY_PLANS[self.body_plan]))
        for name in FIELDS:
            value = options.get(name, self.values[name])
            low, high = (.7, 1.2) if name in ("head_height", "torso_length") else (.65, 1.3) if name == "leg_length" else (.65, 1.5)
            if type(value) not in (int, float) or not math.isfinite(value) or not low <= value <= high:
                raise ValueError(f"morphology.{name} must be between {low} and {high}")
            self.values[name] = value
        hip = 28 - 6.8*self.values["leg_length"]
        shoulder = hip - 6.6*self.values["torso_length"]
        neck = shoulder - .8*self.values["torso_length"]
        head_top = neck - 10.8*self.values["head_height"]
        if head_top < 2:
            raise ValueError("Combined morphology exceeds native headroom; reduce head/torso/leg lengths")
        self.source_y = (3, 13.8, 14.6, 18.7, 21.2, 28)
        waist = shoulder + (18.7-14.6)*self.values["torso_length"]
        self.target_y = (head_top, neck, shoulder, waist, hip, 28)
        self.widths = (self.values["head_width"], self.values["head_width"], self.values["shoulder_width"],
                       self.values["waist_width"], self.values["pelvis_width"], self.values["pelvis_width"])

    def _interpolate(self, y, values, extrapolate=False):
        if y <= self.source_y[0]:
            return values[0] + ((y-self.source_y[0])*self.values["head_height"] if extrapolate else 0)
        if y >= self.source_y[-1]:
            return values[-1] + (y-self.source_y[-1] if extrapolate else 0)
        for index in range(len(self.source_y)-1):
            start, end = self.source_y[index:index+2]
            if start <= y <= end:
                t = (y-start)/(end-start)
                return values[index]*(1-t) + values[index+1]*t
        raise ValueError("Invalid morphology coordinate")

    def point(self, point):
        x, y = point
        return 15.5 + (x-15.5)*self._interpolate(y, self.widths), self._interpolate(y, self.target_y, True)

    def radii(self, x, y, rx, ry):
        return rx*self._interpolate(y, self.widths), (self.point((x, y+ry))[1]-self.point((x, y-ry))[1])/2

    def inverse_point(self, point):
        x, y = point
        if y <= self.target_y[0]:
            source_y = self.source_y[0] + (y-self.target_y[0])/self.values["head_height"]
        elif y >= 28:
            source_y = y
        else:
            for index in range(len(self.target_y)-1):
                start, end = self.target_y[index:index+2]
                if start <= y <= end:
                    t = (y-start)/(end-start)
                    source_y = self.source_y[index]*(1-t) + self.source_y[index+1]*t
                    break
        return 15.5+(x-15.5)/self._interpolate(source_y, self.widths), source_y
