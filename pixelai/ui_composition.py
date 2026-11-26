"""UI composition zones, sparse ornament anchors and fixed-cap resize contracts."""

from pixelai.canvas import Canvas
from pixelai.color import brighten, darken, parse_color


PROFILES = ("quiet", "brackets", "header", "sidebar", "footer", "tab")
STATES = ("normal", "hover", "pressed", "selected", "disabled", "focus")


def build_layout(width, height, options, origin=(0, 0)):
    if type(width) is not int or type(height) is not int or width < 32 or height < 24:
        raise ValueError("UI composition requires native w>=32,h>=24")
    if not isinstance(options, dict) or set(options)-{"profile", "border", "padding", "motif", "ornament_budget", "content_min"}:
        raise ValueError("composition accepts profile, border, padding, motif, ornament_budget and content_min only")
    profile = options.get("profile", "quiet")
    if profile not in PROFILES:
        raise ValueError(f"composition.profile must be one of {', '.join(PROFILES)}")
    border, padding = options.get("border", 3), options.get("padding", 3)
    if type(border) is not int or not 2 <= border <= 6 or type(padding) is not int or not 2 <= padding <= 8:
        raise ValueError("composition border must be integer [2,6], padding integer [2,8]")
    motif = options.get("motif", "facet")
    if motif not in ("facet", "stud", "chevron"):
        raise ValueError("composition.motif must be facet, stud or chevron")
    budget = options.get("ornament_budget", 4)
    if type(budget) is not int or not 0 <= budget <= 4:
        raise ValueError("composition.ornament_budget must be integer [0,4]")
    if profile == "quiet" and "motif" in options:
        raise ValueError("motif is inactive for quiet composition")
    chrome = {side: border for side in ("left", "top", "right", "bottom")}
    if profile == "brackets":
        chrome = {side: border+3 for side in chrome}
    if profile in ("header", "tab"):
        chrome["top"] += 8
    if profile == "sidebar":
        chrome["left"] += 8
    if profile == "footer":
        chrome["bottom"] += 8
    caps = {side: max(border+5, value) for side, value in chrome.items()}
    if profile == "tab":
        caps["left"] += 8
    if caps["left"]+caps["right"] >= width or caps["top"]+caps["bottom"] >= height:
        raise ValueError("Composition fixed caps leave no stretch area; increase component dimensions")
    x, y = origin
    content = {"min": [x+chrome["left"]+padding, y+chrome["top"]+padding],
               "max": [x+width-chrome["right"]-padding, y+height-chrome["bottom"]-padding]}
    minimum = options.get("content_min", [12, 8])
    if not isinstance(minimum, list) or len(minimum) != 2 or any(type(value) is not int or value < 1 for value in minimum):
        raise ValueError("composition.content_min requires two positive integer dimensions")
    if any(content["max"][axis]-content["min"][axis] < minimum[axis] for axis in range(2)):
        raise ValueError("Composition cannot fit the required content area; increase dimensions or reduce chrome/padding")
    positions = {
        "quiet": (), "brackets": ("tl", "tr", "bl", "br"), "header": ("tl", "tr"),
        "sidebar": ("tl", "bl"), "footer": ("bl", "br"), "tab": ("tl",),
    }[profile][:budget]
    anchors = []
    for corner in positions:
        anchors.append({"id": corner, "radius":2,"point": [x+border+2 if corner[1] == "l" else x+width-border-3,
                                                y+border+2 if corner[0] == "t" else y+height-border-3]})
    bounds = {"min": [x, y], "max": [x+width, y+height]}
    cuts = {"min": [x+caps["left"], y+caps["top"]], "max": [x+width-caps["right"], y+height-caps["bottom"]]}
    nodes = [{"id": "origin", "parent": None, "role": "layout_origin", "point": [x, y], "radius": 0}]
    for name, rectangle, role in (("bounds", bounds, "bounds_corner"), ("content", content, "content_corner"), ("cuts", cuts, "slice_corner")):
        for index, point in enumerate((rectangle["min"], [rectangle["max"][0], rectangle["min"][1]], rectangle["max"], [rectangle["min"][0], rectangle["max"][1]])):
            nodes.append({"id": f"{name}_{index}", "parent": "origin", "role": role, "point": list(point), "radius": 0})
    for anchor in anchors:
        nodes.append({"id": f"ornament_{anchor['id']}", "parent": "origin", "role": "ornament_anchor", "point": anchor["point"], "radius": 2})
    return {"type": "ui_graph", "schema_version": 1, "profile": profile, "ground_anchor": [x, y], "nodes": nodes,
            "bounds": bounds, "content": content, "cuts": cuts, "anchors": anchors, "motif": motif,
            "chrome": chrome, "border": border}


