# Lab 05 — The switchboard: containers that can't talk

From **Docker Doctor, Episode 5** on the [Systems and Signals](https://www.youtube.com/@systemsandsignals) YouTube channel. Try the lab first, then watch the episode.

The lab has two parts. Part 1 uses plain `docker run`. Part 2 is a small Compose project.

## Part 1: two containers, side by side

Build the lab's image, and start `records`, a small app that answers on port 8000:

```bash
docker build -t switchboard-app ./app
docker run -d --name records -e NAME=records switchboard-app
```

Now a second container, `reception`, calls `records` by its name:

```bash
docker run --rm --name reception switchboard-app wget -qO- records:8000
```

Then call it by its number instead. The first command prints the number:

```bash
docker exec records hostname -i
docker run --rm --name reception switchboard-app wget -qO- RECORDS-ADDRESS:8000
```

(Type the number you got in place of `RECORDS-ADDRESS`.)

So is the number the answer? Try this, and read carefully who answers:

```bash
docker stop records
docker run -d --name pharmacy -e NAME=pharmacy switchboard-app
docker start records
docker run --rm --name reception switchboard-app wget -qO- RECORDS-ADDRESS:8000
```

If nobody answers at all, your computer handed out the numbers in a different order. Either way, the old number no longer reaches `records`.

**Your mission for Part 1:** make `reception` reach `records` **by name**. You may create things, but don't rebuild the image. This shows where a container looks names up:

```bash
docker exec records cat /etc/resolv.conf
```

Then clean up Part 1, because Part 2 uses the same names:

```bash
docker rm -f records pharmacy
```

(If you created a network in Part 1, remove it too: `docker network rm NETWORK-NAME`.)

## Part 2: the switchboard

`compose.yaml` starts the clinic's switchboard. `reception` calls three departments and shows what each call returned.

| Service | What it does | Who calls it |
|---|---|---|
| `reception` | Calls every department and shows the answers on a board | You, at http://localhost:8080 |
| `records` | Patient records | `reception`, at `RECORDS_URL` |
| `pharmacy` | The pharmacy | `reception`, at `PHARMACY_URL`. You can also open it at http://localhost:8082 |
| `billing` | Billing, kept on its own network | `reception`, at `BILLING_URL` |

### Start it

```bash
docker compose up -d
curl localhost:8080
```

All four containers are `Up`. All three calls fail.

### Your mission

1. Read the board. The three failures show two **different** errors. What does each kind of error tell you?
2. For each call, find the cause from **inside** `reception`.
3. Fix all three, so the board says `open` three times. You only need to change `compose.yaml`. After each change, run `docker compose up -d reception`, then `curl localhost:8080` again.
4. Billing was meant to be private. When you're done, prove that `records` and `pharmacy` still **can't** reach `billing`.
5. Bonus: open a second terminal in this folder, and run the app on your own computer (it needs Python 3):
   ```bash
   NAME="your Mac" python3 app/app.py
   ```
   Now make `reception` reach it. (`localhost` won't work. Why not?) Stop it with Ctrl+C when you're done.

### The chart to fill in

| Call | What the board says | The cause | The fix |
|---|---|---|---|
| `records` | | | |
| `pharmacy` | | | |
| `billing` | | | |

### Tools you'll need

```bash
docker compose exec reception cat /etc/resolv.conf
docker compose exec reception getent hosts records
docker compose exec reception wget -qO- pharmacy:8000
docker compose ps pharmacy --format "table {{.Service}}\t{{.Ports}}"
docker compose ps billing --format "table {{.Service}}\t{{.Status}}"
docker ps --filter name=switchboard --format "table {{.Names}}\t{{.Networks}}"
docker network ls
```

`getent hosts NAME` asks for a name's address the same way your app does. If it prints nothing, the name is unknown.

## Hints (open one at a time)

<details>
<summary>Hint 1</summary>

To call by name, a container needs something that turns names into addresses. Compare the `nameserver` line in `/etc/resolv.conf` on the default network and on a network you create with `docker network create`.
</details>

<details>
<summary>Hint 2</summary>

`Name does not resolve` means nobody could turn the name into an address. `Connection refused` means the name worked: the call reached an address, and nothing was listening on that port.
</details>

<details>
<summary>Hint 3</summary>

Inside a container, `localhost` means that same container. Which container is calling?
</details>

<details>
<summary>Hint 4</summary>

In `"8082:8000"`, the left number is a door on your computer. Containers on the same network call each other directly. Which number is the pharmacy's own port?
</details>

<details>
<summary>Hint 5</summary>

A service with no `networks` line joins the project's `default` network. A service **with** a `networks` line joins only the networks it lists.
</details>

<details>
<summary>Hint 6</summary>

Fixed billing, and broke the other two? Read Hint 5 again, for `reception` this time.
</details>

<details>
<summary>Hint 7 (the bonus)</summary>

Docker Desktop gives your own computer a name that containers can call. On Linux, you add that name yourself, with `extra_hosts` in `compose.yaml`.
</details>

## Clean up

```bash
docker compose down --rmi local
docker rmi switchboard-app
```

The answers are in [SOLUTION.md](SOLUTION.md). Try first!
