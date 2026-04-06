import itertools
from PIL import Image
from pyzbar.pyzbar import decode
import sys


def solve():
    # Načtení obrázku (ujisti se, že název souhlasí)
    try:
        img = Image.open('qrStruggle.png').convert('RGB')
    except FileNotFoundError:
        print("Chyba: Soubor qrStruggle.png nebyl nalezen.")
        return

    w, h = img.size
    tw, th = w // 3, h // 3

    # Nařezání dílků
    tiles = []
    for i in range(9):
        tiles.append(img.crop(((i % 3) * tw, (i // 3) * th, ((i % 3) + 1) * tw, ((i // 3) + 1) * th)))

    # TVOJE IDENTIFIKOVANÉ INDEXY
    corners_idx = [0, 1, 4]
    others_idx = [2, 3, 5, 6, 7, 8]

    # Pozice v QR kódu, kam patří čtverce (indexy v mřížce 3x3)
    # 0 = vlevo nahoře, 2 = vpravo nahoře, 6 = vlevo dole
    target_corner_pos = [0, 2, 6]
    # Ostatní volné pozice
    target_other_pos = [1, 3, 4, 5, 7, 8]

    print("Spouštím optimalizovanou analýzu (zafixované rohy 0, 1, 4)...")

    # 3! kombinací pro rohy * 6! kombinací pro zbytek = 4320 možností
    count = 0
    for p_corners in itertools.permutations(corners_idx):
        for p_others in itertools.permutations(others_idx):
            canvas = Image.new('RGB', (w, h))

            # 1. Umístíme rohy na jejich pozice
            for i, pos in enumerate(target_corner_pos):
                canvas.paste(tiles[p_corners[i]], ((pos % 3) * tw, (pos // 3) * th))

            # 2. Umístíme zbytek na volná místa
            for i, pos in enumerate(target_other_pos):
                canvas.paste(tiles[p_others[i]], ((pos % 3) * tw, (pos // 3) * th))

            count += 1
            if count % 100 == 0:
                sys.stdout.write(f"\rTestováno kombinací: {count}")
                sys.stdout.flush()

            # Kontrola QR kódu
            res = decode(canvas)
            if res:
                flag = res[0].data.decode()
                print(f"\n\n[!!!] ÚSPĚCH!")
                print(f"VLAJKA: {flag}")
                canvas.save("VYRESENO_FINAL.png")
                return

    print("\n\n[-] Žádná kombinace nefungovala. Zkus prověřit, zda jsou indexy 0, 1, 4 správné.")


if __name__ == "__main__":
    solve()