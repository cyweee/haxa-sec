import requests
from collections import deque
from itertools import permutations

BASE_URL = "http://51.21.245.89:8080"

DIRS = {
    'u': (-1, 0),
    'd': (1, 0),
    'l': (0, -1),
    'r': (0, 1),
}


# ---------- BFS с восстановлением пути ----------
def bfs(maze, start):
    h, w = len(maze), len(maze[0])
    q = deque([start])
    visited = {start: None}

    while q:
        x, y = q.popleft()
        for d, (dx, dy) in DIRS.items():
            nx, ny = x + dx, y + dy
            if (
                0 <= nx < h and
                0 <= ny < w and
                maze[nx][ny] != '#' and
                (nx, ny) not in visited
            ):
                visited[(nx, ny)] = (x, y, d)
                q.append((nx, ny))
    return visited


def reconstruct(visited, start, end):
    if end not in visited:
        return None

    path = []
    cur = end

    while cur != start:
        prev = visited.get(cur)
        if prev is None:
            return None
        px, py, d = prev   # ← ВАЖНЫЙ ФИКС
        path.append(d)
        cur = (px, py)

    return ''.join(reversed(path))


# ---------- HTTP ----------
s = requests.Session()

print("[*] Init")
s.get(f"{BASE_URL}/init")

print("[*] Get maze")
raw = s.get(BASE_URL).text

# Проверка, что это реально лабиринт
if '#' not in raw:
    print("[-] Server did not return maze:")
    print(raw)
    exit(1)

maze_text = raw.splitlines()
maze = [list(row) for row in maze_text]

H, W = len(maze), len(maze[0])


# ---------- Поиск старта и конца ----------
start = None
end = None

for i in range(H):
    for j in range(W):
        if maze[i][j] != '#':
            start = (i, j)
            break
    if start:
        break

for i in range(H - 1, -1, -1):
    for j in range(W - 1, -1, -1):
        if maze[i][j] != '#':
            end = (i, j)
            break
    if end:
        break

if not start or not end:
    raise RuntimeError("Start or end not found")


# ---------- Флаги ----------
flags = []
for i in range(H):
    for j in range(W):
        if maze[i][j] == 'f':
            flags.append((i, j))

print(f"[*] Flags found: {len(flags)}")

if not flags:
    print("[-] No flags found, maze:")
    print("\n".join("".join(r) for r in maze))
    exit(1)

points = [start] + flags + [end]


# ---------- Все пути между важными точками ----------
paths = {}
lengths = {}

for p in points:
    visited = bfs(maze, p)
    for q in points:
        path = reconstruct(visited, p, q)
        if path is None:
            raise RuntimeError(f"No path between {p} and {q}")
        paths[(p, q)] = path
        lengths[(p, q)] = len(path)


# ---------- Перебор порядка флагов ----------
best_len = 10**18
best_order = None

for perm in permutations(flags):
    order = [start] + list(perm) + [end]
    total = sum(
        lengths[(order[i], order[i + 1])]
        for i in range(len(order) - 1)
    )
    if total < best_len:
        best_len = total
        best_order = order

print("[*] Best length:", best_len)


# ---------- Склейка полного пути ----------
answer = ""
for i in range(len(best_order) - 1):
    answer += paths[(best_order[i], best_order[i + 1])]

print("[*] Sending answer, length:", len(answer))


# ---------- Отправка ----------
s.post(BASE_URL, json={"answer": answer})
resp = s.get(f"{BASE_URL}/flush")
print(resp.text)
