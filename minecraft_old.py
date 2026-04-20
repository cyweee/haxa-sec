import socket


# Funkce pro kódování do formátu VarInt, který Minecraft protokol vyžaduje
def send_varint(val):
    res = b''
    while True:
        byte = val & 0x7F
        val >>= 7
        if val: byte |= 0x80
        res += bytes([byte])
        if not val: break
    return res


# Funkce pro kódování textu s VarInt délkou na začátku
def send_string(string):
    encoded = string.encode('utf-8')
    return send_varint(len(encoded)) + encoded


# Parametry cíle
host = '18.198.48.212'
port = 80

print(f"[*] Připojuji se k {host}:{port}...")

try:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(5)
    s.connect((host, port))

    # 1. KROK: Sestavení Handshake paketu
    protocol_version = send_varint(47)  # Verze protokolu (např. 47 = verze 1.8)
    server_address = send_string(host)
    server_port = port.to_bytes(2, byteorder='big')
    next_state = send_varint(1)  # 1 znamená "Status Request"

    handshake_data = send_varint(0x00) + protocol_version + server_address + server_port + next_state
    handshake_packet = send_varint(len(handshake_data)) + handshake_data

    # 2. KROK: Sestavení Request paketu (žádost o ping)
    request_data = send_varint(0x00)
    request_packet = send_varint(len(request_data)) + request_data

    # Odeslání paketů
    print("[*] Odesílám Handshake a Status Request...")
    s.send(handshake_packet)
    s.send(request_packet)

    # 3. KROK: Čtení odpovědi
    print("[*] Čekám na odpověď...")
    response = s.recv(4096)

    # Výpis odpovědi. Ignorujeme nečitelné bajty na začátku (délky paketů)
    print("\n=== RAW ODPOVĚĎ SERVERU ===")
    print(response.decode('utf-8', errors='ignore'))
    print("===========================\n")

    s.close()
except Exception as e:
    print(f"[!] Chyba: {e}")