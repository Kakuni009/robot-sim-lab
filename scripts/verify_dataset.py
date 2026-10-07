import csv
from pathlib import Path

from pxr import Gf, Usd, UsdGeom

ROOT = Path(__file__).resolve().parent.parent
USD_PATH = ROOT/ "workcell-v02-camera.usd"
DATA_DIR = ROOT/ "outputs" / "v02"
LABELS_PATH = DATA_DIR /"labels.csv"
CAMERA_PATH = "/WorkcellCamera"
WIDTH,HEIGHT = 1280, 720

def load_camera():
    stage = Usd.Stage.Open(str(USD_PATH))
    prim = stage.GetPrimAtPath(CAMERA_PATH)
    camera = UsdGeom.Camera(prim)
    cam_to_world = UsdGeom.Xformable(prim).ComputeLocalToWorldTransform(Usd.TimeCode.Default())
    world_to_cam = cam_to_world.GetInverse()
    focal = camera.GetFocalLengthAttr().Get()
    aperture = camera.GetHorizontalApertureAttr().Get()
    return world_to_cam, focal / aperture * WIDTH

def project(world_to_cam, scale, x, y, z):
    p = world_to_cam.Transform(Gf.Vec3d(x, y, z))
    depth = -p[2]
    u = WIDTH / 2+ scale * p[0] /depth
    v = HEIGHT / 2 - scale * p[1] /depth
    return u, v

def read_labels():
    with open(LABELS_PATH, newline="") as f:
        return list(csv.DictReader(f))

def main():
    world_to_cam, scale = load_camera()
    for row in read_labels():
        x, y, z =float(row["x"]), float(row["y"]), float(row["z"])
        u, v =project(world_to_cam, scale, x, y, z)
        print(f"{row['image']}: ({x},{y}) -> ({u:.1f},{v:.1f})")

main()
