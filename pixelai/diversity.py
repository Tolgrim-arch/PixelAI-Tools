"""Approximate silhouette diagnostics, never automatic originality approval."""

from PIL import Image, ImageOps


def _mask(path, size=64):
    with Image.open(path) as source:
        alpha = source.convert("RGBA").getchannel("A")
    # Translucent ground shadows must not determine subject identity.
    mask = alpha.point(lambda value: 255 if value >= 128 else 0)
    bbox = mask.getbbox()
    if bbox is None:
        raise ValueError("Cannot compare an empty silhouette")
    native = mask.crop(bbox)
    fitted = ImageOps.contain(native, (size, size), Image.Resampling.NEAREST)
    normalized = Image.new("L", (size, size))
    normalized.paste(fitted, ((size - fitted.width) // 2, size - fitted.height))
    return normalized, native.size


def _iou(first, second):
    a = list(getattr(first, "get_flattened_data", first.getdata)())
    b = list(getattr(second, "get_flattened_data", second.getdata)())
    union = sum(bool(x or y) for x, y in zip(a, b))
    return sum(bool(x and y) for x, y in zip(a, b)) / union if union else 0.0


def compare_silhouettes(first, second):
    """Compare cropped, proportion-preserving masks and their reflection.

    High similarity is a review signal. Rectangular UI, cosmetic variants,
    states and views may legitimately share silhouettes.
    """
    a, size_a = _mask(first)
    b, size_b = _mask(second)
    direct = _iou(a, b)
    mirrored = _iou(a, ImageOps.mirror(b))
    return {"schema_version": 1, "direct_iou": round(direct, 4),
            "mirrored_iou": round(mirrored, 4), "native_bounds": [list(size_a), list(size_b)],
            "review_signal": "high_similarity" if max(direct, mirrored) >= 0.90 else "compare_visually",
            "approval": None,
            "limitations": ["Whole-image mask only; separate parts and atlas cells before comparing", "Similarity does not establish copying or artistic quality"]}


def register(sub):
    import json

    parser = sub.add_parser("diversity", help="Compare normalized silhouettes; diagnostics cannot approve originality.")
    parser.add_argument("first")
    parser.add_argument("second")
    parser.add_argument("--json", action="store_true")

    def run(args):
        print(json.dumps(compare_silhouettes(args.first, args.second)))
        return 0

    parser.set_defaults(func=run)
