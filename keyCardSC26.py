import os


def calculate_uid_and_bcc(file_path):
    try:
        with open(file_path, 'rb') as f:
            data = f.read()

        # Flag 01: UID jsou první 4 bajty v Blocku 0
        uid_bytes = data[0:4]
        uid_hex = uid_bytes.hex().upper()

        # Flag 03: BCC je XOR součet všech bajtů UID
        bcc_calculated = 0
        for byte in uid_bytes:
            bcc_calculated ^= byte
        bcc_hex = f"{bcc_calculated:02X}"

        print(f"Vlajka 01 (UID): haxagon{{{uid_hex}}}")
        print(f"Vlajka 03 (BCC): haxagon{{{bcc_hex}}}")

    except FileNotFoundError:
        print(f"Soubor {file_path} nebyl nalezen.")


if __name__ == "__main__":
    calculate_uid_and_bcc('key-card.bin')

def solve_ctf(filename):
    if not os.path.exists(filename):
        print(f"Soubor {filename} nebyl nalezen.")
        return

    with open(filename, 'rb') as f:
        data = f.read()

    # 1. UID a BCC (Vlajka 01 a 03)
    # Z dumpu vidíme pattern A1 B2 C3 45, který začíná na 2. bajtu (index 1)
    # První bajt 04 je kód výrobce (NXP)
    uid = data[1:5]
    print(f"Vlajka 01 (UID): {uid.hex().upper()}")

    # Výpočet BCC (XOR všech bajtů UID)
    bcc_calculated = uid[0] ^ uid[1] ^ uid[2] ^ uid[3]
    print(f"Vlajka 03 (BCC): {bcc_calculated:02X}")

    # 2. Výrobce (Vlajka 02)
    # První bajt v dumpu je 04, což je ID výrobce NXP
    print(f"Vlajka 02 (Výrobce): NXP")

    # 3. Value Block (Vlajka 04 - Adresa 05)
    # MIFARE Value block má 16 bajtů. Hodnota je na prvních 4 bajtech (little-endian)
    block5 = data[5*16 : 6*16]
    value5 = int.from_bytes(block5[0:4], 'little')
    print(f"Vlajka 04 (Value Block 05): {value5}")

    # 4. Value Block s opravou bitu (Vlajka 05 - Adresa 06)
    block6 = data[6*16 : 7*16]
    v1 = block6[0:4]          # První kopie hodnoty
    v2_inv = block6[4:8]      # Inverzní kopie hodnoty
    v3 = block6[8:12]         # Třetí kopie hodnoty

    # Dekódujeme inverzní kopii pro porovnání
    v2 = bytes([b ^ 0xFF for b in v2_inv])

    # Hlasování: pokud se dva ze tří bloků shodují, je to správná hodnota
    if v2 == v3:
        correct_value = int.from_bytes(v3, 'little')
    elif v1 == v3:
        correct_value = int.from_bytes(v3, 'little')
    else:
        correct_value = int.from_bytes(v1, 'little')

    print(f"Vlajka 05 (Opravený Value Block 06): {correct_value}")

if __name__ == "__main__":
    solve_ctf('key-card.bin')