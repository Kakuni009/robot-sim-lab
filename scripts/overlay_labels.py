from PIL import Image, ImageDraw

from verify_dataset import DATA_DIR, WIDTH, HEIGHT, load_camera, project, read_labels

OUT_DIR = DATA_DIR / "overlay"
MARK = 25
COLUMNS = 9
THUMB_SCALE = 0.25

def draw_mark(image, u, v, size, text=None):
    draw = ImageDraw.Draw(image)
    draw.rectangle((u - size, v - size, u + size, v+ size), outline=(255,0,0), width=2)
    if text:
        draw.text((u -size, v-size - 14), text, fill=(255,255,0))

def main():
    world_to_cam, scale = load_camera()
    rows = read_labels()
    OUT_DIR.mkdir(exist_ok=True)
    tw, th = int(WIDTH * THUMB_SCALE), int(HEIGHT * THUMB_SCALE)
    sheet = Image.new("RGB", (tw * COLUMNS, th * ((len(rows) + COLUMNS -1) // COLUMNS)))
    for i, row in enumerate(rows):
        x, y, z = float(row["x"]), float(row["y"]), float(row["z"])
        u, v = project(world_to_cam, scale, x, y, z)
        image = Image.open(DATA_DIR / row["image"]).convert("RGB")
        thumb = image.resize((tw,th))
        draw_mark(image, u, v, MARK, f"({x:.2f}, {y:+.2f})")
        image.save(OUT_DIR / row["image"])
        draw_mark(thumb, u* THUMB_SCALE, v * THUMB_SCALE, 8)
        sheet.paste(thumb, ((i % COLUMNS) * tw,(i // COLUMNS) * th))
    sheet.save(OUT_DIR / "sheet.png")
    print(f"Saved {len(rows)} image and sheet.png to {OUT_DIR}")

if __name__ == "__main__":
    main()
