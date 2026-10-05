import asyncio
import csv
from pathlib import Path


import omni.usd
from omni.kit.viewport.utility import (
    capture_viewport_to_file,
    get_active_viewport,
    next_viewport_frame_async,
)


POSITIONS = [0.45,0.60]
OUTPUT_DIR = Path("C:/cloud/claude_hub/robot-sim-lab/outputs/v02")
LABELS_PATH = OUTPUT_DIR / "labels.csv"

async def capture(viewport, path):
    result = capture_viewport_to_file(viewport, file_path=str(path))
    if not await result.wait_for_result(completion_frames=30):
        raise RuntimeError(f"Capture failed: {path}")


async def move_part_loop():
    stage = omni.usd.get_context().get_stage()
    cube = stage.GetPrimAtPath("/World/PartCube")
    translate = cube.GetAttribute("xformOp:translate")
    original = translate.Get()
    viewport = get_active_viewport()

    camera_path = str(viewport.camera_path)
    if not camera_path.endswith("/WorkcellCamera"):
        raise RuntimeError(f"Select WorkcellCamera (current: {camera_path})")
    OUTPUT_DIR.mkdir(parents=True,exist_ok=True)


    try:
        for x in POSITIONS:
            path = OUTPUT_DIR / f"pos-x{x:.2f}.png"
            if path.exists():
                raise RuntimeError(f"Already exists: {path}")
            translate.Set(type(original)(x,original[1],original[2]))
            await next_viewport_frame_async(viewport)
            await capture(viewport,path)
            append_label(path.name, translate.Get())
            print(f"Captured {path.name} at {translate.Get()}")

    finally:
        translate.Set(original)
        print(f"Restored to {translate.Get()}")

def append_label(image_name, position):
    is_new = not LABELS_PATH.exists()
    with open(LABELS_PATH, "a", newline="") as f:
        writer = csv.writer(f)
        if is_new:
            writer.writerow(["image", "x" ,"y" ,"z"])
        writer.writerow([image_name, position[0],position[1],position[2]])

asyncio.ensure_future(move_part_loop())

