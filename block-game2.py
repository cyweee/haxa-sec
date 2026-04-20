import json
from pathlib import Path
from solders.keypair import Keypair

# TADY VLOŽ AKTUÁLNÍ TEXT Z WEBU (pokud se změnil, přepiš ho)
message_text = "impossible-game-checker:BLYyPeR5xB89A9TybXfEjW7fHF5kWnpYk8XXHqXCgAuV:171a330546197adce648cf88d8a4cf45"

# Načtení klíče
keypair_path = Path.home() / ".config" / "solana" / "id.json"
with open(keypair_path, "r") as f:
    secret_key = json.load(f)
player = Keypair.from_bytes(bytes(secret_key))

# Podpis čistých UTF-8 bajtů
signature = player.sign_message(message_text.encode("utf-8"))

print(f"\nTvůj čistý podpis (Base58):\n{signature}")