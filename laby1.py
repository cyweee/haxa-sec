import requests
import json
from collections import deque

# Новый URL
BASE_URL = "http://13.60.6.11:8080"

# Карта направлений: теперь нужны полные английские слова
DIR_TO_WORD = {
    'U': 'UP',
    'D': 'DOWN',
    'L': 'LEFT',
    'R': 'RIGHT'
}

# Логика проходов (Box Drawing Characters)
# Те же самые символы, что и в прошлом задании
CHAR_OPENINGS = {
    '┌': ['D', 'R'], '┐': ['D', 'L'], '└': ['U', 'R'], '┘': ['U', 'L'],
    '│': ['U', 'D'], '─': ['L', 'R'], '├': ['U', 'D', 'R'], '┤': ['U', 'D', 'L'],
    '┬': ['D', 'L', 'R'], '┴': ['U', 'L', 'R'], '┼': ['U', 'D', 'L', 'R'],
    '╵': ['U'], '╷': ['D'], '╶': ['R'], '╴': ['L'],
    ' ': []
}


def parse_maze(maze_text):
    lines = maze_text.strip().split('\n')
    return [list(line) for line in lines]


def get_neighbors(r, c, char, grid):
    rows = len(grid)
    cols = len(grid[0])
    valid_moves = []

    if char not in CHAR_OPENINGS:
        return []

    allowed_dirs = CHAR_OPENINGS[char]
    # (смещение_ряд, смещение_кол, внутр_код)
    potential_moves = [(-1, 0, 'U'), (1, 0, 'D'), (0, -1, 'L'), (0, 1, 'R')]

    for dr, dc, d_code in potential_moves:
        if d_code in allowed_dirs:
            nr, nc = r + dr, c + dc
            # Проверка границ
            if 0 <= nr < rows and 0 <= nc < cols:
                neighbor_char = grid[nr][nc]
                # Проверка совместимости (если идем ВПРАВО, у соседа должен быть вход СЛЕВА)
                if neighbor_char in CHAR_OPENINGS:
                    neighbor_dirs = CHAR_OPENINGS[neighbor_char]
                    opposites = {'U': 'D', 'D': 'U', 'L': 'R', 'R': 'L'}
                    if opposites[d_code] in neighbor_dirs:
                        valid_moves.append((nr, nc, d_code))
    return valid_moves


def solve_maze(maze_text):
    try:
        grid = parse_maze(maze_text)
    except Exception:
        return None

    rows = len(grid)
    cols = len(grid[0])
    start = (0, 0)
    end = (rows - 1, cols - 1)  # Цель всегда в правом нижнем углу

    # Очередь: (координаты, список_шагов)
    # В прошлом коде была строка "", теперь список []
    queue = deque([(start, [])])
    visited = {start}

    while queue:
        (curr_r, curr_c), path = queue.popleft()

        if (curr_r, curr_c) == end:
            return path

        current_char = grid[curr_r][curr_c]

        for nr, nc, d_code in get_neighbors(curr_r, curr_c, current_char, grid):
            if (nr, nc) not in visited:
                visited.add((nr, nc))
                # Добавляем полное слово (UP, DOWN...) в список
                new_step = DIR_TO_WORD[d_code]
                new_path = path + [new_step]
                queue.append(((nr, nc), new_path))

    return None


def main():
    print(f"--- Подключаюсь к {BASE_URL} ---")

    try:
        # 1. Получаем лабиринт
        response = requests.get(BASE_URL)
        content = response.text

        print("Лабиринт получен (первые строки):")
        print('\n'.join(content.split('\n')[:3]))  # Показать только начало для проверки

        # 2. Решаем
        path_list = solve_maze(content)

        if not path_list:
            print("ОШИБКА: Путь не найден или парсер не узнал символы.")
            print("Весь ответ сервера:\n", content)
            return

        print(f"Путь найден! Количество шагов: {len(path_list)}")
        # Пример вывода: ['RIGHT', 'DOWN', 'DOWN'...]

        # 3. Отправляем ответ
        payload = {"answer": path_list}

        print("Отправляю решение...")
        post_response = requests.post(
            BASE_URL,
            json=payload,
            headers={"Content-Type": "application/json"}
        )

        print(f"Статус ответа: {post_response.status_code}")
        print("Ответ сервера:")
        print(post_response.text)

    except Exception as e:
        print(f"Произошла ошибка: {e}")


if __name__ == "__main__":
    main()