#!/usr/bin/env python3
# pip install requests z3-solver
# доделать

import requests
import time
from z3 import *
import sys

HOST = "13.48.6.0"
PORT = "8080"
BASE = f"http://{HOST}:{PORT}"

# Настройки
BET_AMOUNT = 1
PER_CHECK_TIMEOUT_MS = 30000  # увеличенный таймаут для Z3 (30s)
# --------------------------------------------------------

def http(path):
    url = BASE + path
    r = requests.get(url, timeout=10)
    r.raise_for_status()
    return r.text.strip()

def collect_three_prevvals():
    print("[*] Calling /init")
    print(http("/init"))
    vals = []
    for i in range(3):
        print(f"[*] Placing bet #{i+1}")
        print(http(f"/bet?betVal=0&betAmount={BET_AMOUNT}"))
        t = http("/prevVal")
        print("    prevVal ->", t)
        vals.append(int(t))
        # tiny sleep to avoid accidental race; keep short
        time.sleep(0.05)
    return vals

# --- Z3 solver (оптимизированный перебор вариантов, с таймаутом) ---

MASK64 = (1 << 64) - 1
POW2_53 = 1 << 53

def try_solve_with_variants(observed, per_check_timeout_ms):
    # используем те же варианты, что и раньше, но с большим таймаутом
    def xsA(cur_s0, cur_s1):
        t = cur_s0
        s1 = cur_s1
        s1_x = s1 ^ ((s1 << 23) & BitVecVal(MASK64,64))
        s1_x = s1_x ^ LShR(s1_x, 17)
        s1_x = s1_x ^ t
        s1_x = s1_x ^ LShR(t, 26)
        result = (t + s1_x) & BitVecVal(MASK64,64)
        return result, s1_x, t

    def xsB(cur_s0, cur_s1):
        t = cur_s0
        s1 = cur_s1
        s1_x = s1 ^ LShR(s1, 17)
        s1_x = s1_x ^ ((s1_x << 23) & BitVecVal(MASK64,64))
        s1_x = s1_x ^ t
        s1_x = s1_x ^ LShR(t, 26)
        result = (t + s1_x) & BitVecVal(MASK64,64)
        return result, s1_x, t

    variants = [('A', xsA), ('B', xsB)]
    possible_shifts = [12, 11, 13]
    possible_offsets = [0,1,2]

    for name, func in variants:
        for sh in possible_shifts:
            for off in possible_offsets:
                print(f"[*] Trying variant {name}, shift >>>{sh}, offset {off} (timeout {per_check_timeout_ms} ms)")
                s = Solver()
                s.set("timeout", per_check_timeout_ms)
                s0 = BitVec('s0', 64)
                s1 = BitVec('s1', 64)
                cur0, cur1 = s0, s1
                for _ in range(off):
                    res_init, n0, n1 = func(cur0, cur1)
                    cur0, cur1 = n0, n1
                ok = True
                for obs in observed:
                    res_i, n0_i, n1_i = func(cur0, cur1)
                    topbits = LShR(res_i, sh) & BitVecVal((1 << (64 - sh)) - 1, 64)
                    s.add(topbits == BitVecVal(obs & ((1 << (64 - sh)) - 1), 64))
                    cur0, cur1 = n0_i, n1_i
                st = s.check()
                print("    Z3 returned", st)
                if st == sat:
                    m = s.model()
                    s0_found = m[s0].as_long() & MASK64
                    s1_found = m[s1].as_long() & MASK64
                    print(">>> FOUND with", name, "shift", sh, "offset", off)
                    print("s0 =", s0_found)
                    print("s1 =", s1_found)
                    return name, sh, off, s0_found, s1_found
    return None

def step_int_variant_A(s0_i, s1_i):
    s1_l = s1_i ^ ((s1_i << 23) & MASK64)
    s1_l ^= (s1_l >> 17)
    s1_l ^= s0_i
    s1_l ^= (s0_i >> 26)
    res_i = (s0_i + s1_l) & MASK64
    return res_i, s1_l & MASK64, s0_i & MASK64

def step_int_variant_B(s0_i, s1_i):
    s1_l = s1_i ^ (s1_i >> 17)
    s1_l ^= ((s1_l << 23) & MASK64)
    s1_l ^= s0_i
    s1_l ^= (s0_i >> 26)
    res_i = (s0_i + s1_l) & MASK64
    return res_i, s1_l & MASK64, s0_i & MASK64

if __name__ == "__main__":
    print("[*] Collecting 3 prevVal from server")
    try:
        observed = collect_three_prevvals()
    except Exception as e:
        print("HTTP error:", e)
        sys.exit(1)

    print("[*] Observed:", observed)
    # quick sanity
    for v in observed:
        if not (0 <= v < POW2_53):
            print("Value out of range:", v)
            sys.exit(1)

    res = try_solve_with_variants(observed, PER_CHECK_TIMEOUT_MS)
    if not res:
        print("[!] No solution found. Возможные действия:")
        print(" - Повторить сбор трех подряд prevVal (init -> 3 bets -> prevVal).")
        print(" - Дать больший timeout (увеличить PER_CHECK_TIMEOUT_MS).")
        print(" - Прислать сюда точный лог команд и ответов; я посмотрю.")
        sys.exit(1)

    name, sh, off, s0, s1 = res
    # выберем корректную integer-step функцию
    step_int = step_int_variant_A if name == 'A' else step_int_variant_B

    cur0, cur1 = s0, s1
    for _ in range(off):
        _, cur0, cur1 = step_int(cur0, cur1)
    # пропустить три наблюдения (они уже были)
    for _ in range(3):
        _, cur0, cur1 = step_int(cur0, cur1)
    next_res, _, _ = step_int(cur0, cur1)
    predicted = (next_res >> sh) & ((1 << (64 - sh)) - 1)
    print("[+] Predicted next prevVal (betVal) =", predicted)
    print(f'curl "{BASE}/bet?betVal={predicted}&betAmount=1000"')
