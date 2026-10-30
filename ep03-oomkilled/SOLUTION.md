# Lab 03 — Solution

Your numbers can be a little different. The pattern is the same. These were measured on Docker Desktop for Mac (Docker Engine 29.9.2, Apple Silicon).

## The chart

| Patient | Limit | How far did it get? | `OOMKilled` | What it really needs | The right fix |
|---|---|---|---|---|---|
| `report` | 64 MB | about 1,200,000 visits | `true` | about 303 MB | Read one visit at a time |
| `report` | 64 MB, no swap | about 600,000 visits | `true` | about 303 MB | Read one visit at a time |
| `report` | 128 MB, no swap | about 1,200,000 visits | `true` | about 303 MB | Read one visit at a time |
| `sessions` | 64 MB, no swap | 12 seconds | `true` | No limit is enough | Keep only the last 50 sessions |
| `sessions` | 128 MB, no swap | 25 seconds | `true` | No limit is enough | Keep only the last 50 sessions |
| `sessions` | 256 MB, no swap | 52 seconds | `true` | No limit is enough | Keep only the last 50 sessions |
| `web` | 64 MB, no swap | The page fails, the container stays `Up` | `true` | about 317 MB for the report page | A limit that fits, or a page that loads less |

## Patient 1: `report`

### The bar was full, and it kept going

`docker stats` reaches about 99.9%, then stays there for several seconds. The logs keep moving. It only dies later, at about twice the distance. Look at the chart above: 64 MB with swap gets as far as 128 MB with no swap.

The reason is what Docker wrote down:

```bash
docker inspect --format 'Memory={{.HostConfig.Memory}}  MemorySwap={{.HostConfig.MemorySwap}}' report
```

```
Memory=67108864  MemorySwap=134217728
```

That's 64 MB and 128 MB. `MemorySwap` is the total of memory plus swap. If you set `--memory` and not `--memory-swap`, the container can use the same amount again as swap, **if the machine has swap**. Swap is a piece of the disk, used as slow memory. `docker stats` doesn't show it, so the bar looks stuck while the real use keeps climbing.

### Works on the laptop, dies on the server

Docker Desktop has swap (`docker run --rm python:3.12-alpine free -m`). So on a laptop, a limit of 256 MB really means 512 MB, and the report fits. Many cloud servers have no swap, and Kubernetes gives containers none by default, so there 256 MB means 256 MB.

Make your machine act like that server by setting `--memory-swap` to the same number as `--memory`:

```bash
docker run --rm --memory 256m --memory-swap 256m ward-report
echo $?
```

It stops at about 2,500,000 visits, and prints **137**. (On a Linux machine with no swap, the report already dies with a plain `--memory 256m`.)

### How much does it really need?

`docker stats` only shows right now. For the worst moment, ask the kernel:

```bash
docker run --rm --memory 1g --memory-swap 1g ward-report sh -c 'python /report.py; cat /sys/fs/cgroup/memory.peak'
```

The last line is about 318,000,000 bytes. Divide by 1024, twice, and you get about **303 MB**. Add about a quarter, and set both flags to that:

```bash
docker run --rm --memory 400m --memory-swap 400m ward-report
```

(`memory.peak` needs cgroup v2 and a fairly recent Linux kernel. Docker Desktop has both. If the file is missing on your Linux machine, watch `docker stats` during the run instead.)

### The better fix: need less memory

The report only wants one number, the total. It doesn't need three million visits in memory to work that out. Replace the last three lines of `report/report.py`:

```python
count = total = 0
for visit in read_visits():
    count += 1
    total += int(visit.split(",")[3])
print(f"report done: {count:,} visits, total fees {total:,}", flush=True)
```

```bash
docker compose build report
docker run --rm --memory 64m --memory-swap 64m ward-report sh -c 'python /report.py; cat /sys/fs/cgroup/memory.peak'
```

The same total, 748,500,000, in the limit that killed it. The peak drops from about 303 MB to about 8 MB.

