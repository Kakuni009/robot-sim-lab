"""Check CUDA computation and a finite, headless Isaac Sim application run."""

import torch

assert torch.cuda.is_available(), "CUDA is unavailable"
matrix = torch.ones((512, 512), device="cuda")
result = matrix @ matrix
torch.cuda.synchronize()
assert result[0, 0].item() == 512
print(f"CUDA: PASS ({torch.cuda.get_device_name(0)})", flush=True)
del matrix, result
torch.cuda.empty_cache()

from isaacsim.simulation_app import SimulationApp

app = SimulationApp({
    "headless": True,
    "extra_args": [
        "--/telemetry/enableAnonymousAppName=false",
        "--/telemetry/enableAnonymousData=false",
    ],
})
try:
    for _ in range(30):
        app.update()
    print("Isaac Sim application updates: PASS", flush=True)
finally:
    app.close()
