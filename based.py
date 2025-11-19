# je na hovno
import requests
import urllib.parse
import time
from typing import Union
import sys

# --- 1. Načtení 100% správné mapy ---

REVERSE_MAP = {}
N_MIN = 0
KNOWN_PREFIX_BIN = "0111010001100101011110000111010001111011"  # "text{"
BASE_URL = "http://13.48.13.73:8080"


def build_unicode_map():
    """
    Načte PŘESNOU mapu ze souboru vygenerovaného pomocí Node.js
    """
    global REVERSE_MAP, N_MIN
    print("⏳ Načítám mapu ze souboru 'unicode_map.txt'...")
    try:
        with open("unicode_map.txt", "r", encoding="utf-8") as f:
            unicode_map_str = f.read()

        REVERSE_MAP = {c: i for i, c in enumerate(unicode_map_str)}
        map_size = len(REVERSE_MAP)

        if map_size == 0:
            print("❌ Chyba: Soubor 'unicode_map.txt' je prázdný.")
            sys.exit(1)

        N_MIN = (map_size - 1).bit_length()

        print(f"✅ Mapa načtena. Velikost: {map_size} znaků.")
        print(f"ℹ️ Minimální N (N_min): {N_MIN}")

    except FileNotFoundError:
        print("❌ CHYBA: Soubor 'unicode_map.txt' nebyl nalezen.")
        print("Nejprve spusťte Node.js skript (generate_map.js) pro jeho vygenerování.")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Chyba při čtení mapy: {e}")
        sys.exit(1)


# --- 2. Vyhledání N (VERZE PRO DEBUG) ---

def find_n(encoded_str: str) -> Union[int, None]:
    """
    Najde správné 'N' pro daný text - s výpisem pro debug.
    """
    L = len(encoded_str)

    print("--- DEBUG: Hledám N ---")
    print(f"Known prefix (text{{): {KNOWN_PREFIX_BIN} (40 bitů)")

    # Zvětšíme rozsah pro jistotu až na 100
    for N in range(N_MIN, 101):

        test_bitstream = ""
        bits_needed = len(KNOWN_PREFIX_BIN)  # 40 bitů

        chars_needed = (bits_needed + N - 1) // N
        if chars_needed > L:
            continue

        try:
            for i in range(chars_needed):
                char = encoded_str[i]
                index = REVERSE_MAP[char]
                test_bitstream += format(index, f'0{N}b')

        except KeyError:
            continue

        # --- TOTO JE NOVÝ DEBUG VÝPIS ---
        # Zkrátíme výpis jen na 40 bitů pro přehlednost
        print(f"Testuji N={N:02d}: {test_bitstream[:bits_needed]}")
        # --- KONEC DEBUG VÝPISU ---

        if test_bitstream.startswith(KNOWN_PREFIX_BIN):
            print("--- DEBUG: NALEZENO! ---")
            return N  # Našli jsme N!

    print("--- DEBUG: Hledání N selhalo v celém rozsahu ---")
    return None  # N se nepodařilo najít v rozsahu


# --- 3. Dekódování (s úpravou) ---

def decode_text(encoded_str: str, N: int) -> str:
    bit_stream = ""

    try:
        for char in encoded_str:
            index = REVERSE_MAP[char]
            bit_stream += format(index, f'0{N}b')
    except KeyError as e:
        # Tuto chybu už vypisovat nemusíme
        # print(f"Chyba: Znak '{e.args[0]}' nenalezen v mapě.")
        return ""

    decoded_text = ""
    started = False  # Přidáno
    for i in range(0, len(bit_stream), 8):
        byte = bit_stream[i:i + 8]
        if len(byte) < 8:
            break

        char_code = int(byte, 2)

        # --- ZMĚNĚNÁ LOGIKA ---
        if char_code == 0 and not started:
            continue  # Přeskakujeme úvodní NUL bajty

        started = True  # Začali jsme číst data

        if char_code == 0:
            break  # NUL bajt uprostřed dat = konec

        ch = chr(char_code)
        decoded_text += ch

        if ch == '}':
            break

    return decoded_text


