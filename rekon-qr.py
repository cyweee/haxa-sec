from PIL import Image, ImageDraw
def check_indices(file_path):
    img = Image.open(file_path).convert('RGB')
    w, h = img.size
    tw, th = w // 3, h // 3

    for i in range(9):
        c, r = i % 3, i // 3
        tile = img.crop((c * tw, r * th, (c + 1) * tw, (r + 1) * th))

        # Рисуем номер прямо на кусочке, чтобы не запутаться
        draw = ImageDraw.Draw(tile)
        draw.text((10, 10), str(i), fill="red")
        tile.save(f"tile_check_{i}.png")
    print("Проверь файлы tile_check_0.png до 8.png и выпиши номера тех, где есть большие квадраты.")


check_indices('qrStruggle.png')