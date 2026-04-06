from Crypto.Cipher import AES
import os


def decrypt_file(filepath, key):
    # Klíč musí mít přesně 64 znaků (512 bitů)
    if len(key) != 64:
        print("Chyba: Klíč musí mít 64 znaků!")
        return

    # 1. Rozdělení klíče (stejně jako v malware)
    key_bytes = key.encode('utf-8') if isinstance(key, str) else key
    key_part1 = key_bytes[:32]
    key_part2 = key_bytes[32:]

    # 2. Načtení zašifrovaného obsahu
    with open(filepath, "rb") as f:
        final_ciphertext = f.read()

    # 3. PRVNÍ KROK DEŠIFROVÁNÍ (použijeme key_part2)
    # Musíme začít od konce - tedy od cipher2
    cipher2 = AES.new(key_part2, AES.MODE_ECB)
    intermediate_data = cipher2.decrypt(final_ciphertext)

    # 4. DRUHÝ KROK DEŠIFROVÁNÍ (použijeme key_part1)
    cipher1 = AES.new(key_part1, AES.MODE_ECB)
    decrypted_padded = cipher1.decrypt(intermediate_data)

    # 5. Odstranění paddingu (malware přidával mezery b" ")
    plaintext = decrypted_padded.rstrip(b" ")

    # 6. Uložení výsledku
    output_path = filepath.replace(".enc", "")
    with open(output_path, "wb") as f:
        f.write(plaintext)

    print(f"Hotovo! Soubor dešifrován jako: {output_path}")


# --- SEM VLOŽTE KLÍČ, KTERÝ JSTE NAŠLI ---
# Ten Bitcoin wallet v ransom note (45 znaků) není celý klíč.
# Hledejte v systému řetězec dlouhý 64 znaků.
FOUND_KEY = "ZDE_VLOZ_64_ZNAKOVY_KLIC_Z_ANALYZY_NEBO_SYSTEMU"

# Příklad použití:
# decrypt_file("/data/flag.txt.enc", FOUND_KEY)