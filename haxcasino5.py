import requests
from z3 import *
import time

BASE_URL = "http://16.170.157.175:8080"


def rotl(x, k):
    return (x << k) | LShR(x, 64 - k)


def xoshiro_step(s0, s1, s2, s3):
    res = s0 + s3
    t = s1 << 17
    s2 ^= s0;
    s3 ^= s1;
    s1 ^= s2;
    s0 ^= s3;
    s2 ^= t
    s3 = rotl(s3, 45)
    return s0, s1, s2, s3, res


def solve_optimized():
    session = requests.Session()
    print("[*] Sběr dat (4 vzorky stačí)...")
    session.get(f"{BASE_URL}/init")
    samples = []
    for i in range(4):
        session.get(f"{BASE_URL}/bet?betVal=1&betAmount=1")
        val = int(session.get(f"{BASE_URL}/prevVal").text)
        samples.append(val // 2)
        print(f"  S{i + 1}: {val}")

    # Definice symbolických proměnných
    st = [BitVec(f's{i}', 64) for i in range(4)]

    print("[*] Předgenerování symbolické cesty (Xoshiro256+)...")
    curr = st
    cache = []
    # Generujeme 128 kroků, abychom pokryli i přechod mezi dávkami (Double-Batch)
    for _ in range(128):
        ns0, ns1, ns2, ns3, out = xoshiro_step(*curr)
        cache.append(LShR(out, 12))
        curr = [ns0, ns1, ns2, ns3]

    # Vytvoření sekvence, jak ji V8 vydává: [Batch1_Reverse, Batch2_Reverse]
    sequence = []
    for i in range(63, -1, -1): sequence.append(cache[i])
    for i in range(127, 63, -1): sequence.append(cache[i])

    print("[*] Spouštím Solver (Sliding Window)...")
    solver = Solver()
    solver.add(Or([x != 0 for x in st]))

    # Hledáme, kde v této 128-hodnotové sekvenci sedí naše 4 vzorky
    # Použijeme symbolický index 'pos', aby Z3 hledal efektivněji
    pos = Int('pos')
    solver.add(pos >= 0, pos <= (128 - len(samples)))

    for i in range(len(samples)):
        # Pro každý vzorek vytvoříme podmínku: "Na pozici pos+i je vzorek samples[i]"
        # To uděláme pomocí If-Else stromu pro stabilitu
        cond = False
        for p in range(128 - len(samples)):
            cond = If(pos == p, sequence[p + i] == samples[i], cond)
        solver.add(cond)

    start_time = time.time()
    if solver.check() == sat:
        m = solver.model()
        res_pos = m[pos].as_long()
        res_st = [m[x].as_long() for x in st]
        print(f"\n[+++] SAT! Pozice: {res_pos}")
        print(f"[!] Počáteční stav: {res_st}")
        print(f"[*] Čas výpočtu: {time.time() - start_time:.2f}s")
        return session, res_st, res_pos
    else:
        print("\n[X] Model Xoshiro256+ neodpovídá. Zkuste znovu (možná jiný PRNG).")


if __name__ == "__main__":
    solve_optimized()