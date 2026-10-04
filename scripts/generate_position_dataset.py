import asyncio
from pathlib import Path


import omni.usd
from omni.kit.viewport.utility import {
    capture_viewport_to_file,
    get_active_viewport,
    next_viewport_frame_async,
}


POSITIONS = [0.55,0.65]
OUTPUT_DIR = Path("C:/cloud/claude_hub/robot-sim-lab/outputs/v02")

async def capture(viewport, path):
    result = capture_viewport_to_file(viewport, flie_path=str(path))
    if not await result.wait_for_result(completion_frame=30):
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
            print(f"Captured {path.name} at {translate.Get()}")

    finally:
        translate.Set(original)
        print(f"Restored to {translate.Get()}")


asyncio.ensure_future(move_part_loop())D

