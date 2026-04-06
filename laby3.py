import requests
import collections
import time
import sys
import logging
import json
from typing import List, Tuple, Dict, Optional, Set

# ==============================================================================
# КОНФИГУРАЦИЯ И ЛОГИРОВАНИЕ
# ==============================================================================
BASE_URL = "http://13.53.127.0:8080"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) MazeSolver/4.0 (Advanced-CTF)",
    "Content-Type": "application/json"
}
DIRS = [(-1, 0, 'U'), (1, 0, 'D'), (0, -1, 'L'), (0, 1, 'R')]

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("LabyrinthGodMode")


# ==============================================================================
# МОДУЛЬ СЕТЕВОГО ВЗАИМОДЕЙСТВИЯ
# ==============================================================================
class LabyrinthClient:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update(HEADERS)

    def reset_game(self):
        logger.info("Выполняю полную реинициализацию сессии (/init)...")
        try:
            self.session.get(f"{self.base_url}/init").raise_for_status()
            return True
        except Exception as e:
            logger.error(f"Критическая ошибка сети: {e}")
            return False

    def get_raw_maze(self) -> Tuple[Optional[str], Optional[str]]:
        try:
            r = self.session.get(self.base_url)
            r.raise_for_status()
            if "haxagon{" in r.text:
                return None, r.text
            return r.text, None
        except Exception as e:
            logger.error(f"Ошибка получения данных: {e}")
            return None, None

    def submit_payload(self, path: str) -> str:
        """Многоуровневая отправка решения."""
        logger.info(f"Транспортировка пути длиной {len(path)}...")
        try:
            # Стандарт Labyrinth 3: порционная отправка в /add
            chunk_size = 500
            for i in range(0, len(path), chunk_size):
                chunk = path[i:i + chunk_size]
                self.session.post(f"{self.base_url}/add", json={"answer": chunk})

            # Финализация через /flush
            time.sleep(0.1)
            resp = self.session.get(f"{BASE_URL}/flush")
            return resp.text
        except Exception as e:
            return f"Network Error: {e}"


# ==============================================================================
# АНАЛИЗАТОР ГЕОМЕТРИИ (DEAD-END FILLING & INSPECTION)
# ==============================================================================
class MazeProcessor:
    def __init__(self, raw_maze: str):
        self.raw = raw_maze
        self.grid: List[str] = []
        self.height = 0
        self.width = 0
        self._prepare_grid()

    def _prepare_grid(self):
        lines = self.raw.splitlines()
        maze_lines = [l for l in lines if '#' in l]
        if not maze_lines:
            return
        self.width = max(len(l) for l in maze_lines)
        self.grid = [l.ljust(self.width, ' ') for l in maze_lines]
        self.height = len(self.grid)

    def get_hex_map(self):
        """Инспекция невидимых байтов для обнаружения триггеров."""
        for r in range(self.height):
            hex_row = " ".join([f"{ord(c):02x}" for c in self.grid[r]])
            logger.debug(f"Row {r:02d} HEX: {hex_row}")

    def find_all_walkable(self) -> List[Tuple[int, int]]:
        return [(r, c) for r in range(self.height) for c in range(self.width) if self.grid[r][c] != '#']

    def find_special_triggers(self) -> Dict[Tuple[int, int], int]:
        """Обнаружение любых аномалий в ASCII/Unicode."""
        triggers = {}
        idx = 0
        for r in range(self.height):
            for c in range(self.width):
                char = self.grid[r][c]
                # Все, что не стена и не обычный пробел (32) — это важная точка
                if char != '#' and ord(char) != 32:
                    triggers[(r, c)] = idx
                    idx += 1
                    logger.info(f"Обнаружен триггер: '{char}' (0x{ord(char):02x}) на [{r},{c}]")
        return triggers


