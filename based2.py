import requests
import urllib.parse
import unicodedata
import time


def get_unicode_table():
    """Vytvoří tabulku přesně podle vlastností unicode-properties v Node.js."""
    table = []
    # MAX_UNICODE 1114111 + 1
    for i in range(33, 1114112):
        c = chr(i)
        cat = unicodedata.category(c)

        # Node.js: isAlphabetic (L, Nl), isDigit (Nd), isPunctuation (P)
        is_alpha = cat.startswith('L') or cat == 'Nl'
        is_digit = (cat == 'Nd')
        is_punc = cat.startswith('P')

        if is_alpha or is_digit or is_punc:
            table.append(c)
    return table


def solve():
    # IP adresa ze screenshotu
    BASE_URL = "http://13.61.5.9:8080"

    print("Generuji Unicode tabulku (L, Nd, P)...")
    table = get_unicode_table()
    char_to_idx = {c: i for i, c in enumerate(table)}
    print(f"Tabulka připravena, velikost: {len(table)}")

    while True:
        print("\n--- Načítám data ---")
        try:
            r = requests.get(BASE_URL, timeout=10)
            if 'flag' in r.headers:
                print(f"\n[!!!] VLAJKA NALEZENA: {urllib.parse.unquote(r.headers['flag'])}")
                break

            data = r.text.strip().strip('"')
            print(f"Data ({len(data)} znaků): {data[:15]}...")

            found = False
            # Zkoušíme N=15 a N=16, což jsou nejvhodnější kandidáti
            for n in [15, 16, 14, 17]:
                # 1. Vytvoření surového bitového proudu
                bit_str = ""
                for char in data:
                    if char in char_to_idx:
                        bit_str += bin(char_to_idx[char])[2:].zfill(n)

                # 2. Zkusíme posunout celý bitový proud o 0 až N-1 bitů
                # To řeší situaci, kdy text nezačíná přesně na začátku prvního znaku
                for bit_offset in range(n):
                    shifted_bits = bit_str[bit_offset:]

                    # Převod na bajty
                    byte_arr = bytearray()
                    for i in range(0, len(shifted_bits) - 7, 8):
                        byte_arr.append(int(shifted_bits[i:i + 8], 2))

                    try:
                        decoded = byte_arr.decode('ascii', errors='ignore')
                        if "text{" in decoded:
                            start = decoded.find("text{")
                            end = decoded.find("}", start)
                            if end != -1:
                                result = decoded[start:end + 1]
                                print(f"[*] Nalezeno! N={n}, BitOffset={bit_offset} -> {result}")

                                # Odeslání
                                ans_url = f"{BASE_URL}/answer/{urllib.parse.quote(result)}"
                                resp = requests.get(ans_url)
                                print(f"[Server]: {resp.text}")
                                found = True
                                break
                    except:
                        continue
                if found: break

            if not found:
                print("[?] Nenalezeno. Zkouším další kolo...")
                time.sleep(1)

        except Exception as e:
            print(f"Chyba: {e}")
            time.sleep(2)


if __name__ == "__main__":
    solve()