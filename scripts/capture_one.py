"""Capture one RGB image from WorkcellCamera and save the part pose next to it.

Run from Isaac Sim's Script Editor (Window > Script Editor) with workcell-v02-camera.usd open
and the simulation stopped. Output goes to robot-sim-lab/outputs/, which is ignored by Git.
"""

import asyncio
import datetime
import json
import os

import omni.replicator.core as rep
import omni.usd
from pxr import Usd, UsdGeom

CAMERA_PATH = "/WorkcellCamera"
PART_PATH = "/World/PartCube"
RESOLUTION = (1280, 720)


def world_translation(prim):
    matrix = UsdGeom.Xformable(prim).ComputeLocalToWorldTransform(Usd.TimeCode.Default())
    return [round(v, 6) for v in matrix.ExtractTranslation()]


async def capture():
    stage = omni.usd.get_context().get_stage()
    camera = stage.GetPrimAtPath(CAMERA_PATH)
    part = stage.GetPrimAtPath(PART_PATH)
    if not camera.IsValid() or not part.IsValid():
        raise RuntimeError(f"Prim not found: camera={camera.IsValid()}, part={part.IsValid()}")

    scene_file = stage.GetRootLayer().realPath
    stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    out_dir = os.path.join(os.path.dirname(scene_file), "outputs", f"capture-{stamp}")
    os.makedirs(out_dir, exist_ok=True)

    render_product = rep.create.render_product(CAMERA_PATH, RESOLUTION)
    writer = rep.WriterRegistry.get("BasicWriter")
    writer.initialize(output_dir=out_dir, rgb=True)
    writer.attach([render_product])
    try:
        # rt_subframes renders extra subframes so the saved image is not a half-converged frame.
        await rep.orchestrator.step_async(rt_subframes=4)
        await rep.orchestrator.wait_until_complete_async()
    finally:
        writer.detach()
        render_product.destroy()

    cam = UsdGeom.Camera(camera)
    label = {
        "scene_file": scene_file,
        "camera_path": CAMERA_PATH,
        "camera_translation": world_translation(camera),
        "focal_length": cam.GetFocalLengthAttr().Get(),
        "horizontal_aperture": cam.GetHorizontalApertureAttr().Get(),
        "resolution": list(RESOLUTION),
        "part_path": PART_PATH,
        "part_translation": world_translation(part),
    }
    with open(os.path.join(out_dir, "label.json"), "w", encoding="utf-8") as f:
        json.dump(label, f, ensure_ascii=False, indent=2)

    print(f"Saved: {out_dir}")
    print(json.dumps(label, ensure_ascii=False, indent=2))


asyncio.ensure_future(capture())
