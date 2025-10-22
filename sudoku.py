import requests

def is_valid(board, row, col, num):
    # check row
    for x in range(9):
        if board[row][x] == num:
            return False
    # check column
    for x in range(9):
        if board[x][col] == num:
            return False
    # check 3x3 box
    start_row, start_col = 3 * (row // 3), 3 * (col // 3)
    for i in range(3):
        for j in range(3):
            if board[i + start_row][j + start_col] == num:
                return False
    return True


def solve_sudoku(board):
    for i in range(9):
        for j in range(9):
            if board[i][j] == 0:
                for num in range(1, 10):
                    if is_valid(board, i, j, num):
                        board[i][j] = num
                        if solve_sudoku(board):
                            return True
                        board[i][j] = 0
                return False
    return True


def format_board_to_string(board):
    return "".join(str(num) for row in board for num in row)


def parse_string_to_board(s):
    board = []
    for i in range(9):
        row_list = []
        for j in range(9):
            char = s[i * 9 + j]
            row_list.append(int(char) if char != '.' else 0)
        board.append(row_list)
    return board


unsolved_puzzles_str = """(long list omitted for brevity)"""

URL = "http://13.53.192.3:8080"
HEADERS = {"content-type": "text/plain"}

unsolved_puzzles = unsolved_puzzles_str.strip().split('\n')
solved_payloads = []

print(f"[*] Found {len(unsolved_puzzles)} lines, filtering and solving...")

valid_puzzles = 0
for puzzle_str in unsolved_puzzles:
    clean_str = puzzle_str.strip()

    if len(clean_str) == 81 and all(c in '123456789.' for c in clean_str):
        valid_puzzles += 1
        board = parse_string_to_board(clean_str)
        if solve_sudoku(board):
            solved_string = format_board_to_string(board)
            solved_payloads.append(solved_string)
        else:
            print(f"[!] Error: could not solve sudoku: {clean_str}")
            exit()
    else:
        print(f"[*] Ignoring invalid line: '{clean_str}' (len: {len(clean_str)})")

print(f"[*] Solved {len(solved_payloads)} out of {valid_puzzles} valid puzzles.")

final_payload = "\n".join(solved_payloads)

print("[*] Sending final solution to server...")

try:
    response = requests.post(URL, data=final_payload, headers=HEADERS)
    print("\n--- SERVER RESPONSE ---")
    print(response.text)
    print("------------------------")

except requests.exceptions.ConnectionError:
    print(f"\n[!] CONNECTION ERROR: can't reach {URL}. Check VPN or network.")
except Exception as e:
    print(f"Unexpected error: {e}")
