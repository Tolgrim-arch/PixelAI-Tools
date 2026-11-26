"""Deterministic native-grid motion with swept convex-region blocking."""

from pixelai.geometry import overlap, swept_overlap, world_regions


def simulate_motion(actors, times, frame_sampler, mode="report", budget=10000):
    """Advance at fixed 1ms steps, independent of requested screenshot times.

    Actors are processed by stable id; X is resolved before Y. This is a
    reference grid solver, not a mass/impulse physics engine.
    """
    if mode not in ("report", "block") or type(budget) is not int or budget < 1:
        raise ValueError("Motion requires collision_mode report/block and a positive motion_budget")
    entries = {actor["id"]: (actor, data, track) for actor, data, track in actors}
    order = sorted(entries)
    positions = {name: list(next(state for state in reversed(entries[name][2]) if state["at_ms"] <= 0)["position"]) for name in order}
    contacts = {}
    work = 0
    cache_time, frame_cache, region_cache = None, {}, {}

    def spend():
        nonlocal work
        work += 1
        if work > budget:
            raise ValueError("Reference motion budget exhausted; shorten the scene or increase motion_budget")

    def regions(name, time):
        nonlocal cache_time
        if cache_time != time:
            frame_cache.clear()
            region_cache.clear()
            cache_time = time
        key = name, tuple(positions[name])
        if key in region_cache:
            return region_cache[key]
        actor, data, track = entries[name]
        if name not in frame_cache:
            state = next(state for state in reversed(track) if state["at_ms"] <= time)
            frame_cache[name] = frame_sampler(data, state["clip"], time-state["clip_started_ms"])
        frame = frame_cache[name]
        origin = (round(positions[name][0]-frame["pivot"][0]), round(positions[name][1]-frame["pivot"][1]))
        result = [region["polygon"] for region in world_regions(frame, origin) if region["role"] == "collision"]
        region_cache[key] = result
        return result

    def check_penetration(time):
        if mode != "block":
            return
        for index, name in enumerate(order):
            for other in order[index+1:]:
                if any(overlap(first, second) for first in regions(name, time) for second in regions(other, time)):
                    raise ValueError(f"Collision geometry overlaps at {time}ms: {name}/{other}; fix initial positions or state geometry")

    check_penetration(0)
    snapshots = {0: {name: list(position) for name, position in positions.items()}} if 0 in times else {}
    requested = set(times)
    for time in range(1, max(times)+1):
        spend()
        for name in order:
            actor, _, _ = entries[name]
            explicit = next((event["position"] for event in actor.get("timeline", []) if event["at_ms"] == time and "position" in event), None)
            velocity = actor.get("velocity", [0, 0])
            delta = ([explicit[axis]-positions[name][axis] for axis in range(2)] if explicit is not None else
                     [round(velocity[axis]*time/1000)-round(velocity[axis]*(time-1)/1000) for axis in range(2)])
            for axis in range(2):
                step = 1 if delta[axis] > 0 else -1
                for _ in range(abs(delta[axis])):
                    spend()
                    movement = [0, 0]
                    movement[axis] = step
                    blockers = []
                    if mode == "block":
                        own = regions(name, time)
                        for other in order:
                            if name != other and any(swept_overlap(first, second, movement) for first in own for second in regions(other, time)):
                                blockers.append(other)
                    if blockers:
                        for other in blockers:
                            contact = contacts.setdefault((name, other), {"actor": name, "obstacle": other, "first_ms": time, "last_ms": time, "attempts": 0})
                            contact["last_ms"] = time
                            contact["attempts"] += 1
                        break
                    positions[name][axis] += step
        check_penetration(time)
        if time in requested:
            snapshots[time] = {name: list(position) for name, position in positions.items()}
    return snapshots, {"mode": mode, "fixed_step_ms": 1, "work_units": work, "budget": budget,
                       "contacts": list(contacts.values()), "solver": "stable actor ids, X then Y native-grid steps with convex sweeps"}
