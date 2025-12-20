import requests

# Скачиваем лабиринт
resp = requests.get("http://51.21.245.89:8080")
text = resp.text

print("--- НАБОР СИМВОЛОВ ---")
# Выводим список всех уникальных символов, которые есть в лабиринте
print(set(text))

print("\n--- RAW TEXT (REPR) ---")
# Выводим текст в "сыром" виде, чтобы увидеть \n, \t и прочее
print(repr(text))

print("\n--- ОБЫЧНЫЙ ВИД ---")
print(text)