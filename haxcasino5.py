import requests
import z3
import time

# --- KONFIGURACE ---
BASE_URL = "http://51.20.129.55:8080"
# Kolik kroků do budoucnosti prohledáváme při ztrátě signálu (Python zvládne miliony rychle)
MAX_RESYNC_DEPTH = 50000

s = requests.Session()
# Zvýšíme buffery pro síť
adapter = requests.adapters.HTTPAdapter(pool_connections=10, pool_maxsize=10)
s.mount('http://', adapter)


def get_balance():
    try:
        r = s.get(f"{BASE_URL}/balance", timeout=3)
        return int(r.text)
    except:
        return 0


def init_game():
    try:
        s.get(f"{BASE_URL}/init", timeout=3)
        print("[*] Hra inicializována.")
    except:
        pass


def place_bet(val, amount):
    try:
        # Timeout velmi krátký, potřebujeme rychlost
        r = s.get(f"{BASE_URL}/bet", params={'betVal': int(val), 'betAmount': int(amount)}, timeout=2)
        return r
    except:
        return None


def get_prev_val():
    try:
        r = s.get(f"{BASE_URL}/prevVal", timeout=3)
        return int(r.text)
    except:
        return None


# --- V8 XorShift128+ ---
def v8_step(state0, state1):
    s1 = state0
    s0 = state1
    state0 = s0
    s1 ^= (s1 << 23) & 0xFFFFFFFFFFFFFFFF
    s1 ^= (s1 >> 17)
    s1 ^= s0
    s1 ^= (s0 >> 26)
    state1 = s1
    return state0, state1


def v8_predict(state0, state1):
    res = (state0 + state1) & 0xFFFFFFFFFFFFFFFF
    return (res >> 12) * 2


# --- Z3 Solver ---
def z3_xorshift_step(s0, s1):
    orig_s0, orig_s1 = s0, s1
    new_s0 = orig_s1
    calc = orig_s0
    calc = calc ^ (calc << 23)
    calc = calc ^ z3.LShR(calc, 17)
    calc = calc ^ orig_s1
    calc = calc ^ z3.LShR(orig_s1, 26)
    new_s1 = calc
    return new_s0, new_s1


