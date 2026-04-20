import struct


def parse_pcap_manually(file_path):
    with open(file_path, 'rb') as f:
        # Читаем глобальный заголовок PCAP (24 байта)
        global_header = f.read(24)
        if len(global_header) < 24:
            print("Файл слишком мал для PCAP")
            return

        # Определяем порядок байтов (Magic number)
        magic = global_header[:4]
        endian = '<' if magic in (b'\xd4\xc3\xb2\xa1', b'\x4d\x3c\xb2\xa1') else '>'

        count = 0
        last_capacity = None

        print(f"Анализ файла: {file_path}")

        while True:
            # Читаем заголовок пакета (16 байт)
            pkt_header = f.read(16)
            if len(pkt_header) < 16:
                break

            # Извлекаем длину захваченных данных (смещение 8 или 12 в заголовке пакета)
            # Формат заголовка: ts_sec, ts_usec, incl_len, orig_len
            _, _, incl_len, _ = struct.unpack(endian + 'IIII', pkt_header)

            # Читаем данные самого пакета
            packet_data = f.read(incl_len)

            # Ищем сигнатуру внутри пакета
            # AA 05 ... (32 байта данных) ... Емкость ... EE FF
            if b'\xaa\x05' in packet_data:
                start = packet_data.find(b'\xaa\x05')
                # Проверяем, хватает ли длины пакета для чтения емкости (32 байта от AA 05)
                if len(packet_data) >= start + 36:
                    capacity_bytes = packet_data[start + 32: start + 36]
                    # Распаковываем mAh (Little Endian)
                    val = struct.unpack('<I', capacity_bytes)[0]
                    last_capacity = val
                    count += 1

        if last_capacity is not None:
            ah = last_capacity / 1000.0
            print("-" * 30)
            print(f"Обработано пакетов: {count}")
            print(f"Последнее значение: {val} mAh")
            print(f"Результат:          {ah:.1f} Ah")
            print("-" * 30)
            print(f"Влаг: haxagon{{{ah:.1f}}}")
        else:
            print("Данные не найдены. Попробуйте проверить тип устройства.")


if __name__ == "__main__":
    parse_pcap_manually("capture.pcap")