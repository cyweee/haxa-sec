import requests
import sys

BASE_URL = 'http://16.16.255.254:8080'
sys.setrecursionlimit(5000)


def solve_board(board):
    rows = len(board)
    cols = len(board[0])
    covered = [[False] * cols for _ in range(rows)]
    solution = []
    used_dominoes = set()

    def get_domino_tuple(n1, n2):
        return tuple(sorted((n1, n2)))

    def get_moves(r, c):
        moves = []
        for dr, dc in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
            nr, nc = r + dr, c + dc
            if 0 <= nr < rows and 0 <= nc < cols and not covered[nr][nc]:
                dom = get_domino_tuple(board[r][c], board[nr][nc])
                if dom not in used_dominoes:
                    moves.append((nr, nc, dom))
        return moves

    def backtrack():
        best_r, best_c = -1, -1
        best_moves = None
        min_len = 5  # Maximum sousedů je 4
        found_uncovered = False
        for r in range(rows):
            for c in range(cols):
                if not covered[r][c]:
                    found_uncovered = True
                    moves = get_moves(r, c)

                    if len(moves) == 0:
                        return False

                    if len(moves) < min_len:
                        min_len = len(moves)
                        best_r, best_c = r, c
                        best_moves = moves

                    if min_len == 1:
                        break
            if min_len == 1: break
        if not found_uncovered:
            return True

        r, c = best_r, best_c
        for nr, nc, dom in best_moves:
            # Proveď tah
            covered[r][c] = covered[nr][nc] = True
            used_dominoes.add(dom)
            solution.append({
                "num1": board[r][c], "num2": board[nr][nc],
                "pos1": {"y": r, "x": c}, "pos2": {"y": nr, "x": nc}
            })

            if backtrack(): return True

            solution.pop()
            used_dominoes.remove(dom)
            covered[r][c] = covered[nr][nc] = False

        return False

    if backtrack():
        return solution
    return None


def main():
    session = requests.Session()

    while True:
        print(f"[>] Stahuji novou desku...")
        try:
            resp = session.get(BASE_URL, timeout=10)
            if resp.status_code != 200:
                print(f"[!] Chyba při stahování: {resp.status_code}")
                if resp.status_code == 404: break
                continue
            board = resp.json()
        except Exception as e:
            print(f"[!] Konec nebo chyba: {e}")
            break

        solution = solve_board(board)
        if not solution:
            print("[!] Nepodařilo se najít řešení! (zkuste spustit znovu)")
            break
        try:
            post_resp = session.post(BASE_URL, json=solution, allow_redirects=False, timeout=10)

            if post_resp.status_code == 200 and "ok" in post_resp.text:
                sys.stdout.write('.')
                sys.stdout.flush()
                continue
            elif post_resp.status_code == 307:
                flag_loc = post_resp.headers.get('Location')
                print(f"\n[!] HOTOVO! Přesměrování na: {flag_loc}")
                if flag_loc.startswith('/'):
                    flag_url = BASE_URL + flag_loc
                else:
                    flag_url = flag_loc

                flag_resp = session.get(flag_url)
                print(f"\n>>> VLAJKA: {flag_resp.text} <<<\n")
                break
            else:
                print(f"\n[X] Chyba odeslání: {post_resp.status_code} - {post_resp.text}")
                break
        except Exception as e:
            print(f"\n[X] Chyba spojení: {e}")
            break

# Redirecting to /flag
if __name__ == "__main__":
    main()