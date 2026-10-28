# Lab 02 — The waiting room: eight patients, eight exit codes

From **Docker Doctor, Episode 2** on the [Systems and Signals](https://www.youtube.com/@systemsandsignals) YouTube channel. Try the lab first, then watch the episode.

## The patients

`compose.yaml` starts eight small services, the kind every company runs: an API, a worker, billing, a database migration, a file parser, a monthly report, a cache and a queue. Each one stops (or doesn't) in a different way.

## Start them

```bash
docker compose up -d
```

Compose prints **one** error. There is more than one problem.

## Your mission

Fill in this chart for every patient:

| Service | Status | Exit code | What happened? | The fix |
|---|---|---|---|---|
| api | | | | |
| worker | | | | |
| billing | | | | |
| migrate | | | | |
| parser | | | | |
| report | | | | |
| cache | | | | |
| queue | | | | |

Then:

1. Stop `cache` with `docker kill clinic-cache-1`, and stop `queue` with `docker compose stop queue`. What codes do you get now, and why are they different?
2. `report` and `cache` can end up with the **same** exit code. How do you tell which one ran out of memory?

## Tools you'll need

```bash
docker compose ps -a --format "table {{.Service}}\t{{.Status}}"
docker inspect --format '{{.Name}}  exit={{.State.ExitCode}}  oom={{.State.OOMKilled}}' $(docker compose ps -aq)
docker inspect --format '{{.State.Error}}' clinic-api-1
docker compose logs billing
kill -l 9
```

## Hints (open one at a time)

<details>
<summary>Hint 1</summary>

`Created` means the container was made but **never started**. `docker inspect --format '{{.State.Error}}'` tells you why.
</details>

<details>
<summary>Hint 2</summary>

Any exit code above 128 means the program was **killed by a signal**. Subtract 128, then run `kill -l <number>` to see which signal.
</details>

<details>
<summary>Hint 3 (almost the answer)</summary>

Two containers can both say 137. Only one of them has `OOMKilled` set to `true`.
</details>

## Clean up

```bash
docker compose down
docker rmi clinic-worker
```

The answers are in [SOLUTION.md](SOLUTION.md). Try first!
