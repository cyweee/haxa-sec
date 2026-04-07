import cv2
import numpy as np

video_path = 'pixelated.mp4'
cap = cv2.VideoCapture(video_path)

# Читаем первый кадр и делаем его "холстом"
ret, first_frame = cap.read()
if not ret:
    print("Ошибка чтения видео")
    exit()

min_frame = cv2.cvtColor(first_frame, cv2.COLOR_BGR2GRAY)

print("Прогоняем видео сквозь сито...")

while True:
    ret, frame = cap.read()
    if not ret:
        break

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # АБСОЛЮТНАЯ МАГИЯ: мы просто берем и попиксельно сравниваем текущий кадр
    # с нашим "холстом". Если пиксель на новом кадре темнее - перезаписываем.
    min_frame = np.minimum(min_frame, gray)

cap.release()

# Сохраняем сырой результат как есть
cv2.imwrite('flag_raw.png', min_frame)

# Делаем копию с жестким контрастом для лучшей читаемости
_, contrast_frame = cv2.threshold(min_frame, 150, 255, cv2.THRESH_BINARY)
cv2.imwrite('flag_contrast.png', contrast_frame)

print("Готово. Открывай flag_contrast.png.")