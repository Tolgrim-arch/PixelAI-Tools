"""Explicit animation intent, timing beats and bounded gameplay event traces."""


def _text(value, label):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} must be a nonempty string")


def _integer(value, label):
    if type(value) is not int or value < 0:
        raise ValueError(f"{label} must be a nonnegative integer")
    return value


def source_records(frames, timings):
    return {index: {**next((item for item in frame.attachments if item.get("type") == "runtime"), {}),
                    "duration_ms": timings[index]}
            for index, frame in enumerate(frames)}


def validate_scores(clips, records):
    """Require complete ordered beat coverage and reachable timed events."""
    for clip in clips.values():
        if "score" not in clip:
            continue
        score = clip["score"]
        if not isinstance(score, dict) or set(score) - {"schema_version", "intent", "beats", "events"} or type(score.get("schema_version")) is not int or score["schema_version"] != 1:
            raise ValueError("Animation score requires schema_version 1 and supported fields")
        _text(score.get("intent"), "score.intent")
        sequence = [records[index] for index in clip["frames"]]
        beats = score.get("beats")
        if not isinstance(beats, list) or not beats:
            raise ValueError("Animation score requires nonempty beats")
        end, names = 0, set()
        for beat in beats:
            if not isinstance(beat, dict) or set(beat) != {"name", "purpose", "start", "end"}:
                raise ValueError("Score beat requires name, purpose, start and end only")
            _text(beat["name"], "beat.name")
            _text(beat["purpose"], "beat.purpose")
            start, stop = _integer(beat["start"], "beat.start"), _integer(beat["end"], "beat.end")
            if beat["name"] in names or start != end or stop <= start or stop > len(sequence):
                raise ValueError("Score beats must have unique names and contiguous ordered clip-slot coverage")
            end = stop
            names.add(beat["name"])
        if end != len(sequence):
            raise ValueError("Score beats must cover every clip slot")
        events = score.get("events", [])
        if not isinstance(events, list):
            raise ValueError("score.events must be an array")
        duration = sum(frame["duration_ms"] for frame in sequence)
        ids, previous = set(), -1
        for event in events:
            if not isinstance(event, dict) or set(event) - {"id", "name", "at_ms", "socket"}:
                raise ValueError("Score event contains unsupported fields")
            _text(event.get("id"), "event.id")
            _text(event.get("name"), "event.name")
            at = _integer(event.get("at_ms"), "event.at_ms")
            if event["id"] in ids or at < previous or at >= duration:
                raise ValueError("Score events require unique ids, ordered times and at_ms below clip duration")
            ids.add(event["id"])
            previous = at
            if "socket" in event:
                _text(event["socket"], "event.socket")
                elapsed = 0
                for frame in sequence:
                    elapsed += frame["duration_ms"]
                    if at < elapsed:
                        if event["socket"] not in frame.get("sockets", {}):
                            raise ValueError("Score event references a missing socket in its active frame")
                        break


def score_beats(clip, records):
    """Expose neutral timing metadata without author intent/purpose arguments."""
    sequence = [records[index] for index in clip["frames"]]
    boundaries = [0]
    for frame in sequence:
        boundaries.append(boundaries[-1]+frame["duration_ms"])
    return [{"name": beat["name"], "start_ms": boundaries[beat["start"]], "end_ms": boundaries[beat["end"]],
             "frames": clip["frames"][beat["start"]:beat["end"]]}
            for beat in clip.get("score", {}).get("beats", [])]


def timeline_events(actors, until_ms, budget=10000):
    """Emit events once per occurrence, independent of screenshot sampling."""
    if type(budget) is not int or budget < 1:
        raise ValueError("event_budget must be a positive integer")
    result = []
    for actor, data, track in actors:
        records = {frame["id"]: frame for frame in data["frames"]}
        # Position-only updates preserve the current clip phase.
        starts = [state for index, state in enumerate(track) if index == 0 or
                  (state["clip"], state["clip_started_ms"]) != (track[index-1]["clip"], track[index-1]["clip_started_ms"])]
        # A time-zero event replaces the initial state.
        starts = [state for index, state in enumerate(starts) if index == len(starts)-1 or starts[index+1]["at_ms"] != state["at_ms"]]
        for index, state in enumerate(starts):
            start = state["clip_started_ms"]
            stop = min(until_ms+1, starts[index+1]["at_ms"] if index+1 < len(starts) else until_ms+1)
            if stop <= start:
                continue
            clip = data["clips"][state["clip"]]
            events = clip.get("score", {}).get("events", [])
            duration = sum(records[name]["duration_ms"] for name in clip["frames"])
            for event in events:
                count = max(0, (stop-1-start-event["at_ms"])//duration+1) if clip["loop"] else int(start+event["at_ms"] < stop)
                if len(result)+count > budget:
                    raise ValueError("Animation event budget exhausted; shorten scene or increase event_budget")
                for cycle in range(count):
                    result.append({**event, "actor": actor["id"], "clip": state["clip"], "cycle": cycle,
                                   "time_ms": start+cycle*duration+event["at_ms"]})
    return sorted(result, key=lambda event: (event["time_ms"], event["actor"], event["id"]))
