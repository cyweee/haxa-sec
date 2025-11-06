import requests

URL = 'http://16.16.122.207/tx'
ORIGINAL_TO = 0xDEADBEEF
NEW_TO = 0xCAFEBABE
FILENAME = 'tx(1).enc'


def solve():

    try:
        with open(FILENAME, 'rb') as f:
            ciphertext = bytearray(f.read())
    except FileNotFoundError:
        print(f"Chyba: Soubor '{FILENAME}' nebyl nalezen.")
        return

    if len(ciphertext) != 16:
        print(f"Varování: Očekávána délka 16 bajtů, ale soubor má {len(ciphertext)} bajtů.")

    print(f"[+] Původní ciphertext: {ciphertext.hex()}")

    xor_diff = ORIGINAL_TO ^ NEW_TO
    diff_bytes = xor_diff.to_bytes(4, 'big')
    print(f"[+] XOR rozdíl: {diff_bytes.hex()}")

    for i in range(4):
        ciphertext[4 + i] ^= diff_bytes[i]

    print(f"[+] Upravený ciphertext: {ciphertext.hex()}")

    headers = {'Content-Type': 'application/octet-stream'}

    print(f"[>] Odesílám modifikovanou transakci na {URL}...")
    try:
        response = requests.post(URL, data=ciphertext, headers=headers, timeout=5)
        print(f"\n[V] Odpověď serveru:\n{response.text}")
    except Exception as e:
        print(f"\n[X] Chyba při komunikaci se serverem: {e}")


if __name__ == '__main__':
    solve()