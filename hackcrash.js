const crypto = require('crypto');

function getMD5(str) {
    return crypto.createHash('md5').update(str).digest('hex');
}

const CHARS = '0123456789';

// 1. ARC4 (Základ knihovny seedrandom - velmi pravděpodobné!)
function arc4_generator(seedStr) {
    let s = [], j = 0, x, i;
    for (i = 0; i < 256; i++) s[i] = i;
    for (i = 0, j = 0; i < 256; i++) {
        j = (j + s[i] + seedStr.charCodeAt(i % seedStr.length)) % 256;
        x = s[i]; s[i] = s[j]; s[j] = x;
    }
    i = j = 0;
    return function() {
        i = (i + 1) % 256;
        j = (j + s[i]) % 256;
        x = s[i]; s[i] = s[j]; s[j] = x;
        return s[(s[i] + s[j]) % 256];
    };
}

// 2. Mulberry32 s jiným výstupem
function mulberry32_alt(seed) {
    let state = Number(seed & 0xFFFFFFFFn);
    return function() {
        state |= 0; state = state + 0x6D2B79F5 | 0;
        let t = Math.imul(state ^ state >>> 15, state | 1);
        t = t + Math.imul(t ^ t >>> 7, t | 61) | 0;
        return (t ^ t >>> 14) >>> 0;
    }
}

async function crack() {
    const TARGET_URL = 'http://3.70.137.138:8080';

    try {
        console.log(`[!] Zahajuji hloubkovou ARC4 analýzu...`);
        const res = await fetch(`${TARGET_URL}/getHash`);
        const targetHash = await res.text();
        const serverTime = res.headers.get('x-request-time');

        console.log(`[+] Cílový hash: ${targetHash}`);
        console.log(`[+] Timestamp:   ${serverTime}`);

        // Okno +- 500ms
        const baseSeed = BigInt(serverTime);
        for (let offset = -500n; offset < 500n; offset++) {
            const currentSeed = baseSeed + offset;
            const seedStr = currentSeed.toString();

            // METODA A: ARC4 (seedrandom)
            const rng_arc4 = arc4_generator(seedStr);
            let passARC4 = "";
            for (let i = 0; i < 13; i++) passARC4 += CHARS[rng_arc4() % 10];
            if (getMD5(passARC4) === targetHash) return submit(TARGET_URL, passARC4, "ARC4 (seedrandom)", offset);

            // METODA B: Mulberry32 (Bajtová varianta)
            const rng_mulberry = mulberry32_alt(currentSeed);
            let passMulberry = "";
            for (let i = 0; i < 13; i++) passMulberry += CHARS[(rng_mulberry() & 0xFF) % 10];
            if (getMD5(passMulberry) === targetHash) return submit(TARGET_URL, passMulberry, "Mulberry32-Byte", offset);

            // METODA C: Jednoduchý LCG (Numerical Recipes varianta)
            let stateLCG = currentSeed & 0xFFFFFFFFn;
            let passLCG = "";
            for (let i = 0; i < 13; i++) {
                stateLCG = (stateLCG * 1664525n + 1013904223n) & 0xFFFFFFFFn;
                passLCG += CHARS[Number(stateLCG >> 24n) % 10];
            }
            if (getMD5(passLCG) === targetHash) return submit(TARGET_URL, passLCG, "LCG-NR", offset);

            if (offset % 100n === 0n) process.stdout.write(".");
        }
        console.log(`\n[-] Žádná shoda. Pokud je to Haxagon, zkuste skript pustit znovu za 10 sekund (může jít o rate-limit).`);
    } catch (e) {
        console.error(`\n[!] Chyba: ${e.message}`);
    }
}

async function submit(url, password, algo, offset) {
    console.log(`\n\n[***] SHODA NALEZENA! [***]`);
    console.log(`[+] Algoritmus: ${algo}`);
    console.log(`[+] Offset:     ${offset}ms`);
    console.log(`[+] Heslo:      ${password}`);

    const solRes = await fetch(`${url}/solution`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ password })
    });
    console.log(`[!] Výsledek odeslání: ${await solRes.text()}`);
    process.exit(0);
}

crack();