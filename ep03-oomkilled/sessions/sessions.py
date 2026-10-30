"""Remembers every visitor. It never forgets one."""
import time

sessions = []
seconds = 0

while True:
    for _ in range(10):
        sessions.append(b"x" * 500_000)  # one visitor's session: half a megabyte
        time.sleep(0.1)
    seconds += 1
    print(f"up {seconds} seconds, {len(sessions)} sessions in memory", flush=True)
