"""Bounded body lean and crouch composed with inspectable proportions."""

import math


class PosturedBody:
    """Deform torso/legs while translating the head as a complete mass.

    This is a native pose control, not IK, balance simulation or perspective
    rotation. Points at/below the ground line stay fixed.
    """

    def __init__(self, body, options):
        if not isinstance(options, dict) or set(options) - {"lean", "crouch"}:
            raise ValueError("posture accepts lean and crouch only")
        self.body = body
        self.body_plan, self.values = body.body_plan, body.values
        self.posture = {"lean": options.get("lean", 0), "crouch": options.get("crouch", 0)}
        for name, (low, high) in {"lean": (-.15, .15), "crouch": (0, 1.5)}.items():
            value = self.posture[name]
            if type(value) not in (int, float) or not math.isfinite(value) or not low <= value <= high:
                raise ValueError(f"posture.{name} must be between {low} and {high}")
        self.neck, self.hip = body.target_y[1], body.target_y[4]

    def _deform(self, point):
        x, y = point
        support = min(1, max(0, (28-y)/(28-self.hip)))
        return (x+self.posture["lean"]*max(0, 28-max(self.neck, y)),
                y+self.posture["crouch"]*support)

    def point(self, point):
        return self._deform(self.body.point(point))

    def inverse_point(self, point):
        x, y = point
        crouch = self.posture["crouch"]
        if y <= self.hip+crouch:
            y -= crouch
        elif y < 28:
            ratio = crouch/(28-self.hip)
            y = (y-28*ratio)/(1-ratio)
        x -= self.posture["lean"]*max(0, 28-max(self.neck, y))
        return self.body.inverse_point((x, y))

    def radii(self, x, y, rx, ry):
        width, _ = self.body.radii(x, y, rx, ry)
        return width, (self.point((x, y+ry))[1]-self.point((x, y-ry))[1])/2
