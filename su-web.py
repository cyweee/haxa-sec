import asyncio
import websockets
import json

URI = "ws://13.49.221.0:8088"


def is_valid(board, r, c, n):
    for x in range(9):
        if board[r * 9 + x] == n or board[x * 9 + c] == n: return False
    sr, sc = 3 * (r // 3), 3 * (c // 3)
    for i in range(3):
        for j in range(3):
            if board[(sr + i) * 9 + (sc + j)] == n: return False
    return True


def solve(board):
    for i in range(81):
        if board[i] == 0:
            for n in range(1, 10):
                if is_valid(board, i // 9, i % 9, n):
                    board[i] = n
                    if solve(board): return True
                    board[i] = 0
            return False
    return True


async def play_sudoku():
    async with websockets.connect(URI) as websocket:
        print(f"Spojeno se serverem {URI}")

        while True:
            # Příjem zprávy od serveru
            message = await websocket.recv()
            data = json.loads(message)

            msg_type = data.get("type")

            if msg_type == "NEW_BOARD":
                board_str = data.get("board")
                level = data.get("level")
                print(f"Level {level} přijat. Řeším...")

                # Převod stringu na list integerů (tečka = 0)
                board = [int(c) if c.isdigit() else 0 for c in board_str]

                if solve(board):
                    # Odeslání pole 81 čísel jako JSON
                    await websocket.send(json.dumps(board))
                    print(f"Level {level} odeslán!")
                else:
                    print("Sudoku nemá řešení?")

            elif msg_type == "FLAG":
                print("\n" + "!" * 40)
                print("!!! VLAJKA NALEZENA !!!")
                # Vypíšeme celý objekt, abychom viděli přesný název klíče
                print(f"Celá zpráva: {data}")
                # Zkusíme nejčastější klíče
                flag = data.get('flag') or data.get('data') or data.get('message')
                print(f"VLAJKA: {flag}")
                print("!" * 40)
                break

            elif msg_type == "ERROR":
                print(f"Server nahlásil chybu: {data.get('message')}")
            else:
                print(f"Neznámý typ zprávy: {msg_type}")


if __name__ == "__main__":
    asyncio.run(play_sudoku())