import re
import sys
import os
from PIL import Image
from PIL.ExifTags import TAGS


def analyze_haxagon(file_path):
    if not os.path.exists(file_path):
        print(f"[-] Soubor {file_path} nebyl nalezen.")
        return

    print(f"[*] Startuji hloubkovou analýzu: {file_path}")
    print("-" * 60)

    with open(file_path, "rb") as f:
        data = f.read()

    # 1. Agresivní hledání vlajky v různých kódováních
    # ASCII / UTF-8
    pattern_ascii = rb"haxagon\{.*?\}"
    # UTF-16 Little Endian (časté v EXIFu: h.a.x.a.g.o.n.{. . .})
    pattern_utf16 = rb"h\x00a\x00x\x00a\x00g\x00o\x00n\x00\{\x00.*?\x00\}"

    print("[*] Prohledávám binární data...")

    found_any = False

    # Hledání ASCII
    for match in re.finditer(pattern_ascii, data, re.IGNORECASE):
        print(f"    [!!!] Nalezena ASCII vlajka: {match.group().decode('ascii', errors='ignore')}")
        found_any = True

    # Hledání UTF-16
    for match in re.finditer(pattern_utf16, data):
        try:
            decoded = match.group().decode('utf-16le')
            print(f"    [!!!] Nalezena UTF-16 vlajka: {decoded}")
            found_any = True
        except:
            continue

    # 2. Detailní EXIF analýza
    print("\n[*] Kontroluji EXIF pole (hledám haxagon)...")
    try:
        img = Image.open(file_path)
        exif = img._getexif()
        if exif:
            for tag_id, value in exif.items():
                tag_name = TAGS.get(tag_id, tag_id)
                val_str = str(value)
                # Vypíšeme zajímavá pole, i když v nich není vlajka
                if any(x in tag_name.lower() for x in ["model", "software", "comment", "artist", "description"]):
                    print(f"    [EXIF] {tag_name}: {val_str}")

                if "haxagon" in val_str.lower():
                    print(f"    [!!!] ZÁSAH V EXIFu ({tag_name}): {val_str}")
                    found_any = True
        else:
            print("    [-] Žádná EXIF data v souboru nejsou.")
    except Exception as e:
        print(f"    [-] Chyba při parsování EXIF: {e}")

    # 3. Kontrola "Trailing Data" (za značkou FF D9)
    eof_marker = b"\xff\xd9"
    last_idx = data.rfind(eof_marker)
    if last_idx != -1 and last_idx < len(data) - 2:
        extra = data[last_idx + 2:]
        print(f"\n[*] Zjištěna data za koncem souboru ({len(extra)} bajtů).")
        # Zkusíme najít text v těchto datech
        extra_strings = re.findall(rb"haxagon\{.*?\}", extra, re.IGNORECASE)
        for s in extra_strings:
            print(f"    [!!!] Vlajka nalezena v 'trailing data': {s.decode('ascii', errors='ignore')}")
            found_any = True

    if not found_any:
        print("\n[?] Vlajka 'haxagon{...}' nebyla nalezena automaticky.")
        print("[?] Zkus: strings -e l " + file_path + " | grep haxagon")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Použití: python3 script.py <soubor>")
    else:
        analyze_haxagon(sys.argv[1])