"""Measure declared planted sockets without inferring artistic intent."""

import math

from pixelai.manifest import _integer


def contact_times(windows, actors, end_ms, budget=10000):
    """Validate continuous plant episodes and bound their 1ms observations."""
    if not isinstance(windows, list):
        raise ValueError("planted_contacts must be an array")
    _integer(budget, "contact_budget", 1)
    times, work = set(), 0
    for window in windows:
        if not isinstance(window, dict) or set(window) - {"actor", "socket", "start_ms", "end_ms", "tolerance_px"}:
            raise ValueError("Planted contact contains unsupported fields")
        if not isinstance(window.get("actor"), str) or window["actor"] not in actors:
            raise ValueError("Planted contact references a missing actor")
        if not isinstance(window.get("socket"), str) or not window["socket"]:
            raise ValueError("Planted contact requires a socket name")
        start = _integer(window.get("start_ms"), "contact.start_ms")
        end = _integer(window.get("end_ms"), "contact.end_ms")
        if start >= end or end > end_ms:
            raise ValueError("Planted contact requires start_ms < end_ms within the scene duration")
        tolerance = window.get("tolerance_px", 0)
        if type(tolerance) not in (int, float) or not math.isfinite(tolerance) or tolerance < 0:
            raise ValueError("contact.tolerance_px must be finite and nonnegative")
        work += end-start+1
        if work > budget:
            raise ValueError("Contact observation budget exhausted; shorten windows or increase contact_budget")
        times.update(range(start, end+1))
    return times


def assess_contacts(windows, actors, frame_sampler, positions=None):
    """Track every millisecond against the socket's initial world position."""
    episodes = []
    for window in windows:
        actor, data, track = actors[window["actor"]]
        baseline, worst, peak, peak_time = None, 0, None, None
        for time in range(window["start_ms"], window["end_ms"]+1):
            state = next(state for state in reversed(track) if state["at_ms"] <= time)
            frame = frame_sampler(data, state["clip"], time-state["clip_started_ms"])
            socket = frame.get("sockets", {}).get(window["socket"])
            if socket is None:
                raise ValueError(f"Planted socket {window['socket']} missing for {window['actor']} at {time}ms")
            position = positions[time][window["actor"]] if positions is not None else state["position"]
            world = [round(position[axis]-frame["pivot"][axis])+socket[axis] for axis in range(2)]
            if baseline is None:
                baseline, peak, peak_time = world, world, time
            distance = math.dist(baseline, world)
            if distance > worst:
                worst, peak, peak_time = distance, world, time
        tolerance = window.get("tolerance_px", 0)
        episodes.append({**window, "tolerance_px": tolerance, "baseline_world": baseline,
                         "max_drift_px": worst, "peak_world": peak, "peak_ms": peak_time,
                         "observations": window["end_ms"]-window["start_ms"]+1,
                         "status": "failed" if worst > tolerance+1e-9 else "passed"})
    return {"status": "not_requested" if not episodes else "failed" if any(item["status"] == "failed" for item in episodes) else "passed",
            "fixed_step_ms": 1, "episodes": episodes,
            "scope": "declared socket drift only; does not prove foot-ground contact, weight or acting"}
