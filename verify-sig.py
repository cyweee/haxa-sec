import socket
import re
import hashlib
from ecdsa import VerifyingKey, NIST256p, SECP256k1
from ecdsa.keys import BadSignatureError


def solve():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect(("13.53.44.95", 1337))
    s.settimeout(2)

    def get_data():
        data = ""
        while "Your answer >" not in data:
            try:
                chunk = s.recv(4096).decode(errors='ignore')
                if not chunk: break
                data += chunk
            except socket.timeout:
                break
        return data

    for i in range(1, 101):
        raw = get_data()

        # Pokud server poslal WRONG nebo jsme nenašli prompt, konec
        if not raw or "WRONG" in raw:
            print(f"❌ Server zamítl odpověď v kole {i - 1} a ukončil spojení!")
            print("Data ze serveru:\n", raw)
            break

        try:
            m = re.search(r"Message:\s*(.*)", raw).group(1).strip()
            sig_h = re.search(r"Signature:\s*([0-9a-fA-F]+)", raw).group(1).strip()
            key_h = re.search(r"Key:\s*([0-9a-fA-F]+)", raw).group(1).strip()

            msg_b = m.encode()
            sig_b = bytes.fromhex(sig_h)
            key_b = bytes.fromhex(key_h)

            ans = "FALSE"

            # Vyzkoušíme obě hlavní 256bitové křivky
            curves = [NIST256p, SECP256k1]
            # Vyzkoušíme SHA-256 i SHA-1 (některé staré verze ecdsa měly SHA-1 jako default)
            hash_funcs = [hashlib.sha256, hashlib.sha1]

            for curve in curves:
                try:
                    # from_string očekává přesně 64 bajtů (X a Y)
                    vk = VerifyingKey.from_string(key_b, curve=curve)
                    for h in hash_funcs:
                        try:
                            # verify očekává přesně 64 bajtů (R a S)
                            vk.verify(sig_b, msg_b, hashfunc=h)
                            ans = "TRUE"
                            break  # Podpis je platný!
                        except BadSignatureError:
                            continue
                        except Exception:
                            continue
                    if ans == "TRUE":
                        break
                except Exception:
                    continue

            print(f"Kolo {i}/100: Odesílám {ans}")
            s.sendall(f"{ans}\n".encode())

        except Exception as e:
            print(f"Chyba při parsování: {e}")
            break

    # Přečtení finální vlajky, pokud projdeme 100. kolem
    try:
        print("\nOdpověď ze serveru:")
        print(s.recv(4096).decode(errors='ignore'))
    except:
        pass


if __name__ == "__main__":
    solve()