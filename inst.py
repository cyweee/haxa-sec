import hashlib
from itertools import permutations

# 1. NASTAVENÍ (Zadání z úlohy)
# Používáme .strip(), aby nás nerozhodily neviditelné mezery
target_hash = "f1b1dc7749cbb0f581e4717e36d3475b".strip()

# 2. SLOVNÍK (Data z OSINT analýzy fotek)
elements = [
    "jessica", "wild", "jess", "jessie",  # Jména
    "buddy",  # Pes
    "la", "losangeles",  # Lokalita
    "1998", "98",  # Roky
    "125", "198", "94"  # Statistiky z profilu
]


def print_win(password, hsh):
    print("\n" + "!" * 45)
    print(f" [+] ÚSPĚCH! HESLO NALEZENO: {password}")
    print(f" [+] Odpovídající hash: {hsh}")
    print(f" [+] FINÁLNÍ VLAJKA: haxagon{{{password}}}")
    print("!" * 45 + "\n")


def solve():
    print(f"[*] Spouštím diagnostiku a brute-force útok...")
    print(f"[*] Cílový hash: {target_hash}")

    found = False
    tested_count = 0

    # FÁZE 1: Samostatná slova a jejich variace
    for word in elements:
        # Zkoušíme: buddy, Buddy, BUDDY
        for variant in [word.lower(), word.capitalize(), word.upper()]:
            tested_count += 1
            current_hash = hashlib.md5(variant.encode('utf-8')).hexdigest()
            if current_hash == target_hash:
                print_win(variant, current_hash)
                return

    # FÁZE 2: Kombinace DVOU prvků (nejpravděpodobnější scénář)
    # Zkoušíme: buddy1998, jessica_wild, jessla atd.
    for combo in permutations(elements, 2):
        # Definujeme různé typy spojení
        templates = [
            f"{combo[0]}{combo[1]}",  # buddy1998
            f"{combo[0]}_{combo[1]}",  # buddy_1998
            f"{combo[0]}.{combo[1]}",  # buddy.1998
        ]

        for base in templates:
            # Pro každou šablonu zkusíme různé velikosti písmen
            variants = [base.lower(), base.capitalize(), base.upper()]

            # Speciální případ: Velké písmeno u obou slov (JessicaWild)
            if "_" not in base and "." not in base:
                variants.append(combo[0].capitalize() + combo[1].capitalize())

            for final_v in variants:
                tested_count += 1
                current_hash = hashlib.md5(final_v.encode('utf-8')).hexdigest()
                if current_hash == target_hash:
                    print_win(final_v, current_hash)
                    return

    print(f"[-] Prohledáno {tested_count} variant.")
    print("[-] Heslo nebylo nalezeno. Zkontroluj, zda je hash v zadání správně.")


if __name__ == "__main__":
    solve()