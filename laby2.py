import requests
import sys
from collections import deque

# Konfigurace URL
BASE_URL = "http://51.20.138.74:8080"

# Mapování znaků na otevřené směry (U=Up, D=Down, L=Left, R=Right)
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
    # (delta_row, delta_col, direction_name)
    potential_moves = [(-1, 0, 'U'), (1, 0, 'D'), (0, -1, 'L'), (0, 1, 'R')]

    for dr, dc, d_name in potential_moves:
        if d_name in allowed_dirs:
            nr, nc = r + dr, c + dc
            if 0 <= nr < rows and 0 <= nc < cols:
                neighbor_char = grid[nr][nc]
                # Kontrola reciprocity (pokud jdu doprava, soused musí mít díru vlevo)
                if neighbor_char in CHAR_OPENINGS:
                    neighbor_dirs = CHAR_OPENINGS[neighbor_char]
                    opposites = {'U': 'D', 'D': 'U', 'L': 'R', 'R': 'L'}
                    if opposites[d_name] in neighbor_dirs:
                        valid_moves.append((nr, nc, d_name))
    return valid_moves


def solve_maze(maze_text):
    try:
        grid = parse_maze(maze_text)
    except Exception:
        return None

    rows = len(grid)
    cols = len(grid[0])
    start = (0, 0)
    end = (rows - 1, cols - 1)

    queue = deque([(start, "")])
    visited = {start}

    while queue:
        (curr_r, curr_c), path = queue.popleft()

        if (curr_r, curr_c) == end:
            return path

        current_char = grid[curr_r][curr_c]

        for nr, nc, direction in get_neighbors(curr_r, curr_c, current_char, grid):
            if (nr, nc) not in visited:
                visited.add((nr, nc))
                queue.append(((nr, nc), path + direction))

    return None


def main():
    # Použití Session pro zrychlení (Keep-Alive)
    s = requests.Session()

    print("--- Resetuji hru (/init) ---")
    s.get(f"{BASE_URL}/init")

    level = 1

    while True:
        try:
            # Stáhneme labyrint
            response = s.get(BASE_URL)
            content = response.text

            # Kontrola stavů
            if "too slow" in content:
                print("\n!!! MOC POMALU - Restartuji hru !!!")
                s.get(f"{BASE_URL}/init")
                level = 1
                continue

            if "solved" in content or "hexagon" in content:
                print("\n\n" + "#" * 30)
                print("VLAJKA NALEZENA:")
                print(content)
                print("#" * 30)
                break

            # Jen pro info vypíšeme první řádek labyrintu, ať nezahlcujeme konzoli
            first_line = content.split('\n')[0] if content else "???"
            print(f"Level {level} | Labyrint: {first_line}...")

            # Řešení
            path = solve_maze(content)

            if not path:
                print("CHYBA: Nepodařilo se najít cestu (nebo parsování selhalo).")
                print("Obsah:", content)
                break

            # Odeslání (používáme stejnou session 's')
            post_response = s.post(
                BASE_URL,
                json={"answer": path},
                headers={"Content-Type": "application/json"}
            )

            if post_response.status_code != 200:
                print(f"Chyba serveru: {post_response.status_code}")
            else:
                level += 1

        except KeyboardInterrupt:
            print("\nUkončeno uživatelem.")
            break
        except Exception as e:
            print(f"Chyba: {e}")
            break


if __name__ == "__main__":
    main()