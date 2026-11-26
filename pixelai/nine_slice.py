"""Validated UI slice contracts and exported-pixel resize evidence."""

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import tempfile

from PIL import Image


def ui_contract(attachments):
    layouts = [item for item in attachments if item.get("type") == "ui_graph"]
    if len(layouts) != 1:
        return None
    return deepcopy({key: layouts[0][key] for key in ("schema_version", "profile", "state", "bounds", "cuts", "content", "anchors", "motif")})


def validate_ui(contract,width,height):
    if not isinstance(contract,dict) or set(contract) != {"schema_version","profile","state","bounds","cuts","content","anchors","motif"} or type(contract.get("schema_version")) is not int or contract["schema_version"] != 1:
        raise ValueError("UI contract requires schema_version 1 and supported fields")
    from pixelai.ui_composition import PROFILES, STATES
    if contract["profile"] not in PROFILES or contract["state"] not in STATES or contract["motif"] not in ("facet","stud","chevron"):
        raise ValueError("UI contract requires a supported profile, state and motif")
    for name in ("bounds","cuts","content"):
        rectangle = contract[name]
        if not isinstance(rectangle,dict) or set(rectangle) != {"min","max"}:
            raise ValueError(f"UI {name} requires min/max coordinate pairs")
        for point in rectangle.values():
            if not isinstance(point,list) or len(point) != 2 or any(type(value) is not int for value in point):
                raise ValueError("UI coordinates must be native integer pairs")
        if any(not 0 <= rectangle["min"][axis] < rectangle["max"][axis] <= (width,height)[axis] for axis in range(2)):
            raise ValueError(f"UI {name} lies outside the native frame or has no area")
    bounds,cuts,content = (contract[name] for name in ("bounds","cuts","content"))
    for axis in range(2):
        if not bounds["min"][axis] < cuts["min"][axis] < cuts["max"][axis] < bounds["max"][axis]:
            raise ValueError("UI cuts must leave positive fixed caps and a positive center")
        if not bounds["min"][axis] <= content["min"][axis] < content["max"][axis] <= bounds["max"][axis]:
            raise ValueError("UI content must remain inside component bounds")
    anchors = contract["anchors"]
    if not isinstance(anchors,list) or len(anchors)>4:
        raise ValueError("UI anchors require a bounded array")
    names = set()
    for anchor in anchors:
        if not isinstance(anchor,dict) or set(anchor) != {"id","point","radius"} or not isinstance(anchor["id"],str) or not anchor["id"] or anchor["id"] in names:
            raise ValueError("UI ornament anchors require unique ids, points and radii")
        names.add(anchor["id"])
        point,radius = anchor["point"],anchor["radius"]
        if not isinstance(point,list) or len(point)!=2 or any(type(value) is not int for value in point) or type(radius) is not int or radius<1:
            raise ValueError("UI ornament geometry must use integer coordinates and positive radius")
        for axis in range(2):
            if not ((bounds["min"][axis] <= point[axis]-radius and point[axis]+radius < cuts["min"][axis]) or
                    (cuts["max"][axis] <= point[axis]-radius and point[axis]+radius < bounds["max"][axis])):
                raise ValueError("UI ornaments must fit entirely within fixed corner caps")
        if all(point[axis]+radius >= content["min"][axis] and point[axis]-radius < content["max"][axis] for axis in range(2)):
            raise ValueError("UI ornament overlaps protected content")


def resize_ui(image,contract,size):
    validate_ui(contract,*image.size)
    if not isinstance(size,(list,tuple)) or len(size)!=2 or any(type(value) is not int or value<1 for value in size):
        raise ValueError("UI target size requires two positive integers")
    bounds,cuts,content = (contract[name] for name in ("bounds","cuts","content"))
    source_box = (*bounds["min"],*bounds["max"])
    source = image.crop(source_box)
    left,top = [cuts["min"][axis]-bounds["min"][axis] for axis in range(2)]
    right,bottom = [bounds["max"][axis]-cuts["max"][axis] for axis in range(2)]
    if size[0] <= left+right or size[1] <= top+bottom:
        raise ValueError("UI target size leaves no center after preserving fixed caps")
    target_content = {"min":[content["min"][axis]-bounds["min"][axis] for axis in range(2)],
                      "max":[size[axis]-(bounds["max"][axis]-content["max"][axis]) for axis in range(2)]}
    if any(target_content["min"][axis]>=target_content["max"][axis] for axis in range(2)):
        raise ValueError("UI target size leaves no protected content area")
    result = Image.new("RGBA",tuple(size))
    sx,sy = [0,left,source.width-right,source.width],[0,top,source.height-bottom,source.height]
    tx,ty = [0,left,size[0]-right,size[0]],[0,top,size[1]-bottom,size[1]]
    corners = []
    for row in range(3):
        for column in range(3):
            patch = source.crop((sx[column],sy[row],sx[column+1],sy[row+1]))
            destination = (tx[column],ty[row],tx[column+1],ty[row+1])
            result.paste(patch.resize((destination[2]-destination[0],destination[3]-destination[1]),Image.Resampling.NEAREST),destination[:2])
            if row != 1 and column != 1:
                corners.append(result.crop(destination).tobytes()==patch.tobytes())
    return result,{"size":list(size),"content":target_content,"fixed_corners_preserved":all(corners)}


