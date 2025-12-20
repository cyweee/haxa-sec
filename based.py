import requests
import unicodedata
import sys
from urllib.parse import quote

# Nastavení adresy serveru (Doplňte IP adresu z vašeho zadání)
TARGET_IP = "51.21.149.90"  # Změňte na IP adresu serveru
BASE_URL = f"http://{TARGET_IP}:8080"


def generate_unicode_map():
    """
    Replikuje logiku TypeScript třídy UnicodeTable.
    Vytvoří slovník {znak: index}.
    """
    print("[*] Generuji Unicode tabulku (to může chvíli trvat)...")
    char_to_index = {}
    current_map_index = 0

    # TypeScript kód začíná na indexu znaku '!' (33) a jde do MAX_UNICODE (1114112)
    # Podmínka v TS: while (!alphabetic && !digit && !punctuation) index++
    # To znamená, že přidáváme do mapy, POKUD je znak Alphabetic, Digit nebo Punctuation.

    for code_point in range(33, 1114112):
        char = chr(code_point)
        category = unicodedata.category(char)

        # Kategorie v Python unicodedata:
        # L = Letter (Alphabetic), N = Number (Digit), P = Punctuation
        is_valid = category.startswith('L') or category.startswith('N') or category.startswith('P')

        if is_valid:
            char_to_index[char] = current_map_index
            current_map_index += 1

    print(f"[*] Tabulka vygenerována. Velikost: {len(char_to_index)}")
    return char_to_index

    try:
        text = data.decode('utf-8')
    except UnicodeDecodeError:
        print("Nelze dekódovat jako UTF-8. Je to šifrované nebo binární?")

def decode_text(encoded_str, char_map):
    """
    Pokusí se dekódovat text zkoušením různých hodnot N (šířka bitů).
    """
    # 1. Převést znaky na seznam indexů podle mapy
    indices = []
    for char in encoded_str:
        if char not in char_map:
            # Pokud znak není v naší mapě, pravděpodobně máme drobnou odchylku v generování tabulky
            # nebo jde o speciální znak. Pro účely CTF většinou stačí ignorovat nebo failnout.
            return None
        indices.append(char_map[char])

    # 2. Brute-force hledání N (zkoušíme rozumný rozsah, např. 9 až 24 bitů)
    # ASCII má 8 bitů. N musí být takové, aby se bity daly přeskládat zpět na 8bitové.

    for n in range(1, 32):
        # Sestavíme bitový řetězec
        # Každý index reprezentuje N bitů
        bit_stream = ""
        for index in indices:
            # Převedeme index na binární řetězec o délce N, bez '0b' prefixu
            bit_stream += format(index, f'0{n}b')

        # Nyní rozdělíme bit_stream po 8 bitech (ASCII)
        # Pokud délka není dělitelná 8, ořízneme konec (padding) nebo to není správné N
        decoded_chars = []
        try:
            # Iterujeme po 8 bitech
            valid_utf = True
            raw_text = ""

            for i in range(0, len(bit_stream) - 7, 8):
                byte_val = int(bit_stream[i:i + 8], 2)
                if byte_val > 127:  # Očekáváme ASCII, takže max 127
                    # Může to být i vyšší ASCII, ale formát je text{...}, což je standard ASCII
                    pass
                decoded_chars.append(chr(byte_val))

            candidate_text = "".join(decoded_chars)

            # 3. Kontrola formátu
            if candidate_text.startswith("text{"):
                return candidate_text

        except Exception:
            continue

    return None


def main():
    # 1. Příprava
    char_map = generate_unicode_map()
    session = requests.Session()

    solved_count = 0

    while True:
        try:
            # 2. Získání zadání
            print(f"\n[?] Žádám o zadání č. {solved_count + 1}...")
            response = session.get(BASE_URL)

            # Kontrola vlajky v hlavičce
            if "flag" in response.headers:
                print("\n" + "=" * 50)
                print(f"VICTORY! Flag: {response.headers['flag']}")
                # Vlajka je URL enkódovaná, dekódujeme ji pro čitelnost
                from urllib.parse import unquote
                print(f"Decoded Flag: {unquote(response.headers['flag'])}")
                print("=" * 50)
                break

            encoded_text = response.text
            if not encoded_text:
                print("[!] Prázdná odpověď serveru.")
                break

            #  - není potřeba, ale pro představu:
            # Server: [Bits] -> (split by N) -> [Indices] -> [Unicode Chars]
            # My: [Unicode Chars] -> [Indices] -> (join by N) -> [Bits] -> (split by 8) -> ASCII

            # 3. Dekódování
            decoded = decode_text(encoded_text, char_map)

            if decoded:
                print(f"[+] Dekódováno: {decoded}")

                # 4. Odeslání odpovědi
                # URL musí být ve formátu /answer/text%7B...%7D
                # Použijeme quote pro bezpečné vložení do URL
                answer_url = f"{BASE_URL}/answer/{quote(decoded)}"
                verify_resp = session.get(answer_url)

                if "correct" in verify_resp.text:
                    print("[OK] Odpověď správná.")
                    solved_count += 1
                else:
                    print(f"[!] Chyba: Server vrátil '{verify_resp.text}'. Resetuji.")
                    solved_count = 0
            else:
                print(f"[!] Nepodařilo se dekódovat řetězec: {encoded_text[:20]}...")
                # Někdy může brute-force selhat, pokud N je velmi exotické, ale range 1-32 by měl stačit.

        except KeyboardInterrupt:
            print("\n[!] Ukončuji script.")
            break
        except Exception as e:
            print(f"[!] Chyba spojení nebo logika: {e}")
            break





if __name__ == "__main__":
    main()