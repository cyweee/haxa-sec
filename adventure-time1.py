import requests
import concurrent.futures

# URL ke dveřím
URL = "http://13.61.187.243:50706/so_it_begins/mountaintop/signpost_cu4gktWYNB/castle_IhbND0uhuv/door"

# Kódy pro symbolické řešení (ID, název)
SYMBOLIC_CODES = [
    (113402, "Terokk's Quill (Pero)"),
    (112998, "Diamond Ring (Prsten)"),
    (113216, "Elekk Plushie (Plyšák)"),
    (112952, "Self-Reflecting Mask (Maska)"),
    (113359, "Hidden Text Scroll (Svitek)")
]

# 1. Zjistíme přesnou chybovou hlášku
print("1. Zjišťuji přesnou chybovou hlášku pro porovnání...")
session = requests.Session()
try:
    bad_resp = session.post(URL, cookies={'code': '000000'})
    BAD_TEXT = bad_resp.text.strip()
    print(f" -> Chybová hláška je: '{BAD_TEXT}' (Délka: {len(BAD_TEXT)})")
except Exception as e:
    print(f"Chyba připojení: {e}")
    exit()

print("2. Hledám kód, který vrátí JINÝ text (symbolické řešení)...")

found_flag = False


def check_content(code_num, name):
    global found_flag
    if found_flag: return

    try:
        code = str(code_num)
        print(f"👉 Zkouším: {code} ({name})", end='\r')
        resp = session.post(URL, cookies={'code': code})

        # Hledáme odpověď, která NENÍ chybová hláška
        if resp.text.strip() != BAD_TEXT:
            found_flag = True
            print(f"\n\n[!!!] USPĚCH! Kód: {code}")
            print("=" * 40)
            print(f"Nalezená odpověď:")
            print(resp.text)
            print("=" * 40)
            return True
    except:
        pass
    return False


# Spustíme kontrolu jen symbolických kódů
with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
    futures = [executor.submit(check_content, id_num, name) for id_num, name in SYMBOLIC_CODES]
    concurrent.futures.wait(futures)

if not found_flag:
    print(
        "\nŽádný symbolický kód z vymezeného rozsahu nefungoval. Kód musí být mimo rozsah nebo je hádanka ještě složitější.")