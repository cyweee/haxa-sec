import requests
import time
import re

# !!! ZKONTROLUJTE, ZDA BĚŽÍ NOVÁ INSTANCE A MÁTE SPRÁVNOU IP !!!
BASE_URL = "http://13.60.203.38:63417"


class HaXasinoPredictor:
    def __init__(self, seed):
        self.seed = seed

    def generate_number(self):
        # SIMULACE JAVASCRIPT CHYBY (Precision Loss)
        # JS používá 64-bitové floaty (doubles), které při násobení velkých čísel
        # ztrácejí přesnost. Python int je přesný, proto musíme použít float().

        # Původní JS: this.seed = (1103515245 * this.seed + 12345) % (2**31);

        # 1. Převedeme na float a vynásobíme (tady vzniká ta nepřesnost jako v JS)
        val = 1103515245.0 * float(self.seed)

        # 2. Přičteme
        val += 12345.0

        # 3. Modulo (zbytek po dělení)
        val %= 2147483648.0  # 2**31

        # Výsledek uložíme jako int pro další kolo (protože po modulu už je číslo malé)
        self.seed = int(val)

        # Výpočet herního čísla
        return (self.seed % 10) + 1


def parse_response(text):
    """Parsuje odpověď a vrací: (vygenerované_číslo, zůstatek)"""
    try:
        # Hledání čísla, co padlo
        num_match = re.search(r"Casino number:\s*(\d+)", text)
        random_number = int(num_match.group(1)) if num_match else None

        # Hledání zůstatku
        bal_match = re.search(r"Your balance:\s*(\d+)", text)
        balance = int(bal_match.group(1)) if bal_match else None

        return random_number, balance
    except Exception:
        return None, None


def solve():
    print(f"[*] Cíl: {BASE_URL}")
    print("[*] 1. Registrace a získání tokenu...")

    estimated_time = int(time.time())

    try:
        r = requests.get(f"{BASE_URL}/generate_token", timeout=10)
        match = re.search(r"token is: ([a-f0-9]+)", r.text)
        if match:
            token = match.group(1)
            print(f"[+] Token: {token}")
        else:
            print("[-] Token nenalezen. Restartuj instanci.")
            return
    except Exception as e:
        print(f"[-] Chyba připojení: {e}")
        return

    headers = {"Authorization": token, "Content-Type": "application/json"}

    print("[*] 2. Získávám vzorek dat (2 kola pro jistotu)...")

    # --- KROK A: Získáme první číslo ---
    r1 = requests.post(f"{BASE_URL}/play", json={"bet": 1, "guess": 1}, headers=headers)
    num1, bal1 = parse_response(r1.text)
    if num1 is None:
        print("[-] Chyba při 1. sázce.")
        print(r1.text)
        return
    print(f"    -> 1. číslo serveru: {num1}")

    # --- KROK B: Získáme druhé číslo ---
    r2 = requests.post(f"{BASE_URL}/play", json={"bet": 1, "guess": 1}, headers=headers)
    num2, bal2 = parse_response(r2.text)
    if num2 is None:
        print("[-] Chyba při 2. sázce.")
        return
    print(f"    -> 2. číslo serveru: {num2}")

    print("[*] 3. Hledám seed (s emulací JS Float math)...")

    found_predictor = None

    # Rozsah hledání +/- 200 sekund (pro jistotu)
    for offset in range(-200, 200):
        test_seed = estimated_time + offset
        predictor = HaXasinoPredictor(test_seed)

        # Simulujeme hru:
        gen1 = predictor.generate_number()
        gen2 = predictor.generate_number()

        if gen1 == num1 and gen2 == num2:
            print(f"[+] SEED NALEZEN! Offset: {offset}s (Seed: {test_seed})")
            found_predictor = predictor
            break

    if not found_predictor:
        print("[-] Seed stále nenalezen. Zkuste znovu vygenerovat token.")
        return

    print(f"[*] Aktuální zůstatek: ${bal2}")
    print("[*] 4. Jdeme si pro miliardu (All-in)...")

    current_balance = bal2

    while current_balance < 1000000000:
        # Predikce DALŠÍHO čísla
        next_val = found_predictor.generate_number()

        # Vsadíme všechno
        bet = current_balance
        if bet <= 0:
            print("[-] Máš 0 peněz. Game Over.")
            break

        try:
            r = requests.post(f"{BASE_URL}/play", json={"bet": bet, "guess": next_val}, headers=headers)

            # Kontrola vlajky
            if "HTB{" in r.text or "flag" in r.text.lower() or "vlajka" in r.text.lower():
                print("\n" + "#" * 50)
                print("VICTORY! VLAJKA NALEZENA:")
                print(r.text)
                print("#" * 50)
                break

            check_num, new_bal = parse_response(r.text)

            if new_bal is not None:
                current_balance = new_bal
                print(f"[+] Výhra! Číslo: {next_val}, Zůstatek: ${current_balance}")
            else:
                print("[-] Divná odpověď (možná výhra bez vlajky?):")
                print(r.text)
                break

        except Exception as e:
            print(f"[-] Chyba: {e}")
            break


if __name__ == "__main__":
    solve()