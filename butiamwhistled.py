from minecraft.networking.connection import Connection
from minecraft.networking.packets.clientbound.play import ChatMessagePacket, JoinGamePacket, DisconnectPacket
import time

def connect(username):
    print(f"[*] Zkouším: {username}")
    conn = Connection("3.127.150.25", 25565, username=username)

    def on_chat(packet):
        print(f"[CHAT] {packet.json_data}")

    def on_join(packet):
        print(f"[+] Připojeno jako {username}")

    def on_kick(packet):
        print(f"[KICK] {packet.json_data}")

    conn.register_packet_listener(on_chat, ChatMessagePacket)
    conn.register_packet_listener(on_join, JoinGamePacket)
    conn.register_packet_listener(on_kick, DisconnectPacket)
    conn.connect()
    time.sleep(8)

for name in ["marekvospel", "admin", "Admin", "notch"]:
    try:
        connect(name)
    except Exception as e:
        print(f"[-] {name}: {e}")