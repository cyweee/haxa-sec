from PIL import Image
import re


def solve_pixels(image_path):
    print(f"Analyzuji: {image_path}")
    try:
        img = Image.open(image_path)
        pixels = img.load()
        width, height = img.size
    except Exception as e:
        print(f"Chyba: {e}")
        return

    # Řetězce pro jednotlivé kanály
    text_r = ""
    text_g = ""
    text_b = ""

    # Procházíme pixely a převádíme barvu přímo na znak
    # Například: hodnota barvy 104 = znak 'h'
    for y in range(height):
        for x in range(width):
            r, g, b = pixels[x, y]

            # Převedeme na znak pouze pokud je to tisknutelné (pro čistší výstup)
            # ASCII 32-126 jsou čitelné znaky
            text_r += chr(r) if 32 <= r <= 126 else ""
            text_g += chr(g) if 32 <= g <= 126 else ""
            text_b += chr(b) if 32 <= b <= 126 else ""

    print("\n--- HLEDÁNÍ VLAJKY ---")

    # Funkce pro hledání a výpis
    def find_flag(channel_name, text):
        # Hledáme haxagon{...} nebo hexagon{...}
        match = re.search(r"(haxagon\{.*?\})", text, re.IGNORECASE)
        if match:
            print(f"✅ Vlajka nalezena v kanálu {channel_name}:")
            print(f"🚩 {match.group(1)}")
            return True
        return False

    found = False
    found |= find_flag("ČERVENÝ (Red)", text_r)
    found |= find_flag("ZELENÝ (Green)", text_g)
    found |= find_flag("MODRÝ (Blue)", text_b)

    if not found:
        print("Vlajka nebyla nalezena přímým převodem.")
        print("Zkouším vypsat začátky kanálů, jestli neuvidíme vzor:")
        print(f"R: {text_r[:50]}")
        print(f"G: {text_g[:50]}")
        print(f"B: {text_b[:50]}")

        # Tip: Někdy je text pozpátku
        print("\nZkouším text pozpátku...")
        find_flag("R (Reverse)", text_r[::-1])
        find_flag("G (Reverse)", text_g[::-1])
        find_flag("B (Reverse)", text_b[::-1])


# Spuštění
solve_pixels("/home/cywe/PycharmProjects/haxagon-sec/noise.bmp")