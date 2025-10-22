import math
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP
from Crypto.Util.number import inverse
import binascii

# --- 1. Given data ---

pem_key = """-----BEGIN PUBLIC KEY-----
MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQCIDHP5EkMPaQ3FDL9yoHMREia5
WiTin3D2rwFvcCDc+AuVm0HiywEQQF8ZxOO4hEfvmXzVqPSojkkarDNqe8hQvsGx
lv/EjvL6ULf60Yt5BrlbLKnpkhcYSj0YRBf24lzQD8D2vzNlaW16aJXbwUzdaHN/
jUczApfsrMtkeVrirwIDAQAB
-----END PUBLIC KEY-----"""

ciphertext_hex = "7da8ffed704d231c7d8e26a61bf2da342b7e22bf1652f032588b301fb05ace8194ac1a6e82958bfd27fc653de572d6418ab8e92ff2ff82f89ca036fdad87ab5846c9c58d43e1659764db80f9057b3f6bb51faf9e96fd87dfb60a5d74e54b4f0049fd920d013d034e3677ed8f2ecd06be22825db4d395e1418b4fa9f490dd60f3"
ciphertext = bytes.fromhex(ciphertext_hex)

# --- 2. Parse public key ---

public_key = RSA.import_key(pem_key)
n = public_key.n
e = public_key.e

print(f"Modulus N ({n.bit_length()} bits):\n{n}\n")
print(f"Exponent e: {e}\n")

# --- 3. Fermat factorization ---

def is_square(n):
    if n < 0:
        return False
    x = math.isqrt(n)
    return x * x == n

print("Running Fermat factorization...")

a = math.isqrt(n) + 1
b2 = a * a - n

while not is_square(b2):
    a += 1
    b2 = a * a - n

b = math.isqrt(b2)
p = a - b
q = a + b

print("Success!\n")
print(f"p = {p}")
print(f"q = {q}\n")

assert p * q == n
print("Check p * q == n: OK\n")

# --- 4. Compute private exponent d ---

phi = (p - 1) * (q - 1)
d = inverse(e, phi)

print(f"Private exponent d ({d.bit_length()} bits):\n{d}\n")

# --- 5. Construct full private key ---

key_params = (n, e, d, p, q)
private_key = RSA.construct(key_params)

# --- 6. Decrypt message ---

cipher = PKCS1_OAEP.new(private_key)

try:
    plaintext = cipher.decrypt(ciphertext)
    flag = plaintext.decode('utf-8')

    print("--- DECRYPTED MESSAGE ---")
    print(flag)
    print("-------------------------")

except ValueError as err:
    print(f"Decryption error: {err}")
    print("Check if correct padding/schema is used (OAEP).")
