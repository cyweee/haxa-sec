import subprocess
import os

# Словарь для перевода USB HID кодов в символы (US клавиатура)
HID_KEY_MAP = {
    0x04: 'a', 0x05: 'b', 0x06: 'c', 0x07: 'd', 0x08: 'e', 0x09: 'f',
    0x0A: 'g', 0x0B: 'h', 0x0C: 'i', 0x0D: 'j', 0x0E: 'k', 0x0F: 'l',
    0x10: 'm', 0x11: 'n', 0x12: 'o', 0x13: 'p', 0x14: 'q', 0x15: 'r',
    0x16: 's', 0x17: 't', 0x18: 'u', 0x19: 'v', 0x1A: 'w', 0x1B: 'x',
    0x1C: 'y', 0x1D: 'z',
    0x1E: '1', 0x1F: '2', 0x20: '3', 0x21: '4', 0x22: '5', 0x23: '6',
    0x24: '7', 0x25: '8', 0x26: '9', 0x27: '0',
    0x2D: '-', 0x2E: '=', 0x2F: '[', 0x30: ']', 0x31: '\\', 0x32: '#',
    0x33: ';', 0x34: '\'', 0x35: '`', 0x36: ',', 0x37: '.', 0x38: '/',
    0x28: '\n', 0x2A: '[BACK]', 0x2B: '\t', 0x2C: ' '
}


def analyze_via_tshark(file_path):
    print(f"[*] Запускаем tshark для файла: {file_path}...")

    if not os.path.exists(file_path):
        print(f"[-] Ошибка: файл {file_path} не найден!")
        return

    # Запрашиваем сразу три самых частых поля, где могут лежать байты клавиатуры
    cmd = [
        "tshark", "-r", file_path,
        "-T", "fields",
        "-e", "usbhid.data",
        "-e", "usb.capdata",
        "-e", "usb.data_fragment"
    ]

    try:
        # Выполняем команду и получаем вывод
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        lines = result.stdout.strip().split('\n')
    except subprocess.CalledProcessError as e:
        print("[-] Ошибка выполнения tshark. Убедись, что Wireshark/tshark установлен.")
        print("Подробности:", e.stderr)
        return

    extracted_text = ""

    for line in lines:
        # Убираем табы (если tshark вернул несколько полей) и двоеточия
        data = line.replace('\t', '').replace(':', '').strip()

        # Пакет клавиатуры должен быть не менее 8 байт (16 hex-символов)
        if not data or len(data) < 16:
            continue

        try:
            modifier = int(data[0:2], 16)  # Первый байт
            keycode = int(data[4:6], 16)  # Третий байт

            if keycode > 0 and keycode in HID_KEY_MAP:
                char = HID_KEY_MAP[keycode]

                # Обработка Shift (0x02 - левый, 0x20 - правый)
                if modifier == 0x02 or modifier == 0x20:
                    if char == '[':
                        char = '{'
                    elif char == ']':
                        char = '}'
                    elif char == '9':
                        char = '('
                    elif char == '0':
                        char = ')'
                    elif char == '-':
                        char = '_'
                    else:
                        char = char.upper()

                extracted_text += char
        except ValueError:
            continue

    if not extracted_text:
        print("[-] Данные не найдены. Возможно, файл имеет нестандартную структуру.")
        return

    # Убираем дубликаты (залипания клавиш)
    clean_text = ""
    for i in range(len(extracted_text)):
        if i == 0 or extracted_text[i] != extracted_text[i - 1]:
            clean_text += extracted_text[i]

    print("[+] Расшифрованный текст (сырой):", extracted_text)
    print("[+] Расшифрованный текст (очищенный):", clean_text)


if __name__ == "__main__":
    # Укажи точный путь к pcap-файлу
    pcap_file = "/home/cywe/PycharmProjects/haxagon-sec/keylogger_keys(2).pcap"
    analyze_via_tshark(pcap_file)