import csv

from itertools import product

from PIL import Image, ImageDraw

from verify_dataset import DATA_DIR, WIDTH, HEIGHT, load_camera, project, read_labels

OUT_DIR = DATA_DIR / "overlay"
BOXES_PATH = DATA_DIR / "boxes.csv"
HALF = 0.0515 /2
COLUMNS = 9
THUMB_SCALE = 0.25

def project_box(world_to_cam,scale,x, y, z):
    corners = [project(world_to_cam, scale, x+dx, y +dy, z + dz) 
               for dx, dy, dz in product((-HALF, HALF), repeat =3)]

    us = [u for u, v in corners]
    vs =[v for u,v in corners]
    return min(us), min(vs), max(us), max(vs)

def draw_mark(image, box, text=None):
    left, top,right, bottom = box
    draw = ImageDraw.Draw(image)
    draw.rectangle(box, outline =(255,0,0),width=2)
    if text:
        draw.text((left, top - 14), text, fill=(255,255,0))


 

def main():
    world_to_cam, scale = load_camera()
    rows = read_labels()
    OUT_DIR.mkdir(exist_ok=True)
    tw, th = int(WIDTH * THUMB_SCALE), int(HEIGHT * THUMB_SCALE)
    boxes = []

    sheet = Image.new("RGB", (tw * COLUMNS, th * ((len(rows) + COLUMNS -1) // COLUMNS)))
    for i, row in enumerate(rows):
        x, y, z = float(row["x"]), float(row["y"]), float(row["z"])
        box = project_box(world_to_cam, scale, x, y, z)
        boxes.append([row["image"], *(round(p,1) for p in box)])
        image = Image.open(DATA_DIR / row["image"]).convert("RGB")
        thumb = image.resize((tw,th))
        draw_mark(image, box, f"({x:.2f}, {y:+.2f})")
        image.save(OUT_DIR / row["image"])
        draw_mark(thumb,[p * THUMB_SCALE for p in box])

        sheet.paste(thumb, ((i % COLUMNS) * tw,(i // COLUMNS) * th))
    sheet.save(OUT_DIR / "sheet.png")
    with open(BOXES_PATH, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["image", "left", "top", "right", "bottom"])
        writer.writerows(boxes)

    print(f"Saved {len(rows)} image and sheet.png to {OUT_DIR}")

if __name__ == "__main__":
    main()
