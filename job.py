import string
from collections import Counter

# ---------- NASTAVENÍ ----------
KEY_LEN = 12
ALPHABET = string.ascii_lowercase

# Frekvence písmen v angličtině
EN_FREQ = {
    'a': 0.08167, 'b': 0.01492, 'c': 0.02782, 'd': 0.04253,
    'e': 0.12702, 'f': 0.02228, 'g': 0.02015, 'h': 0.06094,
    'i': 0.06966, 'j': 0.00153, 'k': 0.00772, 'l': 0.04025,
    'm': 0.02406, 'n': 0.06749, 'o': 0.07507, 'p': 0.01929,
    'q': 0.00095, 'r': 0.05987, 's': 0.06327, 't': 0.09056,
    'u': 0.02758, 'v': 0.00978, 'w': 0.02360, 'x': 0.00150,
    'y': 0.01974, 'z': 0.00074
}

def char_to_num(c):
    return ord(c) - 97

def num_to_char(n):
    return chr(n + 97)

def affine_vigenere_decrypt(ct, key):

    pt = ""
    for i, c in enumerate(ct):
        ci = char_to_num(c)
        ki = char_to_num(key[i % len(key)])
        # Použití inverzního prvku pro dešifrování
        pi = (21 * (ci - ki)) % 26
        pt += num_to_char(pi)
    return pt

def chi_squared(text):

    freq = Counter(text)
    n = len(text)
    chi = 0
    for c in ALPHABET:
        observed = freq.get(c, 0)
        expected = EN_FREQ[c] * n
        chi += (observed - expected) ** 2 / expected
    return chi

# ---------- NAČTENÍ DAT ----------
with open("job.txt", "r") as f:
    ciphertext = f.read().strip()

# ---------- HLEDÁNÍ KLÍČE ----------
key = ""

# Analýza každé pozice v klíči
for i in range(KEY_LEN):
    segment = ciphertext[i::KEY_LEN]
    best_shift = None
    best_score = float("inf")


    for k in range(26):
        decrypted = ""
        for c in segment:
            ci = char_to_num(c)
            pi = (21 * (ci - k)) % 26
            decrypted += num_to_char(pi)

        score = chi_squared(decrypted)
        if score < best_score:
            best_score = score
            best_shift = k

    key += num_to_char(best_shift)

print("[+] Nalezený klíč:", key)

# ---------- DEŠIFROVÁNÍ ----------
plaintext = affine_vigenere_decrypt(ciphertext, key)
print("\n[+] Část otevřeného textu:\n")
print(plaintext[:1500])