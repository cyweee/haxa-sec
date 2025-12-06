import ctypes
def to_int32(v):
    """Zajistí, že číslo se chová jako 32-bitové signed integer (jako v C)"""
    return ctypes.c_int32(v).value


def solve():
    # Hodnoty vyčtené ze souboru a kódu
    id_part = 1000
    date_part = 20251231

    # 1. Inicializace SEEDU (podle kódu: rax_23 = rax_17 ^ 0xc2000001)
    seed = to_int32(date_part ^ 0xc2000001)

    # 2. "Zahřívací" smyčka (LCG algoritmus)
    # V kódu: smyčka běží 16x (od i=16 do 1)
    for _ in range(16):
        # rax_23 = rax_23 * 0x19660d + 0x3c6ef35f
        seed = to_int32(seed * 0x19660d + 0x3c6ef35f)

    # 3. Generování klíče (8 bajtů = 16 hex znaků)
    id_tracker = id_part
    result_hex = ""

    for _ in range(8):
        # Aktualizace stavu generátoru
        seed = to_int32(seed * 0x19660d + 0x3c6ef35f)

        # rcx_4 = rax_23 >> 0x10 ^ rax_23
        # Pozor: v C je shift doprava u signed int aritmetický (zachovává znaménko)
        rcx_4 = to_int32((seed >> 16) ^ seed)

        # ROLD(rcx_4, rcx_4) -> Rotace bitů doleva
        # Velikost rotace je dána spodními 5 bity čísla
        shift_amt = rcx_4 & 0x1F
        u_rcx_4 = ctypes.c_uint32(rcx_4).value  # Pro rotaci potřebujeme unsigned
        rotated = (u_rcx_4 << shift_amt) | (u_rcx_4 >> (32 - shift_amt))
        rotated = rotated & 0xFFFFFFFF

        # char rcx_6 = ROLD(...) ^ r13_3 (aktuální hodnota ID)
        byte_val = (rotated ^ id_tracker) & 0xFF

        # r13_3 -= 0x62 (úprava ID pro další kolo)
        id_tracker = to_int32(id_tracker - 0x62)

        # Přidání hex hodnoty do výsledku
        result_hex += f"{byte_val:02x}"

    final_key = f"1000-{date_part}-{result_hex}"
    print(f"VÁŠ KLÍČ: {final_key}")
    print(f"Příkaz: curl -X GET \"http://51.20.136.165/test?key={final_key}\"")


if __name__ == "__main__":
    solve()