def find_seed_fast(history):
    # Protože víme, že GAP je 0 (z vašich logů), zjednodušíme solver na maximum.
    # To zrychlí start.
    print(f"[*] Rychlý výpočet seedu z {len(history)} vzorků...")
    solver = z3.Solver()
    s0 = z3.BitVec('s0', 64)
    s1 = z3.BitVec('s1', 64)

    # Použijeme poslední 2 čísla
    val_A = history[-2]
    val_B = history[-1]

    curr_s0, curr_s1 = s0, s1
    # Stav A
    solver.add(z3.LShR(curr_s0 + curr_s1, 12) == (val_A // 2))
    # Posun
    curr_s0, curr_s1 = z3_xorshift_step(curr_s0, curr_s1)
    # Stav B
    solver.add(z3.LShR(curr_s0 + curr_s1, 12) == (val_B // 2))

    if solver.check() == z3.sat:
        m = solver.model()
        f_s0, f_s1 = m[s0].as_long(), m[s1].as_long()

        # Posuneme stav do přítomnosti (po val_B)
        rec_s0, rec_s1 = f_s0, f_s1
        rec_s0, rec_s1 = v8_step(rec_s0, rec_s1)  # po A
        rec_s0, rec_s1 = v8_step(rec_s0, rec_s1)  # po B
        return rec_s0, rec_s1
    return None, None


def measure_lag(s0, s1):
    """
    Změří, jak daleko je server oproti našemu lokálnímu stavu.
    """
    print("    [?] Kalibrace lagu sítě...", end="", flush=True)
    real_val = get_prev_val()
    if not real_val: return 0, s0, s1

    # Hledáme real_val v naší budoucnosti
    t_s0, t_s1 = s0, s1
    for i in range(MAX_RESYNC_DEPTH):
        pred = v8_predict(t_s0, t_s1)
        if pred == real_val:
            # Našli jsme ho! Server je o 'i' kroků napřed.
            # Musíme náš stav posunout na 'i + 1' (abychom byli připraveni na další)
            t_s0, t_s1 = v8_step(t_s0, t_s1)
            print(f" Hotovo. Server lag: {i} kroků.")
            return i, t_s0, t_s1

        t_s0, t_s1 = v8_step(t_s0, t_s1)

    print(" Chyba kalibrace.")
    return 0, s0, s1


def main():
    print("========================================")
    print("     HAXASINO SNIPER (LAG COMP)         ")
    print("========================================")

    init_game()

    # 1. Získání seedu (Jednorázově!)
    history = []
    print("[*] Sbírám data pro seed...")
    failsafe = 0
    while len(history) < 5 and failsafe < 20:
        place_bet(0, 1)
        val = get_prev_val()
        if val and (not history or history[-1] != val):
            history.append(val)
            print(f"    {val}")
        failsafe += 1

    s0, s1 = find_seed_fast(history)
    if s0 is None:
        print("[-] Seed nenalezen. Restartujte skript.")
        return

    print("[+] SEED ULOŽEN. Zahajuji synchronizaci.")

    # 2. Synchronizace a měření lagu
    # Zjistíme, kde přesně jsme
    lag, curr_s0, curr_s1 = measure_lag(s0, s1)

    # Nastavíme "Offset" - kolik kroků dopředu budeme střílet
    # Pokud je lag 10, znamená to, že mezi naším requestem a odpovědí uběhlo 10 čísel.
    # Musíme střílet na (Lag / 2) + Safety Margin
    # Zkusíme dynamický offset. Začneme na lag + 2.
    offset = lag + 3
    print(f"[*] Nastavuji předsazení střelby (Offset): +{offset}")

    consecutive_losses = 0

    while True:
        balance = get_balance()
        if balance >= 1_000_000_000:
            print(f"\n[!!!] VÍTĚZSTVÍ! Balance: {balance}")
            print(place_bet(0, 1).text)
            break

        if balance <= 0:
            print("[-] Bankrot. Restartuji hru...")
            init_game()
            history = []  # Reset pro nový seed
            # ... zde by to chtělo rekurzivní volání nebo loop, ale pro jednoduchost:
            print("Restartujte skript ručně.")
            return

        # --- PREDIKCE S OFFSETEM ---
        # Musíme predikovat číslo, které bude vygenerováno za 'offset' kroků
        # Vytvoříme si dočasný stav pro predikci
        future_s0, future_s1 = curr_s0, curr_s1
        for _ in range(offset):
            future_s0, future_s1 = v8_step(future_s0, future_s1)

        target_val = v8_predict(future_s0, future_s1)

        # Sázka
        bet_amt = balance if balance < 1_000_000_000 else 1_000_000_000

        # Odeslání
        # print(f"    Střílím na {target_val} (Offset {offset})...")
        res = place_bet(target_val, bet_amt)

        # --- POSUN STAVU ---
        # Náš lokální stav musíme posunout o 1, protože jsme udělali 1 request (sázku)
        # Tím udržujeme krok se serverem.
        curr_s0, curr_s1 = v8_step(curr_s0, curr_s1)

        # --- VYHODNOCENÍ ---
        if res and "Better luck" in res.text:
            # Prohra
            consecutive_losses += 1
            if consecutive_losses % 3 == 0:
                print(f"    [!] 3x Prohra v řadě. Server nám utíká. Rekalibrace...")
                # Pokud prohráváme, asi je náš offset špatně nebo se server posunul víc.
                # Změříme, kde server DOOPRAVDY je.
                lag_new, curr_s0, curr_s1 = measure_lag(curr_s0, curr_s1)

                # Pokud lag roste, musíme zvýšit offset
                offset = lag_new + 2
                print(f"    [+] Nový offset: +{offset}")
                consecutive_losses = 0

        elif res and ("Win" in res.text or "balance" in res.text):
            print(f"    [+] ZÁSAH! Balance: {balance + bet_amt}")
            consecutive_losses = 0
            # Pokud vyhráváme, offset je perfektní. Neměnit.

        elif res and "Vlajka" in res.text:
            print(res.text)
            break


if __name__ == "__main__":
    main()