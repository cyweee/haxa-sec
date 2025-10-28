import websocket
import json
import time


# -------------------------------------------------------------------
# 1. ČÁST: RYCHLÝ ŘEŠITEL SUDOKU (neměnit)
# -------------------------------------------------------------------

def solve_sudoku(board):
    find = find_empty(board)
    if not find:
        return True
    else:
        row, col = find

    for num in range(1, 10):
        if is_valid(board, num, (row, col)):
            board[row][col] = num
            if solve_sudoku(board):
                return True
            board[row][col] = 0
    return False


def is_valid(board, num, pos):
    row, col = pos
    for i in range(9):
        if board[row][i] == num and col != i:
            return False
    for i in range(9):
        if board[i][col] == num and row != i:
            return False
    box_x = col // 3
    box_y = row // 3
    for i in range(box_y * 3, box_y * 3 + 3):
        for j in range(box_x * 3, box_x * 3 + 3):
            if board[i][j] == num and (i, j) != pos:
                return False
    return True


def find_empty(board):
    for i in range(9):
        for j in range(9):
            if board[i][j] == 0:
                return (i, j)
    return None


# -------------------------------------------------------------------
# 2. ČÁST: WEBSOCKET BOT (zde doplňte názvy klíčů)
# -------------------------------------------------------------------

def on_message(ws, message):
    """Spustí se při přijetí zprávy."""
    print(f"<<< Přijata zpráva: {message[:150]}...")  # Vypíše jen prvních 150 znaků

    try:
        data = json.loads(message)

        # ▼▼▼ ZMĚŇTE TENTO KLÍČ ▼▼▼
        # Jak se jmenuje klíč, ve kterém server posílá sudoku?
        # (Zjistěte z F12 -> Network -> WS -> Messages)
        PUZZLE_KEY_FROM_SERVER = 'puzzle'  # MŮJ ODHAD, doplňte správný

        if PUZZLE_KEY_FROM_SERVER in data:
            print("Nalezeno nové sudoku! Řeším...")
            board = data[PUZZLE_KEY_FROM_SERVER]

            # TODO: Zkontrolujte formát 'board'.
            # Tento řešitel očekává 2D pole (seznam seznamů), např.:
            # [[9, 7, 4, 0, ...], [6, 0, 3, 0, ...], ...]
            # Pokud server posílá string "9740...6030...",
            # musíte ho nejprve převést na 2D pole.

            # 2. Vyřešit
            start_time = time.time()
            if solve_sudoku(board):
                end_time = time.time()
                print(f"+++ Sudoku vyřešeno za {end_time - start_time:.6f} sekund.")

                # 3. Připravit odpověď
                # ▼▼▼ ZMĚŇTE TENTO FORMÁT (PAYLOAD) ▼▼▼
                # V jakém formátu server očekává řešení?
                # (Zjistěte z F12, když odešlete řešení ručně)
                SOLUTION_KEY_TO_SERVER = 'solution'  # MŮJ ODHAD, doplňte správný
                payload = {
                    SOLUTION_KEY_TO_SERVER: board
                    # Možná je potřeba poslat i něco dalšího?
                    # "type": "submit"
                }

                # 4. Odeslat
                ws.send(json.dumps(payload))
                print(f">>> Řešení odesláno.")

            else:
                print("!!! Chyba: Toto sudoku nelze vyřešit.")

        # Zkontrolovat, jestli nepřišla vlajka
        if 'flag' in message.lower():
            print(f"\n\n\n🎉🎉🎉 MÁME VLAJKU: {message}\n\n\n")
            ws.close()

    except Exception as e:
        print(f"Chyba při zpracování zprávy: {e}")


def on_error(ws, error):
    print(f"### Chyba: {error} ###")


def on_close(ws, close_status_code, close_msg):
    print("### Spojení uzavřeno ###")


def on_open(ws):
    print("=== Spojení otevřeno ===")
    # Možná je potřeba po připojení poslat "pozdrav"?
    # Např. {"action": "join", "name": "bot"}
    # Pokud ne, nechte funkci prázdnou.
    # ws.send(json.dumps({"action": "register", "name": "MujBot"}))


if __name__ == "__main__":
    # URL, kterou jste našel:
    WEBSOCKET_URL = "ws://13.48.127.137:8088/"

    print(f"Připojuji se k {WEBSOCKET_URL}...")
#    websocket.enableTrace(True)  # Dejte True pro VELMI detailní logování
    ws = websocket.WebSocketApp(WEBSOCKET_URL,
                                on_open=on_open,
                                on_message=on_message,
                                on_error=on_error,
                                on_close=on_close)

    # Spustí bota (a poběží, dokud ho neukončíte nebo nenajde vlajku)
    ws.run_forever()