def check_ui(manifest_path,frame_id,sizes,output):
    from pixelai.manifest import load_manifest
    data,texture = load_manifest(manifest_path)
    frame = next((item for item in data["frames"] if item["id"]==frame_id),None)
    if frame is None or "ui" not in frame:
        raise ValueError("uicheck requires a frame with an exported UI slice contract")
    x,y,w,h = frame["rect"]
    source = texture.crop((x,y,x+w,y+h))
    if not isinstance(sizes,(list,tuple)) or not 1<=len(sizes)<=16 or any(not isinstance(size,(list,tuple)) or len(size)!=2 or any(type(value) is not int or value<1 for value in size) for size in sizes):
        raise ValueError("uicheck requires 1..16 positive integer size pairs")
    if sum(size[0]*size[1] for size in sizes)>4000000:
        raise ValueError("uicheck requires 1..16 sizes within a 4000000-pixel budget")
    trials = [resize_ui(source,frame["ui"],size) for size in sizes]
    destination = Path(output).resolve()
    if destination.exists():
        raise ValueError("UI check output directory already exists")
    destination.parent.mkdir(parents=True,exist_ok=True)
    report = {"schema_version":1,"status":"needs_visual_review","asset_id":data["asset_id"],"frame":frame_id,
              "manifest_content_sha256":hashlib.sha256(json.dumps(data,sort_keys=True,separators=(",",":")).encode()).hexdigest(),
              "texture_sha256":data["texture_sha256"],"contract":frame["ui"],
              "state":frame["ui"]["state"],"trials":[],"unverified":["text fit and localization","focus/input behavior","artistic hierarchy","engine integration"]}
    with tempfile.TemporaryDirectory(prefix="pixelai-uicheck-",dir=destination.parent) as temporary:
        bundle = Path(temporary)/"bundle"
        bundle.mkdir()
        for index,(image,trial) in enumerate(trials):
            native,zoom = f"target_{index:02d}.png",f"target_{index:02d}_4x.png"
            image.save(bundle/native)
            image.resize((image.width*4,image.height*4),Image.Resampling.NEAREST).save(bundle/zoom)
            report["trials"].append({**trial,"native":native,"zoom":zoom})
        if not all(trial["fixed_corners_preserved"] for trial in report["trials"]):
            report["status"] = "failed"
        (bundle/"ui.json").write_text(json.dumps(report,indent=2))
        bundle.rename(destination)
    return {**report,"output":str(destination)}


def register(sub):
    parser = sub.add_parser("uicheck",help="Resize exported UI slices and emit fixed-corner checks plus native/4x review images.")
    parser.add_argument("manifest")
    parser.add_argument("--frame",default="0",help="Exported frame id (default: 0).")
    parser.add_argument("--size",action="append",required=True,help="Target WIDTHxHEIGHT; repeat up to 16 times.")
    parser.add_argument("--output",required=True,help="New evidence directory.")
    parser.add_argument("--json",action="store_true")
    def run(args):
        sizes = []
        for value in args.size:
            parts = value.lower().split("x")
            if len(parts)!=2 or any(not part.isdecimal() for part in parts):
                raise ValueError("UI sizes must use WIDTHxHEIGHT positive integer syntax")
            sizes.append([int(part) for part in parts])
        report = check_ui(args.manifest,args.frame,sizes,args.output)
        print(json.dumps(report))
        return 1 if report["status"]=="failed" else 0
    parser.set_defaults(func=run)