# --- 2. Vyhledání N (s úpravou) ---

def find_n(encoded_str: str) -> Union[int, None]:
    """
    Najde správné 'N' tak, že zkusí dekódovat text pro každé N
    a zkontroluje, zda začíná na "text{".
    """
    L = len(encoded_str)

    # N_MIN je ~17. Zkusíme rozumný rozsah.
    for N in range(N_MIN, 65):

        # Zkusíme rovnou dekódovat
        # Použijeme jen prvních pár znaků pro rychlost
        # (Kolik znaků stačí na 5 bajtů * 8 bitů = 40 bitů)
        chars_needed = (40 + N - 1) // N
        # Přidáme pár znaků navíc pro jistotu (kvůli možným NUL bajtům)
        chars_to_test = min(L, chars_needed + 5)

        test_chunk = encoded_str[:chars_to_test]

        decoded_preview = decode_text(test_chunk, N)

        # print(f"Testuji N={N:02d}: Dekódováno -> '{decoded_preview[:10]}...'") # Odkomentujte pro těžký debug

        if decoded_preview.startswith("text{"):
            print(f"--- DEBUG: Nalezeno N={N} s novou logikou! ---")
            return N  # Našli jsme N!

    return None  # N se nepodařilo najít v rozsahu


# --- 4. Hlavní smyčka ---

def solve():
    build_unicode_map()  # Načte mapu ze souboru

    session = requests.Session()
    correct_count = 0

    while True:
        try:
            print(f"\n--- Pokus {correct_count + 1} ---")
            resp = session.get(BASE_URL)

            if 'flag' in resp.headers:
                print("\n" + "=" * 30)
                print("🎉 VLAJKA NALEZENA! 🎉")
                print(f"Hlavička: {resp.headers['flag']}")
                try:
                    flag = urllib.parse.unquote(resp.headers['flag'])
                    print(f"Dekódováno: {flag}")
                except Exception:
                    print("Nepodařilo se URL dekódovat.")
                print("=" * 30)
                break

            encoded_text = resp.text
            print(f"Přijato: {encoded_text[:50]}...")

            # --- Sanity check ---
            first_char = encoded_text[0]
            if first_char not in REVERSE_MAP:
                print(f"❌ Kritická chyba: První znak '{first_char}' (Unicode: {ord(first_char)})")
                print("nebyl nalezen ve vygenerované mapě 'unicode_map.txt'.")
                print("Ujistěte se, že jste spustili 'node generate_map.js' ve stejném adresáři.")
                break
            # --- Konec sanity check ---

            N = find_n(encoded_text)
            if N is None:
                print(f"❌ Nepodařilo se najít 'N' v rozsahu (do 64). Server poslal text, který neodpovídá.")
                print(f"(Text byl: {encoded_text})")
                correct_count = 0
                time.sleep(1)
                continue

            print(f"ℹ️ Nalezeno N = {N}")

            decoded = decode_text(encoded_text, N)

            if not decoded.startswith("text{") or not decoded.endswith("}"):
                print(f"❌ Dekódování selhalo. Výsledek: {decoded}")
                correct_count = 0
                time.sleep(1)
                continue

            print(f"Dekódováno: {decoded}")

            encoded_answer = urllib.parse.quote(decoded)
            answer_url = f"{BASE_URL}/answer/{encoded_answer}"

            answer_resp = session.get(answer_url)

            if answer_resp.text == "correct":
                correct_count += 1
                print(f"✅ Správně! ({correct_count} v řadě)")
            else:
                print(f"❌ Špatně! Odpověď serveru: {answer_resp.text}")
                correct_count = 0

            time.sleep(0.5)

        except requests.RequestException as e:
            print(f"HTTP Chyba: {e}")
            time.sleep(5)
        except Exception as e:
            print(f"Neočekávaná chyba: {e}")
            break


if __name__ == "__main__":
    solve()