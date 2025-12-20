import re
import sys
from PIL import Image, ExifTags


def find_flag_01(filename):
    print(f"--- ЗАПУСК ПОИСКА ФЛАГА 01: {filename} ---")

    try:
        with open(filename, "rb") as f:
            content = f.read()
    except FileNotFoundError:
        print("ОШИБКА: Файл не найден.")
        return

    found = False

    # 1. ГЛУБОКИЙ ПОИСК ПО БАЙТАМ (Regex)
    # Ищет haxagon{...} даже если он в странной кодировке
    print("\n[1] Проверка бинарных строк...")
    patterns = [
        rb'haxagon\{[^}]+\}',  # Стандартный формат
        rb'haxagon',  # Просто слово
    ]

    for p in patterns:
        matches = re.findall(p, content, re.IGNORECASE)
        for m in matches:
            print(f"!!! НАЙДЕНО (Regex): {m.decode('utf-8', errors='ignore')}")
            found = True

    # 2. ПРОВЕРКА ХВОСТА ФАЙЛА (EOF)
    # JPEG заканчивается байтами FF D9. Всё, что после — скрыто.
    print("\n[2] Проверка данных после конца файла (EOF)...")
    eof_marker = b'\xff\xd9'
    last_eof = content.rfind(eof_marker)

    if last_eof != -1 and last_eof + 2 < len(content):
        hidden_data = content[last_eof + 2:]
        print(f"[*] Найдены скрытые данные после изображения ({len(hidden_data)} байт)!")
        print(f"[*] Содержимое (raw): {hidden_data[:100]}...")  # Показываем первые 100 байт

        # Пробуем найти текст в хвосте
        try:
            text = hidden_data.decode('utf-8', errors='ignore').strip()
            if "haxagon" in text or "flag" in text:
                print(f"!!! НАЙДЕНО В ХВОСТЕ: {text}")
                found = True
        except:
            pass
    else:
        print("[-] Лишних данных в конце файла нет.")

    # 3. ПРОВЕРКА МЕТАДАННЫХ (EXIF)
    print("\n[3] Проверка скрытых комментариев в EXIF...")
    try:
        img = Image.open(filename)
        exif = img._getexif()
        if exif:
            for tag_id, value in exif.items():
                tag = ExifTags.TAGS.get(tag_id, tag_id)
                # Ищем в комментариях
                if tag in ['UserComment', 'ImageDescription', 'XPComment']:
                    print(f"[*] {tag}: {value}")
                    if isinstance(value, bytes):
                        val_str = value.decode(errors='ignore')
                    else:
                        val_str = str(value)

                    if "haxagon" in val_str:
                        print(f"!!! НАЙДЕНО В МЕТАДАННЫХ: {val_str}")
                        found = True
        else:
            print("[-] EXIF данные отсутствуют.")
    except Exception as e:
        print(f"[-] Ошибка чтения EXIF: {e}")

    print("\n------------------------------------------------")
    if not found:
        print("ИТОГ: Скрипт не нашел флаг в открытом виде.")
        print("ВАЖНО: Это значит, что флаг зашифрован внутри пикселей.")
        print("РЕШЕНИЕ: Тебе 100% нужен инструмент 'steghide'.")
        print("ЕСЛИ НЕ СТАВИТСЯ НА ПК -> Иди на сайт: aperisolve.com")
    else:
        print("УСПЕХ: Проверь найденные строки выше.")


if __name__ == "__main__":
    find_flag_01("crocodile.jpg")