def draw_composition(canvas, x, y, palette, op):
    from pixelai.ui import _THEMES
    from pixelai.schema import UNIVERSAL_OP_FIELDS
    allowed = {"x", "y", "w", "h", "kind", "component", "theme", "state", "color", "composition"}
    inactive = set(op)-allowed-UNIVERSAL_OP_FIELDS
    if inactive:
        raise ValueError("UI composition has inactive/unsupported fields: "+", ".join(sorted(inactive)))
    kind = str(op.get("kind", op.get("component", "panel"))).lower()
    theme, state = str(op.get("theme", "wood")).lower(), str(op.get("state", "normal")).lower()
    if kind not in ("panel", "button", "slot") or theme not in _THEMES or state not in STATES:
        raise ValueError("Composition requires panel/button/slot, a known theme and normal/hover/pressed/selected/disabled/focus state")
    width, height = op.get("w", 64), op.get("h", 40)
    layout = build_layout(width, height, op["composition"])
    local = Canvas(width, height)
    base, light, _, inner = _THEMES[theme]
    if "color" in op:
        base = parse_color(op["color"], palette)
    if state == "hover":
        base, inner = brighten(base, 1.14), brighten(inner, 1.08)
    elif state == "pressed":
        base, inner = darken(base, .82), darken(inner, .92)
    elif state == "disabled":
        def muted(color):
            value = round(sum(color[:3])/3*.75)
            return value, value, value, color[3]
        base, inner = muted(base), muted(inner)
    light = brighten(base, 1.22)
    border, chrome = layout["border"], layout["chrome"]
    outline = [(3,1),(width-4,1),(width-2,3),(width-2,height-4),(width-4,height-2),(3,height-2),(1,height-4),(1,3)]
    if layout["profile"] == "tab":
        cap = layout["cuts"]["min"][0]
        outline = [(3,1),(cap-3,1),(cap-1,5),(width-4,5),(width-2,7),(width-2,height-4),(width-4,height-2),(3,height-2),(1,height-4),(1,3)]
    local.draw_polygon(outline, base)
    local.clip_to_opaque = True
    local.draw_rect(1,1,width-2,2,darken(base,.85) if state == "pressed" else light)
    local.draw_rect(1,1,2,height-2,darken(base,.85) if state == "pressed" else light)
    local.draw_rect(width-3,1,2,height-2,darken(base,.86))
    local.draw_rect(1,height-3,width-2,2,darken(base,.86))
    local.draw_rect(chrome["left"],chrome["top"],width-chrome["left"]-chrome["right"],height-chrome["top"]-chrome["bottom"],inner)
    for anchor in layout["anchors"]:
        ax, ay = anchor["point"]
        if layout["motif"] == "facet":
            local.draw_polygon([(ax-2,ay),(ax,ay-2),(ax+2,ay),(ax,ay+2)],light)
            local.draw_polygon([(ax,ay),(ax+2,ay),(ax,ay+2)],darken(base,.83))
        elif layout["motif"] == "stud":
            local.draw_rect(ax-1,ay-1,3,3,light)
            local.set_pixel(ax+1,ay+1,base)
        else:
            local.draw_line(ax-2,ay-1,ax,ay+1,light)
            local.draw_line(ax,ay+1,ax+2,ay-1,light)
    signal = (90,190,184,255) if state == "selected" else ((38,72,88,255) if sum(base[:3])>480 else (244,244,220,255))
    if state == "selected":
        local.draw_rect(3,3,2,height-6,signal)
    if state in ("focus", "selected"):
        for ax, ay, sx, sy in ((3,3,1,1),(width-4,3,-1,1),(3,height-4,1,-1),(width-4,height-4,-1,-1)):
            local.draw_line(ax,ay,ax+sx*3,ay,signal)
            local.draw_line(ax,ay,ax,ay+sy*3,signal)
    local.clip_to_opaque = False
    canvas.blit(local,x,y)
    graph = build_layout(width,height,op["composition"],(x,y))
    graph.pop("chrome")
    graph.pop("border")
    graph["state"] = state
    canvas.attachments.append(graph)