# ==============================================================================
# ДВИЖОК ПОИСКА ПУТИ (MULTIPLE ALGORITHMS)
# ==============================================================================
class PathfindingEngine:
    def __init__(self, grid: List[str]):
        self.grid = grid
        self.h = len(grid)
        self.w = len(grid[0])

    def solve_best_path(self, start: Tuple[int, int], end: Tuple[int, int], flags: Dict) -> Optional[str]:
        """BFS с битовой маской для сбора всех флагов."""
        full_mask = (1 << len(flags)) - 1
        f_map = {pos: i for i, pos in enumerate(flags.keys())}

        start_mask = (1 << f_map[start]) if start in f_map else 0
        queue = collections.deque([(start[0], start[1], start_mask, "")])
        visited = {(start[0], start[1], start_mask)}

        while queue:
            r, c, mask, path = queue.popleft()

            if (r, c) == end and mask == full_mask:
                return path

            for dr, dc, move in DIRS:
                nr, nc = r + dr, c + dc
                if 0 <= nr < self.h and 0 <= nc < self.w and self.grid[nr][nc] != '#':
                    nm = mask | (1 << f_map[(nr, nc)]) if (nr, nc) in f_map else mask
                    state = (nr, nc, nm)
                    if state not in visited:
                        visited.add(state)
                        queue.append((nr, nc, nm, path + move))
        return None


# ==============================================================================
# ГЛАВНЫЙ ОРКЕСТРАТОР
# ==============================================================================
class LabyrinthGodMode:
    def __init__(self):
        self.client = LabyrinthClient(BASE_URL)
        self.level = 1

    def execute(self):
        logger.info("=== ЗАПУСК ЛОГИЧЕСКОГО МОДУЛЯ L3 ===")
        self.client.reset_game()

        while True:
            raw_maze, flag_found = self.client.get_raw_maze()
            if flag_found:
                logger.info(f"ФЛАГ ЗАХВАЧЕН: {flag_found}")
                break

            proc = MazeProcessor(raw_maze)
            if proc.height == 0:
                logger.warning("Пустое поле, перезапуск...")
                self.client.reset_game()
                continue

            # --- ГЕНЕРАЦИЯ СТРАТЕГИЙ ---
            # 1. Поиск Start/End
            walkable = proc.find_all_walkable()
            start = walkable[0]
            corner_end = walkable[-1]  # Правый нижний угол

            # Находим самую дальнюю точку от старта (истинный выход из змейки)
            q = collections.deque([(start, 0)])
            v = {start}
            furthest_node, max_dist = start, 0
            while q:
                curr, d = q.popleft()
                if d > max_dist: max_dist, furthest_node = d, curr
                for dr, dc, _ in DIRS:
                    nr, nc = curr[0] + dr, curr[1] + dc
                    if 0 <= nr < proc.height and 0 <= nc < proc.width and \
                            proc.grid[nr][nc] != '#' and (nr, nc) not in v:
                        v.add((nr, nc))
                        q.append(((nr, nc), d + 1))

            # --- ПЕРЕБОР СТРАТЕГИЙ (BRUTEFORCE STRATEGY) ---
            # Статья говорит: брутфорс - это O(n!), но на 5x5 это доли секунды.
            strategies = [
                # Стратегия А: Только триггеры + выход в углу
                {"end": corner_end, "flags": proc.find_special_triggers(), "name": "Classic Corner"},
                # Стратегия Б: Посетить ВООБЩЕ ВСЁ и выйти в углу
                {"end": corner_end, "flags": {p: i for i, p in enumerate(walkable)}, "name": "Completionist Corner"},
                # Стратегия В: Посетить всё и выйти в самой дальней точке
                {"end": furthest_node, "flags": {p: i for i, p in enumerate(walkable)}, "name": "Completionist Snake"},
            ]

            is_solved = False
            for strat in strategies:
                logger.info(f"Уровень {self.level} | Проверка стратегии: {strat['name']}")
                engine = PathfindingEngine(proc.grid)
                path = engine.solve_best_path(start, strat['end'], strat['flags'])

                if not path: continue

                result = self.client.submit_payload(path)
                logger.info(f"Вердикт сервера: {result.strip()}")

                if "not the best" not in result.lower() and "timeou" not in result.lower():
                    self.level += 1
                    is_solved = True
                    break
                else:
                    logger.warning(f"Стратегия {strat['name']} отвергнута. Сброс сессии...")
                    self.client.reset_game()
                    time.sleep(0.3)

            if not is_solved:
                logger.error("Все стратегии исчерпаны. Анализ HEX-дампа...")
                proc.get_hex_map()
                break


if __name__ == "__main__":
    try:
        LabyrinthGodMode().execute()
    except KeyboardInterrupt:
        print("\nПрервано пользователем.")