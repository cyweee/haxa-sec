import pyshark

# Словарь для перевода USB HID кодов в символы (US клавиатура)
# Содержит буквы, цифры и основные спецсимволы
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


def analyze_usb_pcap(file_path):
    print(f"[*] Анализируем файл: {file_path}...")

    # Открываем pcap файл и фильтруем только пакеты, содержащие данные USB (usb.capdata)
    cap = pyshark.FileCapture(file_path, display_filter='usb.capdata')
    extracted_text = ""

    for packet in cap:
        try:
            # Получаем сырые данные (обычно строка вида "00:00:2f:00:00:00:00:00")
            capdata = packet.usb.capdata
            bytes_list = capdata.split(':')

            # Пакет клавиатуры USB HID состоит из 8 байт
            if len(bytes_list) == 8:
                modifier = int(bytes_list[0], 16)  # 1-й байт: модификаторы (Shift, Ctrl и т.д.)
                keycode = int(bytes_list[2], 16)  # 3-й байт: код самой нажатой клавиши

                # Игнорируем пакеты отпускания клавиши (когда keycode == 0)
                if keycode > 0 and keycode in HID_KEY_MAP:
                    char = HID_KEY_MAP[keycode]

                    # Логика обработки зажатого Shift (0x02 - Left Shift, 0x20 - Right Shift)
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
        except AttributeError:
            # Пропускаем пакеты, у которых нет нужных атрибутов
            continue

    cap.close()

    # Очистка вывода от дубликатов (в USB часто отправляется несколько одинаковых
    # пакетов при удержании клавиши). Это простая очистка, в зависимости от дампа
    # может потребоваться более сложная фильтрация.
    clean_text = ""
    for i in range(len(extracted_text)):
        if i == 0 or extracted_text[i] != extracted_text[i - 1]:
            clean_text += extracted_text[i]

    print("[+] Расшифрованный текст (сырой):", extracted_text)
    print("[+] Расшифрованный текст (очищенный от залипаний):", clean_text)


if __name__ == "__main__":
    # Укажи правильный путь к своему файлу
    analyze_usb_pcap('keylogger_keys(2).pcap')