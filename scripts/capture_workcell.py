"""Capture the active Isaac Sim viewport to a PNG file."""

import asyncio
from pathlib import Path

from omni.kit.viewport.utility import (
    capture_viewport_to_file,
    get_active_viewport,
    next_viewport_frame_async,
)


OUTPUT_DIR = Path("C:/cloud/robot-sim-lab/outputs")


def next_output_path() -> Path:
    for index in range(1, 1000):
        candidate = OUTPUT_DIR / f"workcell-camera-{index:03d}.png"
        if not candidate.exists():
            return candidate
    raise RuntimeError("No unused output filename remains in the 001-999 range.")


async def capture_workcell() -> None:
    viewport = get_active_viewport()
    if viewport is None:
        raise RuntimeError("Active viewport was not found.")

    camera_path = str(viewport.camera_path)
    if not camera_path.endswith("/WorkcellCamera"):
        raise RuntimeError(f"Select WorkcellCamera before capture (current: {camera_path}).")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = next_output_path()
    await next_viewport_frame_async(viewport)

    capture = capture_viewport_to_file(viewport, file_path=str(output_path))
    succeeded = await capture.wait_for_result(completion_frames=30)
    if not succeeded:
        raise RuntimeError("Viewport capture did not complete successfully.")

    print(f"Capture complete: {output_path}")


asyncio.ensure_future(capture_workcell())
