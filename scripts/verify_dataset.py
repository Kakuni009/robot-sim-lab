import csv
from pathlib import Path

from pxr import Gf, Usd, UsdGeom

import numpy as np
from PIL import Image


ROOT = Path(__file__).resolve().parent.parent
USD_PATH = ROOT/ "workcell-v02-camera.usd"
WINDOW = 40
PART_THRESHOLD = 60
MAX_ERROR_PX = 5
GHOST_WINDOW = 8
GHOST_THRESHOLD = 7

HOME = (0.5, 0.0,0.025800000876188278)

DATA_DIR = ROOT/ "outputs" / "v04"
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

def load_image(rows):
    return [np.asanyarray(Image.open(DATA_DIR / row["image"]).convert("RGB")).astype(int) for row in rows]

def find_part(diff, u, v):
    u0, v0 = int(u) - WINDOW, int(v) - WINDOW
    window = diff[v0:v0 +2 * WINDOW, u0:u0 +2 * WINDOW]
    vs, us = np.nonzero(window > PART_THRESHOLD)
    if len(us) == 0:
        return None
    return u0 + us.mean(), v0 +vs.mean()

def ghost_level(diff, u, v):
    u0, v0 = int(u) - GHOST_WINDOW,int(v) - GHOST_WINDOW
    return diff[v0:v0 + 2 * GHOST_WINDOW, u0:u0 + 2 * GHOST_WINDOW].mean()



def main():
    world_to_cam, scale = load_camera()
    rows = read_labels()
    images = load_image(rows)
    background = np.median(images,axis=0)
    prev = HOME
    for row,image in zip(rows, images):
        x, y, z = float(row["x"]), float(row["y"]), float(row["z"])
        u, v = project(world_to_cam, scale, x, y, z)
        diff = np.abs(image - background).sum(axis=2)
        pu, pv = project(world_to_cam, scale, *prev)
        ghost = ghost_level(diff, pu, pv)
        prev = (x,y,z)
        found = find_part(diff, u, v)
        if found is None:
            print(f"{row['image']}: NG 部品が見つからない")
            continue
        error = ((found[0]-u) **2 + (found[1] - v) ** 2) ** 0.5
        result = "OK" if error <= MAX_ERROR_PX and ghost <= GHOST_THRESHOLD else "NG"
        print(f"{row['image']}: {result} 計算({u:.1f},{v:.1f})画像({found[0]:.1f}, {found[1]:.1f})ずれ{error:.1f} 残像{ghost:.1f}")




main()
