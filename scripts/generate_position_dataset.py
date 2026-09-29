import asyncio
from omni.kit.viewport.utility import get_active_viewport,next_viewport_frame_async

async def wait_for_frame():
    viewport = get_active_viewport()
    await next_viewport_frame_async(viewport)
    print("One viewport frame completed")

asyncio.ensure_future(wait_for_frame())
