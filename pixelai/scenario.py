"""Explicit functional assertions for reference runtime evidence."""

from pixelai.manifest import _integer, _point


def validate_expectations(expectations, times, actors):
    if not isinstance(expectations, list):
        raise ValueError("expectations must be an array")
    for item in expectations:
        if not isinstance(item, dict) or set(item) - {"time_ms", "actor", "position", "clip", "before", "contacted", "event"}:
            raise ValueError("Scenario expectation contains unsupported fields")
        _integer(item.get("time_ms"), "expectation.time_ms")
        if item["time_ms"] not in times:
            raise ValueError("Expectation time must be included in times_ms")
        if not isinstance(item.get("actor"), str) or item["actor"] not in actors:
            raise ValueError("Expectation references a missing actor")
        if not set(item) & {"position", "clip", "before", "contacted", "event"}:
            raise ValueError("Expectation must assert position, clip, draw order, prior contact or event")
        if "event" in item and (not isinstance(item["event"], str) or not item["event"].strip()):
            raise ValueError("expectation.event must be a nonempty score event id")
        if "position" in item:
            point = _point(item["position"], "expectation.position")
            if any(type(value) is not int for value in point):
                raise ValueError("Expected positions must be native integer coordinates")
        if "clip" in item and (not isinstance(item["clip"], str) or item["clip"] not in actors[item["actor"]]["clips"]):
            raise ValueError("Expectation references a missing clip")
        for name in ("before", "contacted"):
            if name in item and (not isinstance(item[name], str) or item[name] not in actors or item[name] == item["actor"]):
                raise ValueError(f"expectation.{name} must reference another actor")


def assess_scenario(expectations, trace, motion=None, events=()):
    failures, assertions = [], 0
    by_time = {frame["time_ms"]: frame for frame in trace}
    for item in expectations:
        frame = by_time[item["time_ms"]]
        actors = {actor["actor"]: actor for actor in frame["actors"]}
        actual = actors[item["actor"]]
        if "event" in item:
            assertions += 1
            if not any(event["actor"] == item["actor"] and event["id"] == item["event"] and event["time_ms"] == item["time_ms"] for event in events):
                failures.append({"time_ms": item["time_ms"], "actor": item["actor"], "field": "event", "expected": item["event"], "actual": False})
        for key, actual_key in (("position", "world_position"), ("clip", "clip")):
            if key in item:
                assertions += 1
                if actual[actual_key] != item[key]:
                    failures.append({"time_ms": item["time_ms"], "actor": item["actor"], "field": key,
                                     "expected": item[key], "actual": actual[actual_key]})
        order = [actor["actor"] for actor in frame["actors"]]
        if "before" in item:
            assertions += 1
            if order.index(item["actor"]) >= order.index(item["before"]):
                failures.append({"time_ms": item["time_ms"], "actor": item["actor"], "field": "before", "expected": item["before"], "actual_draw_order": order})
        if "contacted" in item:
            assertions += 1
            if not any(contact["actor"] == item["actor"] and contact["obstacle"] == item["contacted"] and contact["first_ms"] <= item["time_ms"]
                       for contact in (motion or {}).get("contacts", [])):
                failures.append({"time_ms": item["time_ms"], "actor": item["actor"], "field": "contacted", "expected": item["contacted"], "actual": False})
    return {"status": "not_requested" if not assertions else "failed" if failures else "passed", "assertions": assertions, "failures": failures}
