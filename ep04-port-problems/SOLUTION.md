# Lab 04 — Solution

Measured on Docker Desktop for Mac (Docker Engine 29.9.2, Compose 5.6.1, Apple Silicon). On Linux, some `curl` errors read differently, so the inside check is always your proof.

## The path every request takes

Your request goes through three doors: **your computer's port** (8080), then **Docker**, then **the container's port** (8000), where the app waits. The error tells you which door it stopped at:

| What you see | Where it stopped |
|---|---|
| `curl: (7) … Couldn't connect to server` · Chrome: "localhost refused to connect." | Door 1: nothing is listening on your computer's port |
| `curl: (56) … Connection reset by peer` · Chrome: "The connection was reset." | Door 3: Docker answered, but nothing answered inside the container (or the app isn't ready yet: wait a second) |

Chrome shows the same headline for both: "This site can’t be reached". Read the second line, or use `curl`.

## The chart

| Service | What `curl` says | Where it stopped | The cause | The fix |
|---|---|---|---|---|
| `web` | `(56)` reset | Door 3 | The app listens on `127.0.0.1` only | `HOST: 0.0.0.0` |
| `booking` | `(56)` reset | Door 3 | The mapping sends requests to port 80, and the app listens on 8000 | `"8081:8000"` |
| `records` | `(7)` refused (on 8000) | Door 1 | No ports line: `EXPOSE` doesn't publish | `ports: "8083:8000"` |
| `pharmacy` | The wrong service answers, or it never starts | Door 1 is taken | `xray` copied its ports line: both want 8082 | Give `xray` its own port, like `"8084:8000"`, then recreate the one that lost |
| `xray` | Starts, or doesn't: it's a race | Door 1 is taken | Same as above | Same as above |

## Patient 1: `records`, a door painted on the wall

```bash
docker compose ps records --format "table {{.Service}}\t{{.Status}}\t{{.Ports}}"
grep EXPOSE app/Dockerfile
```

The PORTS column says `8000/tcp`, with no arrow. A published port has an arrow, like `0.0.0.0:8080->8000/tcp`. The `8000/tcp` comes from `EXPOSE 8000` in the Dockerfile, and Docker's docs are clear: "The `EXPOSE` instruction doesn't actually publish the port." It's a note for people.

**The fix:** give it a ports line in `compose.yaml`:

```yaml
    ports:
      - "8083:8000"
```

```bash
docker compose up -d records
curl localhost:8083
```

## Patient 2: `booking`, the wrong door inside

The PORTS column says `0.0.0.0:8081->80/tcp`. The arrow is there, so Docker answers on 8081. But the right side, 80, is the port **inside** the container, and the logs say the app listens on 8000:

```bash
docker compose logs booking
```

In a mapping, the left number is yours to choose. The right number must be the port the app really listens on.

**The fix:**

```yaml
      - "8081:8000"
```

```bash
docker compose up -d booking
curl localhost:8081
```

## Patient 3: `web`, the app that only listens to itself

The mapping is right (`8080->8000`), and the app listens on 8000. But its log says:

```bash
docker compose logs web
```

`web: listening on http://127.0.0.1:8000`. Look inside:

```bash
docker compose exec web wget -qO- 127.0.0.1:8000
docker compose exec web hostname -i
docker compose exec web wget -qO- CONTAINER-ADDRESS:8000
docker compose exec web netstat -tln
```

On `127.0.0.1` the app answers. On the container's own network address, the one `hostname -i` prints, it's refused. And `netstat` shows only `127.0.0.1:8000`.

`127.0.0.1` means "only me", and inside a container, "me" is the container itself. Docker's request arrives on the container's network address, where nothing is listening. So the app never hears it.

**The fix:** listen on `0.0.0.0`, which means every address the container has. In `compose.yaml`, add this line under `NAME: web`:

```yaml
      HOST: 0.0.0.0
```

```bash
docker compose up -d web
curl localhost:8080
docker compose exec web netstat -tln
```

You'll meet this with real tools. Flask's `app.run()` defaults to `127.0.0.1`, Django's `runserver` runs on `127.0.0.1:8000`, and Vite's dev server defaults to `localhost`. Inside a container, start them on `0.0.0.0` (for example `flask run --host 0.0.0.0`, `python manage.py runserver 0.0.0.0:8000`, or `vite --host`).

(Use `127.0.0.1` in the inside check, not `localhost`. In this image, `localhost` can mean the IPv6 address `::1` first, and the app only listens on the IPv4 one.)

## Patient 4: `pharmacy` and `xray`, two services and one port

Both services ask for port 8082, because someone copied the pharmacy's ports line into `xray`. Compose starts them at the same time, and whichever is first gets the port. The other one stays `Created`, and Compose prints:

`Bind for 0.0.0.0:8082 failed: port is already allocated`

It's a race, so it can go either way. In the video, `xray` won, so `curl localhost:8082` answered `xray is open`: the wrong service answered the pharmacy's door. To see who has a port:

```bash
docker ps --filter publish=8082 --format "table {{.Names}}\t{{.Ports}}"
```

**On a Mac, try port 5000.** It's Flask's default port, so it's the first one many people pick. Change `xray`'s ports line to this:

```yaml
      - "5000:8000"
```

```bash
docker compose up -d xray
lsof -nP -iTCP:5000 -sTCP:LISTEN
```

A different error: `ports are not available: … bind: address already in use`. `lsof` shows `ControlCe`: Control Center, which runs AirPlay Receiver. macOS listens on ports 5000 and 7000. (On Linux, 5000 is usually free.)

| The words | Who has the port | How to find them |
|---|---|---|
| `port is already allocated` | Another **container** | `docker ps --filter publish=PORT` |
| `address already in use` | Another **program on your computer** | `lsof -nP -iTCP:PORT -sTCP:LISTEN` |

**The fix:** give `xray` a free port:

```yaml
      - "8084:8000"
```

```bash
docker compose up -d xray
curl localhost:8084
```

Then start the pharmacy again, and look closely:

```bash
docker compose up -d pharmacy
curl localhost:8082
docker compose ps pharmacy --format "table {{.Service}}\t{{.Status}}\t{{.Ports}}"
```

It's `Up`, `curl` is refused, and the PORTS column says only `8000/tcp`: no arrow. **A container that lost the race for a port never gets that port**, even though the port is free now. `docker start`, `docker restart` and `docker compose restart` don't fix it. `docker inspect` still lists the port under `PortBindings`, but nothing is published. Make a fresh container:

```bash
docker compose up -d --force-recreate pharmacy
curl localhost:8082
```

Now the PORTS column has its arrow, and `pharmacy is open`. (If `xray` lost the race on your machine, you can skip this: changing its ports line already makes Compose build a fresh `xray` container.) This was measured on Docker Engine 29.9.2.

## Too easy to reach

Everything opens now. But look at who can open it:

```bash
lsof -nP -iTCP:8080 -sTCP:LISTEN
ipconfig getifaddr en0
curl WIFI-ADDRESS:8080
```

`*:8080` means every network your computer is on. Your own Wi-Fi address opens the website, so anyone else on that Wi-Fi can try too, unless a firewall stops them. Docker's docs say it plainly: "Publishing container ports is insecure by default." On a Linux server it's worse: Docker's docs warn that published ports skip ufw's rules, "effectively ignoring your firewall configuration".

**The fix, when only you need it:** put `127.0.0.1` on the left of the mapping:

```yaml
      - "127.0.0.1:8080:8000"
```

```bash
docker compose up -d web
lsof -nP -iTCP:8080 -sTCP:LISTEN
curl WIFI-ADDRESS:8080
curl localhost:8080
```

Now `lsof` shows `127.0.0.1:8080`, the Wi-Fi address is refused, and `localhost` still works.

So this lab has **two** `0.0.0.0`s. Inside the container, the app needs it. On your computer, you may not want it.

## Next episode

The second line in `netstat`, `127.0.0.11`, is Docker's own DNS:

```bash
docker compose exec web cat /etc/resolv.conf
```

Episode 5 is about containers that can't find each other, and it starts right there.

## The interview answer

> "The container is running, but the app won't open in the browser. What do you check?"

I read the error to see where the request stopped. I check the ports column: is there an arrow, and does the right side match the port the app listens on? Then I look inside the container: does the app answer on its own network address, or only on 127.0.0.1? And if the container won't start, I find who holds the port: `docker ps --filter publish` for another container, or `lsof` for another program.
