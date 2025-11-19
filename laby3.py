import requests
import itertools
import time
import sys
from collections import deque
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# --- KONFIGURACE ---
BASE_URL = "http://13.60.201.119:8080"

# Vytvoříme session s automatickým opakováním při chybě sítě
session = requests.Session()
retry_strategy = Retry(
    total=3,  # Kolikrát zkusit znovu
    backoff_factor=1,  # Čekat 1s, 2s, 4s...
    status_forcelist=[429, 500, 502, 503, 504],  # Kódy chyb serveru, kdy zkusit znovu
)
adapter = HTTPAdapter(max_retries=retry_strategy)
session.mount("http://", adapter)
session.mount("https://", adapter)


def get_maze():
    """Stáhne zadání. Při chybě vrací None."""
    try:
        # Timeout nastaven na 5s, ať nečekáme věčnost
        response = session.get(f"{BASE_URL}", timeout=5)
        return response.text
    except Exception as e:
        # Jen vypíšeme malou tečku jako chybu, ať nespamujeme konzoli
        print(".", end="", flush=True)
        return None


def parse_maze(maze_text):
    if not maze_text: return None, None, None, None

    if "too slow" in maze_text.lower():
        return "TOO_SLOW", None, None, None

    lines = maze_text.strip().split('\n')

    # Ochrana proti HTML chybám (např. 502 Bad Gateway v textu)
    if len(lines) < 3 or not lines[0].startswith("#"):
        return None, None, None, None

    grid = [list(line) for line in lines]
    rows = len(grid)
    cols = len(grid[0])

    flags = []
    start = None
    end = None

    for r in range(rows):
        if len(grid[r]) != cols: continue
        for c in range(cols):
            if grid[r][c] == 'f':
                flags.append((r, c))
            # Hledáme start (pokud není [1][1])
            if start is None and grid[r][c] != '#':
                # Start bývá nahoře vlevo, ale ne nutně [0][0]
                # Pro jistotu bereme první volné místo shora
                pass

    # Specifická logika pro start: [1][1]
    if rows > 1 and cols > 1 and grid[1][1] != '#':
        start = (1, 1)
    else:
        # Fallback start
        for r in range(rows):
            for c in range(cols):
                if grid[r][c] != '#':
                    start = (r, c)
                    break
            if start: break

    end = (rows - 2, cols - 2)
    return grid, start, end, flags


def bfs_path(grid, start, end):
    rows = len(grid)
    cols = len(grid[0])
    queue = deque([(start, "")])
    visited = set([start])
    directions = [(-1, 0, 'U'), (1, 0, 'D'), (0, -1, 'L'), (0, 1, 'R')]

    while queue:
        (r, c), path = queue.popleft()
        if (r, c) == end: return path

        for dr, dc, move in directions:
            nr, nc = r + dr, c + dc
            if 0 <= nr < rows and 0 <= nc < cols:
                if grid[nr][nc] != '#' and (nr, nc) not in visited:
                    visited.add((nr, nc))
                    queue.append(((nr, nc), path + move))
    return None


def solve_maze_logic(maze_text):
    grid, start, end, flags = parse_maze(maze_text)

    if grid == "TOO_SLOW": return "RESTART_NEEDED"
    if grid is None or start is None or end is None: return None

    if not flags: return bfs_path(grid, start, end)

    points = {'start': start, 'end': end}
    for i, f in enumerate(flags): points[f'f{i}'] = f

    path_cache = {}

    def get_segment(p1_key, p2_key):
        if (p1_key, p2_key) in path_cache: return path_cache[(p1_key, p2_key)]
        if p1_key not in points or p2_key not in points: return None
        path = bfs_path(grid, points[p1_key], points[p2_key])
        path_cache[(p1_key, p2_key)] = path
        return path

    flag_keys = [f'f{i}' for i in range(len(flags))]
    best_full_path = None
    min_length = float('inf')

    for perm in itertools.permutations(flag_keys):
        current_path = ""
        possible = True

        # Start -> 1. vlajka
        seg = get_segment('start', perm[0])
        if seg is None: continue
        current_path += seg

        # Vlajka -> Vlajka
        for i in range(len(perm) - 1):
            seg = get_segment(perm[i], perm[i + 1])
            if seg is None:
                possible = False;
                break
            current_path += seg
        if not possible: continue

        # Poslední -> Cíl
        seg = get_segment(perm[-1], 'end')
        if seg is None: continue
        current_path += seg

        if len(current_path) < min_length:
            min_length = len(current_path)
            best_full_path = current_path

    return best_full_path


def initialize_game():
    print("\n>>> RESETUJI HRU (/init) <<<")
    try:
        session.get(f"{BASE_URL}/init", timeout=5)
        return True
    except:
        return False


def main():
    initialize_game()
    round_num = 1
    errors_in_row = 0

    while True:
        try:
            # 1. Získání bludiště
            maze_text = get_maze()

            # Kontrola výhry
            if maze_text and ("haxagon" in maze_text or "solved" in maze_text):
                print("\n\n" + "#" * 50)
                print("🎉 VLAJKA ZÍSKÁNA 🎉")
                print(maze_text)
                print("#" * 50)
                break

                # 2. Řešení
            solution = solve_maze_logic(maze_text)

            if solution == "RESTART_NEEDED":
                print("\nTIMEOUT (Too Slow). Restartuji...")
                initialize_game()
                round_num = 1
                continue

            if not solution:
                # Pokud se nepodařilo stáhnout nebo vyřešit, jen zkusíme znovu
                errors_in_row += 1
                if errors_in_row > 5:
                    print("\nOpakované chyby, zkouším REINIT...")
                    initialize_game()
                    errors_in_row = 0
                time.sleep(0.5)
                continue

            errors_in_row = 0
            print(f"\rKolo {round_num}: Odesílám řešení ({len(solution)} kroků)... ", end="", flush=True)

            # 3. Odeslání - Tady to padalo, teď je to v try/except
            res = session.post(f"{BASE_URL}", json={"answer": solution}, timeout=5)

            if "Wrong" in res.text:
                print("ŠPATNĚ! Restart.")
                initialize_game()
                round_num = 1
            else:
                # Předpokládáme úspěch
                print("OK.", end="")
                round_num += 1

        except KeyboardInterrupt:
            print("\n\nUživatel ukončil program.")
            sys.exit()
        except Exception as e:
            print(f" Chyba sítě ({str(e)[:20]})...", end="")
            # Krátká pauza před dalším pokusem
            time.sleep(1)


if __name__ == "__main__":
    main()