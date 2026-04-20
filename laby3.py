#!/usr/bin/env python3
"""
Labyrint 3 - OPTIMALIZOVANÁ verze
HLAVNÍ OPTIMALIZACE: Multi-target BFS - místo N*(N-1) BFS běhů jen N běhů.
Z každého waypoint spustíme jeden BFS a najdeme cesty ke VŠEM ostatním.
"""

import requests
from collections import deque
from heapq import heappush, heappop
import sys
import time

BASE_URL = "http://63.179.238.181:8080"
SESSION = requests.Session()

# ─────────────────────────── Fetch ───────────────────────────

def init_round():
    r = SESSION.get(f"{BASE_URL}/init", timeout=10)
    print(f"[INIT] {r.status_code}: {r.text.strip()}")

def get_maze() -> str:
    r = SESSION.get(BASE_URL, timeout=10)
    ct = r.headers.get('Content-Type', '')
    if 'json' in ct or r.text.strip().startswith('{'):
        try:
            data = r.json()
            for key in ('maze', 'labyrint', 'map', 'grid', 'data'):
                if key in data:
                    return data[key]
        except Exception:
            pass
    return r.text

def add_answer(path: str) -> str:
    r = SESSION.post(f"{BASE_URL}/add", json={"answer": path}, timeout=15)
    return r.text

def flush() -> str:
    r = SESSION.get(f"{BASE_URL}/flush", timeout=15)
    return r.text

# ─────────────────────────── Parse ───────────────────────────

def parse_maze(text: str):
    lines = text.strip().splitlines()
    rows = len(lines)
    cols = max(len(row) for row in lines)
    grid = [row.ljust(cols) for row in lines]

    flags = []
    for r, row in enumerate(grid):
        for c, ch in enumerate(row):
            if ch == 'f':
                flags.append((r, c))

    # Start: first odd-row, odd-col non-# cell
    start = None
    for r in range(1, rows, 2):
        for c in range(1, cols, 2):
            if grid[r][c] != '#':
                start = (r, c)
                break
        if start:
            break

    # End: last odd-row, odd-col non-# cell
    end = None
    for r in range(rows - 2, 0, -2):
        for c in range(cols - 2, 0, -2):
            if grid[r][c] != '#':
                end = (r, c)
                break
        if end:
            break

    # Fallback
    if start is None:
        for r in range(rows):
            for c in range(cols):
                if grid[r][c] != '#':
                    start = (r, c); break
            if start: break
    if end is None:
        for r in range(rows-1,-1,-1):
            for c in range(cols-1,-1,-1):
                if grid[r][c] != '#':
                    end = (r, c); break
            if end: break

    return grid, rows, cols, start, end, flags

# ─────────────────────────── OPTIMIZED BFS ─────────────────────
# Multi-target: run ONE BFS from src, find ALL targets at once.

DIRS = [(-2, 0, 'U'), (2, 0, 'D'), (0, 2, 'R'), (0, -2, 'L')]

def bfs_multi(grid, rows, cols, src, targets):
    """
    BFS from src on logical grid (step=2, check wall).
    Returns dict: target_pos -> path_string
    Only stops when all targets found or exhausted.
    """
    if not targets:
        return {}

    target_set = set(targets)
    found = {}

    # parent[(r,c)] = (parent_pos, direction)
    parent = {src: (None, None)}
    queue = deque([src])

    while queue:
        r, c = queue.popleft()

        for dr, dc, d in DIRS:
            nr, nc = r + dr, c + dc
            wr, wc = r + dr // 2, c + dc // 2

            if not (0 <= nr < rows and 0 <= nc < cols):
                continue
            if (nr, nc) in parent:
                continue
            if grid[wr][wc] == '#' or grid[nr][nc] == '#':
                continue

            parent[(nr, nc)] = ((r, c), d)

            if (nr, nc) in target_set:
                # Reconstruct path
                path = []
                cur = (nr, nc)
                while parent[cur][0] is not None:
                    p, direction = parent[cur]
                    path.append(direction)
                    cur = p
                path.reverse()
                found[(nr, nc)] = ''.join(path)

                if len(found) == len(target_set):
                    return found

            queue.append((nr, nc))

    return found

# ──────────────────────── TSP bitmask DP ─────────────────────

