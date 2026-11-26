"""Body-versus-limb movement diagnostics from actual rendered anatomy graphs."""

import math


BODY_ROLES = {"pelvis", "chest", "head"}
LIMB_ROLES = {"hip", "knee", "foot", "shoulder", "elbow", "hand"}


def analyze_motion(frames, timings, clips, full=False):
    graphs = []
    for index, frame in enumerate(frames):
        current = [item for item in frame.attachments if item.get("type") == "anatomy_graph"]
        if len(current) != 1:
            raise ValueError(f"Motion analysis requires exactly one anatomy graph in frame {index}; render one morphology/posture character per spec")
        graphs.append(current[0])
    topology = {node["id"]: (node["parent"], node["role"]) for node in graphs[0]["nodes"]}
    for graph in graphs[1:]:
        if {node["id"]: (node["parent"], node["role"]) for node in graph["nodes"]} != topology:
            raise ValueError("Motion analysis requires consistent joint ids, roles and parents throughout the sequence")
    relative = [{node["id"]: [node["point"][axis]-graph["ground_anchor"][axis] for axis in range(2)]
                 for node in graph["nodes"]} for graph in graphs]
    report = {}
    for name, clip in clips.items():
        indices = clip["frames"]
        transitions = []
        elapsed = timings[indices[0]]
        pairs = list(zip(indices, indices[1:]))
        if clip["loop"]:
            pairs.append((indices[-1], indices[0]))
        for slot, (first, second) in enumerate(pairs):
            deltas = {joint: math.dist(relative[first][joint], relative[second][joint]) for joint in topology}
            body = max((delta for joint, delta in deltas.items() if topology[joint][1] in BODY_ROLES), default=0)
            limbs = max((delta for joint, delta in deltas.items() if topology[joint][1] in LIMB_ROLES), default=0)
            transitions.append({"from_frame": first, "to_frame": second, "at_ms": elapsed,
                                "loop_join": slot == len(indices)-1,
                                "body_max_delta_px": body, "limb_max_delta_px": limbs,
                                "ground_delta_px": math.dist(graphs[first]["ground_anchor"], graphs[second]["ground_anchor"]),
                                "limb_without_body_motion": body == 0 and limbs > 0})
            if slot+1 < len(indices):
                elapsed += timings[indices[slot+1]]
        tracks = {}
        for joint, (_, role) in topology.items():
            path = [relative[index][joint] for index in indices]
            closed = path+[path[0]] if clip["loop"] else path
            tracks[joint] = {"role": role, "path_length_px": sum(math.dist(a, b) for a, b in zip(closed, closed[1:])),
                             "net_displacement_px": math.dist(path[0], path[-1]),
                             "span_px": [max(point[axis] for point in path)-min(point[axis] for point in path) for axis in range(2)],
                             **({"ground_relative_path": path} if full else {})}
        report[name] = {"duration_ms": sum(timings[index] for index in indices),
                        "body_motion_detected": any(item["body_max_delta_px"] > 0 for item in transitions),
                        "transitions": transitions, "joint_tracks": tracks,
                        "views": [graphs[index].get("view") for index in indices],
                        "actions": [graphs[index].get("action") for index in indices]}
    return {"clips": report, "coordinate_space": "native rendered pixels relative to each frame's ground anchor",
            "approval": None, "limitations": ["Motion magnitude does not establish acting, weight or balance",
                "Limb-only changes and intentional holds may be valid; review them against the requested performance",
                "View/action changes can move joints without expressive acting", "Tool tips are not anatomy joints"]}
