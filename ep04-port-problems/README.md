# Lab 04 — The front desk: five doors, four problems

From **Docker Doctor, Episode 4** on the [Systems and Signals](https://www.youtube.com/@systemsandsignals) YouTube channel. Try the lab first, then watch the episode.

## The patients

`compose.yaml` starts the clinic's front desk: five small services. Every one of them should open in your browser.

| Service | What it does | Where it should open |
|---|---|---|
| `web` | The clinic's website | http://localhost:8080 |
| `booking` | Book an appointment | http://localhost:8081 |
| `records` | Patient records | Nobody wrote it down. The app listens on port 8000. |
| `pharmacy` | The pharmacy | http://localhost:8082 |
| `xray` | X-ray results | Pick a free port |

## Start them

```bash
docker compose up -d
```

Compose prints **one** error. More than one thing is broken. (The error can be about a different service each time you start it. That's a clue.)

## Your mission

1. Knock on every door, and write down exactly what `curl` says. Read the answers carefully: who answered?
   ```bash
   curl localhost:8080
   curl localhost:8081
   curl localhost:8000
   curl localhost:8082
   ```
2. For each one: where did the request stop? On your computer, at Docker, or inside the container?
3. Fix all five, so each one opens. You only need to change `compose.yaml`. After each change, run `docker compose up -d` again.
4. Now make sure **only your own computer** can open them, not everyone on your Wi-Fi.

## The chart to fill in

| Service | What `curl` says | Where it stopped | The cause | The fix |
|---|---|---|---|---|
| `web` | | | | |
| `booking` | | | | |
| `records` | | | | |
| `pharmacy` | | | | |
| `xray` | | | | |

## Tools you'll need

```bash
docker compose ps -a --format "table {{.Service}}\t{{.Status}}\t{{.Ports}}"
docker compose logs web
docker compose exec web wget -qO- 127.0.0.1:8000
docker compose exec web hostname -i
docker compose exec web netstat -tln
docker ps --filter publish=8082 --format "table {{.Names}}\t{{.Ports}}"
lsof -nP -iTCP:8080 -sTCP:LISTEN
```

In the inside check, type `127.0.0.1`, not `localhost`. In this image, `localhost` can mean the IPv6 address `::1` first, and the app only listens on the IPv4 one.

On Linux, `lsof` may need `sudo`, or use `ss -ltnp` instead.

## Hints (open one at a time)

<details>
<summary>Hint 1</summary>

`curl: (7) … Couldn't connect to server` means nothing is listening on that port on your computer. `curl: (56) … Connection reset by peer` means Docker answered, but nothing answered inside the container. (That's on Docker Desktop. On Linux the words can differ, so the inside check is your proof.)
</details>

<details>
<summary>Hint 2</summary>

In the PORTS column, a published port has an arrow: `0.0.0.0:8080->8000/tcp`. A port with no arrow, like `8000/tcp`, isn't published at all.
</details>

<details>
<summary>Hint 3</summary>

In `"8081:80"`, the left number is on your computer and the right number is inside the container. Which port does the app say it listens on? Ask `docker compose logs booking`.
</details>

<details>
<summary>Hint 4</summary>

Read `docker compose logs web` closely. `127.0.0.1` inside a container means "only this container". Docker's request arrives on the container's own network address (`hostname -i`).
</details>

<details>
<summary>Hint 5</summary>

"port is already allocated" means another container has the port. "address already in use" means another program on your computer has it. On a Mac, port 5000 belongs to AirPlay Receiver.

Fixed the clash, but the container that lost still has no arrow? A container that lost the race for a port never gets it back, even after a restart. Make a fresh one: `docker compose up -d --force-recreate SERVICE`.
</details>

<details>
<summary>Hint 6 (almost the answer to step 4)</summary>

Put an address on the left side of the mapping: `"127.0.0.1:8080:8000"`.
</details>

## Clean up

```bash
docker compose down --rmi local
```

The answers are in [SOLUTION.md](SOLUTION.md). Try first!
