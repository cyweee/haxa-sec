from PIL import Image, ImageChops

# Otevření GIFu
im = Image.open("gif-me-the-flag.gif")

# Vytvoření černého plátna o stejné velikosti
background = Image.new("RGB", im.size, (0, 0, 0))

# Projdi všechny snímky
try:
    while True:
        # Převedení aktuálního snímku na RGB
        current_frame = im.convert("RGB")

        # Sloučení s pozadím (funkce lighter vybere světlejší pixely - tedy bílé tečky)
        background = ImageChops.lighter(background, current_frame)

        # Posun na další snímek
        im.seek(im.tell() + 1)
except EOFError:
    pass  # Konec souboru

# Uložení výsledku
background.save("vlajka.png")
print("Hotovo! Otevři vlajka.png")