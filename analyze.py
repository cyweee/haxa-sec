#!/usr/bin/env python3
# export_vcd.py
import numpy as np
import pandas as pd

CHUNK = 5_000_000
# Napěťové prahy odvozené z našich předchozích histogramů
THRESHOLDS = {0: 1.0, 1: 1.0, 2: 1.5, 3: 1.5}  # CH1, CH2, CH3, CH4

print("Inicializuji VCD exportér...")

# Čteme všechny 4 kanály najednou po blocích
iters = [
    pd.read_csv(f'ch{i}_full_capture.csv', names=['t', 'v'], skiprows=1, dtype=np.float32, chunksize=CHUNK)
    for i in range(1, 5)
]

with open('capture.vcd', 'w') as f:
    # VCD Hlavička
    f.write("$date\n  Today\n$end\n")
    f.write("$version\n  Haxagon CTF Exporter\n$end\n")
    f.write("$timescale\n  20 ns\n$end\n")  # 50 MHz = 20 ns
    f.write("$scope module logic $end\n")

    chars = ['!', '"', '#', '$']
    for i in range(4):
        f.write(f"$var wire 1 {chars[i]} CH{i + 1} $end\n")

    f.write("$upscope $end\n")
    f.write("$enddefinitions $end\n")

    time_offset = 0
    states = np.zeros(4, dtype=np.uint8)
    first_chunk = True
    chunk_idx = 0

    while True:
        try:
            chunks = [next(it)['v'].values for it in iters]
        except StopIteration:
            break

        chunk_idx += 1
        print(f"Zpracovávám blok {chunk_idx} (čas {time_offset * 20} ns)...")

        # Binarizace signálu (převod na 1 a 0 podle prahu)
        dig = np.array([(chunks[i] > THRESHOLDS[i]).astype(np.uint8) for i in range(4)])

        # Zápis počátečního stavu
        if first_chunk:
            f.write(f"#{time_offset}\n")
            for i in range(4):
                f.write(f"{dig[i, 0]}{chars[i]}\n")
            first_chunk = False
        else:
            # Kontrola změny na přechodu mezi bloky
            for i in range(4):
                if dig[i, 0] != states[i]:
                    f.write(f"#{time_offset}\n{dig[i, 0]}{chars[i]}\n")

        # Hledání všech indexů, kde se změnil jakýkoliv kanál
        changes = np.any(dig[:, 1:] != dig[:, :-1], axis=0)
        change_indices = np.where(changes)[0] + 1

        # Zápis změn do VCD
        for idx in change_indices:
            f.write(f"#{time_offset + idx}\n")
            for i in range(4):
                if dig[i, idx] != dig[i, idx - 1]:
                    f.write(f"{dig[i, idx]}{chars[i]}\n")

        # Aktualizace pro další kolo
        time_offset += len(chunks[0])
        for i in range(4):
            states[i] = dig[i, -1]

print("Hotovo! Vytvořen soubor 'capture.vcd'.")