You'll see this at work as `read()` or `readlines()` on a big file, `fetchall()` on a big query, or loading a whole CSV into a table in memory.

## Patient 2: `sessions`

It lives 12 seconds with 64 MB, 25 with 128 MB, and 52 with 256 MB. Double the memory, and you double the time. **More memory doesn't fix a leak.** It only moves the crash to later. On a real server, that can take days instead of seconds.

The fix is in the code. In `sessions/sessions.py`, add a line under `import time`, and change the `sessions` line:

```python
from collections import deque
```

```python
sessions = deque(maxlen=50)
```

```bash
docker compose build sessions
docker run -d --name sessions --memory 64m --memory-swap 64m ward-sessions
docker stats --format "table {{.Name}}\t{{.MemUsage}}\t{{.MemPerc}}" sessions
```

The line climbs to about 29 MB, then goes flat, and stays alive in the same limit that killed it.

**Read the shape of the line:**

- It climbs and goes flat: it just needs room. Give it what it needs.
- It climbs forever: it's a leak. No limit is big enough.

## Patient 3: `web`

```bash
docker run -d --name web --memory 64m --memory-swap 64m -p 8080:8000 ward-web
```

Give it a second to start. The home page works. The report page says `curl: (52) Empty reply from server`. And then:

| Check | What it says |
|---|---|
| `docker ps` | `Up`. Looks healthy. |
| `docker logs web` | Only the home page requests. The report request isn't there, because the worker died before it could log anything. |
| `docker stats` | About 12 MB, 18%. Looks calm, because it only shows right now. |
| The ward round | `/web  exit=0  oom=true`. Exit 0 and out of memory, on a running container! |
| `memory.events` | `oom_kill 3` after three tries. The kernel counts every kill. |
| `memory.peak` | `67108864`, which is exactly the limit. It hit the ceiling. |
| `docker events --filter event=oom` | One `oom` line for every kill. |

**What happened:** this website gives every request its own worker process. The report page pushed the container over its limit, so the OOM killer killed the biggest program: the worker, not the main one. A container only stops when its **main program** stops, so it stays `Up`, and your users just see errors. Behind nginx, they get `502 Bad Gateway`. Gunicorn, uWSGI, Celery and other apps with workers can all do this.

**A restart wipes the evidence.** After `docker restart web`, `OOMKilled` goes back to `false` and `oom_kill` goes back to 0. Check first, then restart.

**The fix:** give it a limit that fits, or make the page load less:

```bash
docker rm -f web
docker run -d --name web --memory 400m --memory-swap 400m -p 8080:8000 ward-web
```

Give it a second to start, then:

```bash
curl localhost:8080/report
docker exec web grep oom_kill /sys/fs/cgroup/memory.events
```

It prints `report ready, 314,572,800 bytes read`, and `oom_kill 0`.

**In Kubernetes:** on cgroup v2, the kubelet normally has the kernel kill every process in the container together, so you get a restart and a clear `OOMKilled` instead of this quiet kill. In plain Docker, the kill is one process at a time (`memory.oom.group` is 0).

## Prevent it

Set both lines on every service in `compose.yaml`, so your laptop and your server behave the same:

```yaml
services:
  report:     # builds the monthly report, then exits
    build: ./report
    mem_limit: 64m
    memswap_limit: 64m

  sessions:   # remembers every visitor
    build: ./sessions
    mem_limit: 64m
    memswap_limit: 64m

  web:        # the clinic's website
    build: ./web
    mem_limit: 400m
    memswap_limit: 400m
    ports:
      - "8080:8000"
```

And always set a limit. With no limit, `docker stats` shows all of Docker's memory as the limit, and one leak can take down every container next to it.

## The interview answer

> "A container keeps dying with exit code 137, and the logs are empty. What's happening?"

I check `OOMKilled` with `docker inspect`. If it's true, I read `memory.peak` to see what the app really needs, and I set the limit from that, with `--memory-swap` the same as `--memory`, so every machine behaves the same. And if its memory keeps climbing and never goes flat, it's a leak, so I fix the code instead of adding memory.
