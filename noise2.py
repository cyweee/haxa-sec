from PIL import Image
import numpy as np


def find_true_poly_key_length(image_path):
    # Cíl: Zelený kanál (1) a Bitová rovina 1
    CHANNEL_INDEX = 1
    BIT_INDEX = 1
    mask = 2 ** BIT_INDEX

    img = Image.open(image_path)
    data = np.array(img)

    # 1. Extrakce Surových Bajtů (Stejný postup jako dříve)
    green_channel = data[:, :, CHANNEL_INDEX]
    lsb_bits = ((green_channel & mask) // mask).flatten()

    extracted_bytes = []
    for i in range(0, len(lsb_bits) - 7, 8):
        byte_bits = lsb_bits[i:i + 8]
        byte_bits_reversed = byte_bits[::-1]
        byte_value = np.packbits(byte_bits_reversed)[0]
        extracted_bytes.append(byte_value)
        if len(extracted_bytes) > 100:
            break

    cipher_text = bytes(extracted_bytes)
    KNOWN_PLAINTEXT = b'haxagon{'  # Klíčový začátek zprávy

    print("\n--- Hledání správné délky klíče (1 až 15) ---")

    # 2. Iterace přes různé délky klíče (Polyalfabetický XOR)
    for assumed_key_length in range(1, 16):

        # Vypočítáme prvních 'assumed_key_length' bajtů klíče
        # Klíč se vypočítá: Klíč = Šifrovaný text XOR Známý text
        key_bytes_test = bytes(
            c ^ p for c, p in zip(cipher_text[:assumed_key_length], KNOWN_PLAINTEXT[:assumed_key_length]))

        # 3. Dekódování celé zprávy s touto délkou klíče
        decrypted_bytes = []
        for i, byte in enumerate(cipher_text):
            key_byte = key_bytes_test[i % assumed_key_length]
            decrypted_bytes.append(byte ^ key_byte)

        final_text_attempt = bytes(decrypted_bytes).decode('ascii', errors='ignore')

        # 4. Hledání vlajky v dešifrovaném textu
        if final_text_attempt.lower().startswith("haxagon{"):
            end_index = final_text_attempt.find("}")
            final_flag = final_text_attempt[:end_index + 1]

            print("\n🎉 Vlajka NALEZENA (správná délka klíče)!")
            print("--------------------------------------------------")
            print(f"POUŽITÁ DÉLKA KLÍČE: {assumed_key_length}")
            print(f"FLAG: {final_flag}")
            print("--------------------------------------------------")
            return final_flag

        # Zobrazíme, jak dešifrovaný text začíná, pokud to není flag
        print(f"Délka {assumed_key_length}: '{final_text_attempt[:20]}...'")

    print("\n🚨 Nenašli jsme platnou délku klíče pro 'haxagon{'. Poslední možností je Base64 bez validace.")


# Spuštění funkce
find_true_poly_key_length("noise.bmp")