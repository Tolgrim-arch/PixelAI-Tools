"""Shared export timing and named-clip validation."""


def durations_ms(count, fps=8, values=None):
    if type(fps) not in (int, float) or fps <= 0:
        raise ValueError("fps must be positive")
    if values is None:
        return [max(1, round(1000 / fps))] * count
    if not isinstance(values, list) or len(values) != count or any(type(v) is not int or v < 1 for v in values):
        raise ValueError("durations_ms must contain one positive integer per rendered frame")
    return list(values)


def clips_by_index(count, clips=None):
    if clips is None:
        return {"default": {"frames": list(range(count)), "loop": True}}
    if not isinstance(clips, dict) or not clips:
        raise ValueError("clips must be a nonempty object")
    for name, clip in clips.items():
        if not isinstance(name, str) or not name or not isinstance(clip, dict) or type(clip.get("loop")) is not bool:
            raise ValueError("Each named clip requires a loop boolean")
        if "interruptible" in clip and type(clip["interruptible"]) is not bool:
            raise ValueError("clip.interruptible must be a boolean")
        indices = clip.get("frames")
        if not isinstance(indices, list) or not indices or any(type(i) is not int or not 0 <= i < count for i in indices):
            raise ValueError(f"Clip {name!r} references invalid frame indices")
    return clips


def validate_transitions(transitions, clips):
    if not isinstance(transitions, list):
        raise ValueError("transitions must be an array")
    for edge in transitions:
        if not isinstance(edge, dict) or not isinstance(edge.get("from"), str) or not isinstance(edge.get("to"), str) or edge["from"] not in clips or edge["to"] not in clips:
            raise ValueError("Transition references a missing clip")
    return transitions