def solve_tsp(waypoints, dist_matrix, path_matrix):
    n_flags = len(waypoints) - 2
    end_idx = len(waypoints) - 1

    if n_flags == 0:
        d = dist_matrix[0][end_idx]
        if d is None:
            return None
        return d, path_matrix[0][end_idx]

    full_mask = (1 << n_flags) - 1
    dp = {}
    seen = {}
    best = {}
    pq = []

    for fi in range(n_flags):
        flag_node = fi + 1
        d = dist_matrix[0][flag_node]
        if d is not None:
            mask = 1 << fi
            state = (flag_node, mask)
            if state not in seen or seen[state] > d:
                seen[state] = d
                dp[state] = (d, 0, 0, path_matrix[0][flag_node])
                heappush(pq, (d, flag_node, mask))

    result_cost = None
    result_path = None

    while pq:
        cost, node, mask = heappop(pq)
        state = (node, mask)
        if state in best and best[state] <= cost:
            continue
        best[state] = cost

        if mask == full_mask:
            d = dist_matrix[node][end_idx]
            if d is not None:
                total = cost + d
                if result_cost is None or total < result_cost:
                    result_cost = total
                    result_path = _reconstruct(dp, node, mask, end_idx, path_matrix)
            continue

        for fi in range(n_flags):
            if not (mask >> fi & 1):
                next_node = fi + 1
                d = dist_matrix[node][next_node]
                if d is not None:
                    new_cost = cost + d
                    new_mask = mask | (1 << fi)
                    new_state = (next_node, new_mask)
                    if new_state not in seen or seen[new_state] > new_cost:
                        seen[new_state] = new_cost
                        dp[new_state] = (new_cost, node, mask, path_matrix[node][next_node])
                        heappush(pq, (new_cost, next_node, new_mask))

    if result_cost is None:
        return None
    return result_cost, result_path


def _reconstruct(dp, last_node, last_mask, end_idx, path_matrix):
    segments = [path_matrix[last_node][end_idx]]
    node, mask = last_node, last_mask
    while node != 0:
        _cost, prev_node, prev_mask, seg = dp[(node, mask)]
        segments.append(seg)
        node, mask = prev_node, prev_mask
    segments.reverse()
    return ''.join(segments)

# ──────────────────────── Main solver ────────────────────────

def solve(maze_text: str):
    grid, rows, cols, start, end, flags = parse_maze(maze_text)

    if start is None or end is None:
        return None

    waypoints = [start] + flags + [end]
    N = len(waypoints)
    n_flags = len(flags)

    # Initialize matrices
    dist_matrix = [[None] * N for _ in range(N)]
    path_matrix = [[''] * N for _ in range(N)]
    for i in range(N):
        dist_matrix[i][i] = 0

    # OPTIMIZED: N BFS runs (one per waypoint as source)
    # instead of N*(N-1) pairwise runs
    for i, src in enumerate(waypoints):
        targets = [waypoints[j] for j in range(N) if j != i]
        results = bfs_multi(grid, rows, cols, src, targets)
        for j, dst in enumerate(waypoints):
            if j != i and dst in results:
                p = results[dst]
                dist_matrix[i][j] = len(p)
                path_matrix[i][j] = p

    result = solve_tsp(waypoints, dist_matrix, path_matrix)
    if result is None:
        return None

    total_cost, full_path = result
    return full_path, total_cost, n_flags, rows, cols

# ─────────────────────────── Entry ───────────────────────────

def main():
    print("=" * 60)
    print("  Labyrint 3 Solver - FAST multi-target BFS + TSP")
    print("=" * 60)

    try:
        init_round()
        session_start = time.time()

        maze_num = 0
        MAX_MAZES = 500

        while maze_num < MAX_MAZES:
            maze_num += 1
            t0 = time.time()

            maze_text = get_maze()

            # Detect flag/solved in maze response
            if 'haxagon' in maze_text.lower():
                print(f"\n🎉 VLAJKA: {maze_text.strip()}")
                break
            if maze_text.strip().startswith('solved'):
                print(f"\n🎉 SOLVED: {maze_text.strip()}")
                break

            # Detect timeout/error
            if 'too slow' in maze_text.lower() or 'reset' in maze_text.lower():
                print(f"[TIMEOUT] {maze_text.strip()[:80]}")
                print("[INFO] Server timeout - starting new session...")
                init_round()
                continue

            result = solve(maze_text)

            if result is None:
                print(f"  #{maze_num}: No solution found!")
                continue

            full_path, total_cost, n_flags, rows, cols = result
            t_solve = time.time() - t0

            # Submit
            add_resp = add_answer(full_path)
            flush_resp = flush()

            t_total = time.time() - t0
            elapsed = time.time() - session_start

            # One-line status
            status = "✓" if add_resp.strip() == 'ok' else "?"
            print(f"  #{maze_num:3d} {rows}x{cols} f={n_flags} len={total_cost:5d} "
                  f"t={t_solve:.2f}s tot={t_total:.2f}s sess={elapsed:.0f}s "
                  f"add={add_resp.strip()[:8]} flush={flush_resp.strip()[:30]}")

            # Check for flag in responses
            for resp in [add_resp, flush_resp]:
                if 'haxagon' in resp.lower():
                    print(f"\n🎉 VLAJKA: {resp.strip()}")
                    return
                if resp.strip().startswith('solved'):
                    print(f"\n🎉 SOLVED: {resp.strip()}")
                    return

            # If timeout detected
            if 'too slow' in flush_resp.lower() or 'too slow' in add_resp.lower():
                print("[INFO] Timeout detected, resetting...")
                init_round()
                maze_num = 0

    except requests.exceptions.ConnectionError:
        print("[ERROR] Cannot connect.")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n[STOP]")
    except Exception as e:
        import traceback
        print(f"[ERROR] {e}")
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()