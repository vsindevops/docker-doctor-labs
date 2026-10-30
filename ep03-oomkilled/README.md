# Lab 03 — Out of memory: three patients, one killer

From **Docker Doctor, Episode 3** on the [Systems and Signals](https://www.youtube.com/@systemsandsignals) YouTube channel. Try the lab first, then watch the episode.

## The patients

| Patient | What it does | The symptom |
|---|---|---|
| `report` | Builds the monthly report, then exits | Works on a laptop with a 128 MB limit, and dies on a server with the same limit |
| `sessions` | Remembers every visitor | You double its memory, and it still dies |
| `web` | The clinic's website | `docker ps` says `Up`, but the report page fails |

Nothing here can hurt your machine: every command below sets a memory limit, so only the lab's own container can run out of memory.

## Build them

```bash
docker compose build
```

## Your mission

### Patient 1: `report`

Open a second terminal window and start the security camera. Leave it running:

```bash
docker events --filter container=report --format '{{.Action}}'
```

Back in the first window, start the report with a 64 MB limit, and watch its memory:

```bash
docker run -d --name report --memory 64m ward-report
docker stats --format "table {{.Name}}\t{{.MemUsage}}\t{{.MemPerc}}" report
```

Press **Ctrl+C** in both windows when the numbers drop to zero. Now answer these:

1. The bar reached about 100%. Did the report die right then? How far did it get? (`docker logs --tail 3 report`)
2. What did Docker really write down for the limit?
   ```bash
   docker inspect --format 'Memory={{.HostConfig.Memory}}  MemorySwap={{.HostConfig.MemorySwap}}' report
   ```
3. Run `docker rm report`. Does the report finish with a 256 MB limit (`docker run --rm --memory 256m ward-report`)? Now make your machine act like a server with no swap, using one more flag. Does it still finish?
4. How much memory does the report really need? (Look for the file `memory.peak` in `/sys/fs/cgroup` inside the container.)
5. Set a limit that's right. Then change `report/report.py` so it needs far less, and make it pass with the first limit: 64 MB, no swap.

### Patient 2: `sessions`

Run it three times, with 64, 128 and 256 MB, and no swap. Each run stops by itself.

```bash
docker run --rm --memory 64m --memory-swap 64m ward-sessions
```

1. How long does it live each time? What's the pattern?
2. Why will more memory never fix this one?
3. Fix `sessions/sessions.py`, so its memory line goes flat. Prove it with `docker stats`.

### Patient 3: `web`

```bash
docker run -d --name web --memory 64m --memory-swap 64m -p 8080:8000 ward-web
```

Give it a second to start. (Too soon, and `curl` says `Connection reset by peer`. That only means the app isn't ready yet.) Then:

```bash
curl localhost:8080
curl localhost:8080/report
curl localhost:8080
```

1. Run `docker ps`, `docker stats` and `docker logs` for `web`. Which of them shows you the problem?
2. Run the ward round from Episode 2. What's strange about the answer?
   ```bash
   docker inspect --format '{{.Name}}  exit={{.State.ExitCode}}  oom={{.State.OOMKilled}}' web
   ```
3. Hit the report page a few more times. How many kills has the kernel counted?
   ```bash
   docker exec web grep oom_kill /sys/fs/cgroup/memory.events
   ```
4. Run `docker restart web`, then repeat questions 2 and 3. What happened to the evidence?

## The chart to fill in

| Patient | Limit | How far did it get? | `OOMKilled` | What it really needs | The right fix |
|---|---|---|---|---|---|
| `report` | 64 MB | | | | |
| `report` | 64 MB, no swap | | | | |
| `report` | 128 MB, no swap | | | | |
| `sessions` | 64 MB, no swap | | | | |
| `sessions` | 128 MB, no swap | | | | |
| `sessions` | 256 MB, no swap | | | | |
| `web` | 64 MB, no swap | | | | |

Your numbers can be a little different from the video. The pattern will be the same.

## Hints (open one at a time)

<details>
<summary>Hint 1</summary>

`--memory 64m` isn't the whole story. If you don't set `--memory-swap`, the container can also use as much swap as `--memory`, if the machine has swap. Docker Desktop has swap. Many servers don't.
</details>

<details>
<summary>Hint 2</summary>

`docker stats` only shows right now. The kernel remembers the worst moment. Let the report finish with plenty of room, then read the file:

`sh -c 'python /report.py; cat /sys/fs/cgroup/memory.peak'`
</details>

<details>
<summary>Hint 3</summary>

`report` only needs one number: the total. Does it need to keep every visit in memory to work that out?
</details>

<details>
<summary>Hint 4</summary>

`sessions` keeps every session forever. What if it only kept the last 50? Look up `collections.deque` and its `maxlen`.
</details>

<details>
<summary>Hint 5 (almost the answer)</summary>

A container only stops when its **main program** stops. `web` gives every request its own worker process. What happens to the container if the kernel kills a worker?
</details>

## Clean up

```bash
docker rm -f report sessions web
docker rmi ward-report ward-sessions ward-web
```

The answers are in [SOLUTION.md](SOLUTION.md). Try first!
