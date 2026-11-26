"""Contract-required UI geometry, content capacity and visible state coverage."""

import hashlib

from pixelai.nine_slice import resize_ui


def validate_ui_delivery(options,states):
    if not isinstance(options,dict) or set(options)-{"target_sizes","content_min","distinct_states"}:
        raise ValueError("delivery.ui accepts target_sizes, content_min and distinct_states only")
    sizes = options.get("target_sizes")
    if not isinstance(sizes,list) or not 1<=len(sizes)<=16 or any(not isinstance(size,list) or len(size)!=2 or any(type(v) is not int or v<1 for v in size) for size in sizes):
        raise ValueError("delivery.ui.target_sizes requires 1..16 positive integer size pairs")
    if len({tuple(size) for size in sizes})!=len(sizes) or sum(w*h for w,h in sizes)>4000000:
        raise ValueError("UI target sizes must be unique and within the pixel budget")
    minimum = options.get("content_min",[12,8])
    if not isinstance(minimum,list) or len(minimum)!=2 or any(type(v) is not int or v<1 for v in minimum):
        raise ValueError("delivery.ui.content_min requires positive integer dimensions")
    if "distinct_states" in options and type(options["distinct_states"]) is not bool:
        raise ValueError("delivery.ui.distinct_states must be a boolean")
    if options.get("distinct_states") and len(states)<2:
        raise ValueError("Distinct UI states require at least two delivery.states")


def verify_ui_delivery(frames,texture,options,states):
    validate_ui_delivery(options,states)
    if len(frames)*sum(w*h for w,h in options["target_sizes"])>4000000 or sum(frame["rect"][2]*frame["rect"][3] for frame in frames)>4000000:
        raise ValueError("UI delivery frame/target pixel budget exhausted")
    minimum = options.get("content_min",[12,8])
    groups,checks = {},[]
    for frame in frames:
        ui = frame.get("ui")
        if ui is None:
            raise ValueError("UI delivery requires a slice contract in every reachable frame")
        group = (ui["profile"],frame.get("view"),frame.get("action"))
        geometry = {key:ui[key] for key in ("bounds","cuts","content","anchors","motif")}
        entry = groups.setdefault(group,{"geometry":geometry,"states":{}})
        if entry["geometry"]!=geometry:
            raise ValueError("UI slice/content geometry must remain stable through each component's states")
        content = ui["content"]
        if any(content["max"][axis]-content["min"][axis]<minimum[axis] for axis in range(2)):
            raise ValueError("Native UI content area is below the delivery minimum")
        x,y,w,h = frame["rect"]
        image = texture.crop((x,y,x+w,y+h))
        component = image.crop((*ui["bounds"]["min"],*ui["bounds"]["max"]))
        digest = hashlib.sha256(str(component.size).encode())
        for pixel in getattr(component,"get_flattened_data",component.getdata)():
            digest.update(bytes(pixel if pixel[3] else (0,0,0,0)))
        entry["states"].setdefault(ui["state"],set()).add(digest.hexdigest())
        for size in options["target_sizes"]:
            _,report = resize_ui(image,ui,size)
            content = report["content"]
            if not report["fixed_corners_preserved"] or any(content["max"][axis]-content["min"][axis]<minimum[axis] for axis in range(2)):
                raise ValueError("Resized UI violates fixed corners or minimum content area")
            checks.append({"frame":frame["id"],"state":ui["state"],**report})
    if options.get("distinct_states"):
        for group,entry in groups.items():
            missing = set(states)-set(entry["states"])
            if missing:
                raise ValueError(f"Missing UI states for {group}: {', '.join(sorted(missing))}")
            for index,first in enumerate(states):
                for second in states[index+1:]:
                    if entry["states"][first]==entry["states"][second]:
                        raise ValueError(f"UI states {first}/{second} contain identical exported component pixels")
    return {"status":"checked","trials":checks,"scope":"stable slice geometry, native/resized content capacity and requested exported state distinctions",
            "unverified":["text/localization fit","input behavior","artistic hierarchy"]}
