"""Structural diagnostics use rendered generator graphs, not profile names."""

from pixelai.runner import run_frames


def growth_signature(graph, geometry=True, mirror=False):
    nodes = {node["id"]: node for node in graph["nodes"]}
    children = {name: [] for name in nodes}
    roots = []
    for node in nodes.values():
        if node["parent"] is None:
            roots.append(node["id"])
        else:
            children[node["parent"]].append(node["id"])
    xs, ys = [node["point"][0] for node in nodes.values()], [node["point"][1] for node in nodes.values()]
    scale = max(max(xs)-min(xs), max(ys)-min(ys), 1)
    anchor = graph["ground_anchor"]

    def normalized(value):
        return round(value / scale, 6) or 0.0

    def visit(name):
        node = nodes[name]
        position = ((normalized((node["point"][0]-anchor[0]) * (-1 if mirror else 1)),
                     normalized(node["point"][1]-anchor[1]), normalized(node["radius"])) if geometry else ())
        return node["role"], position, tuple(sorted(visit(child) for child in children[name]))

    return tuple(sorted(visit(name) for name in roots))


def compare_growth(first, second):
    return {"topology_equal": growth_signature(first, False) == growth_signature(second, False),
            "normalized_geometry_equal": growth_signature(first) == growth_signature(second),
            "mirrored_geometry_equal": growth_signature(first) == growth_signature(second, mirror=True),
            "approval": None}


def analyze_structures(spec, other=None, frame=0, full=False):
    frames, _ = run_frames(spec)
    if type(frame) is not int or not 0 <= frame < len(frames):
        raise ValueError("Requested structure frame is outside the rendered sequence")
    graphs = [record for record in frames[frame].attachments if record.get("type") == "growth_graph"]
    summaries = [{"index": index, "profile": graph["profile"], "node_count": len(graph["nodes"]),
                  "root_count": sum(node["role"] == "root" for node in graph["nodes"]),
                  "ground_anchor": graph["ground_anchor"], **({"graph": graph} if full else {})}
                 for index, graph in enumerate(graphs)]
    comparisons = []
    if other is not None:
        other_frames, _ = run_frames(other)
        if frame >= len(other_frames):
            raise ValueError("Comparison structure frame is outside the rendered sequence")
        other_graphs = [record for record in other_frames[frame].attachments if record.get("type") == "growth_graph"]
        comparisons = [{"first": i, "second": j, **compare_growth(first, second)}
                       for i, first in enumerate(graphs) for j, second in enumerate(other_graphs)]
    return {"schema_version": 1, "frame": frame, "structures": summaries, "comparisons": comparisons,
            "limitations": ["Growth graphs only in this increment", "Structural inequality does not establish artistic quality or originality"]}
