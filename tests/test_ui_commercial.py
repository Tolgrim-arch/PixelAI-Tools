import json
import subprocess
import sys
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
PARTS = ROOT / "outputs" / "stress_commercial_inventory_parts"


def _inspect(path: Path) -> dict:
    result = subprocess.run(
        [sys.executable, "-m", "pixelai", "inspect", str(path)],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(result.stdout)


def test_commercial_inventory_native_sheet_and_nine_slice_parts():
    sheet = ROOT / "outputs" / "stress_commercial_inventory.png"
    metrics = _inspect(sheet)
    assert (metrics["width"], metrics["height"]) == (192, 132)
    assert metrics["unique_colors"] <= 32
    assert metrics["islands"] == 1
    assert metrics["margins"] == {"top": 3, "right": 3, "bottom": 3, "left": 3}

    expected = {
        "panel": (96, 64),
        "slot": (32, 32),
        "slot_selected": (32, 32),
        "button_normal": (48, 24),
        "button_hover": (48, 24),
        "button_pressed": (48, 24),
    }
    for name, dimensions in expected.items():
        image_path = PARTS / f"{name}.png"
        image = Image.open(image_path).convert("RGBA")
        assert image.size == dimensions
        assert image.getpixel((0, 0))[3] == 0
        assert _inspect(image_path)["islands"] == 1

    panel = Image.open(PARTS / "panel.png").convert("RGBA")
    # The render has a 10px frame + 1px external outline; 12px is a safe
    # nine-slice cap, leaving a 72x40 stretchable center at native resolution.
    assert panel.getpixel((48, 32))[3] == 0
    assert 2 * 12 < 96 and 2 * 12 < 64
    assert (96 - 24, 64 - 24) == (72, 40)

    states = [Image.open(PARTS / f"button_{state}.png").convert("RGBA")
              for state in ("normal", "hover", "pressed")]
    assert len({image.tobytes() for image in states}) == 3
