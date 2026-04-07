import urllib.request
import json
import base64
import struct

# Připojení na Solana Devnet RPC
url = "https://api.devnet.solana.com"

# Požadavek na získání dat účtu
payload = json.dumps({
    "jsonrpc": "2.0",
    "id": 1,
    "method": "getAccountInfo",
    "params": [
        "DP9RatLeM8rZwAoKTPw6Nksq7dSCkZrbrLx16n7Bzqgu",
        {"encoding": "base64"}
    ]
}).encode('utf-8')

req = urllib.request.Request(url, data=payload, headers={'Content-Type': 'application/json'})

print("Spouštím sítě do vln Devnetu...")

try:
    with urllib.request.urlopen(req) as response:
        res_data = json.loads(response.read().decode('utf-8'))
except Exception as e:
    print(f"Chyba při komunikaci s uzlem: {e}")
    exit()

if 'result' not in res_data or not res_data['result']['value']:
    print("Účet nebyl nalezen. Jste si jisti, že truhla nebyla přesunuta?")
    exit()

# Stažení a dekódování Base64 dat
b64_data = res_data['result']['value']['data'][0]
data = base64.b64decode(b64_data)

offset = 0

# 1. Přeskočení Anchor Discriminatoru (8 bajtů)
offset += 8

# 2. bump (1 bajt) a version (1 bajt)
bump = data[offset]
version = data[offset + 1]
offset += 2

# 3. Přeskočení 'noise' pole (32 bajtů)
offset += 32

# 4. Zjištění počtu kousků vlajky (4 bajty, u32 little-endian)
chunks_len = struct.unpack('<I', data[offset:offset + 4])[0]
offset += 4

chunks = []

# 5. Iterace skrze všechny kousky (chunks)
for _ in range(chunks_len):
    # Přečtení 'order'
    order = data[offset]
    offset += 1

    # Přečtení délky textu
    str_len = struct.unpack('<I', data[offset:offset + 4])[0]
    offset += 4

    # Přečtení samotného textu (UTF-8)
    text_bytes = data[offset:offset + str_len]
    text = text_bytes.decode('utf-8')
    offset += str_len

    chunks.append((order, text))

# Seřazení kousků podle jejich pořadí (pro případ, že je tvůrce zpřeházel)
chunks.sort(key=lambda x: x[0])

# Složení pokladu
flag_content = "".join([c[1] for c in chunks])
print("\n🎉 Úspěch! Zde je vaše vlajka:")
print(f"haxagon{{{flag_content}}}")