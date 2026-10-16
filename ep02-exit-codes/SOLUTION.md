# Lab 02 — Solution

## The chart

| Service | Status | Exit code | What happened? | The fix |
|---|---|---|---|---|
| api | `Created` | **127** | The command has a typo: `pyhton`. Docker couldn't find a program with that name, so the container never started. | Fix the command: `python` |
| worker | `Created` | **126** | `start.sh` exists, but it isn't allowed to run (no execute permission). The container never started. | In the Dockerfile: `COPY --chmod=755 start.sh /start.sh` |
| billing | `Exited (1)` | **1** | The app hit an error and stopped itself. The logs say why: `RuntimeError: payment service is not reachable`. | Fix what the logs say |
| migrate | `Exited (0)` | **0** | **Nothing is wrong.** A one-time job is supposed to finish, and 0 means "done, all good". | Nothing |
| parser | `Exited (139)` | **139** | 139 = 128 + 11, and signal 11 is `SEGV`: the program touched memory it wasn't allowed to, and crashed so hard it couldn't print anything. | Update or rebuild the buggy library |
| report | `Exited (137)` | **137** | 137 = 128 + 9, and signal 9 is `KILL`. `OOMKilled` is `true`: it used more memory than its 64 MB limit, so it was killed. | Use less memory, or give it a realistic limit (Episode 3) |
| cache | `Up` | 0 (still running) | Healthy, until you kill it. | — |
| queue | `Up` | 0 (still running) | Healthy, until you stop it. | — |

## The two stops

```bash
docker kill clinic-cache-1
docker compose stop queue
```

- `cache` → **137**, with `OOMKilled` `false`. `docker kill` sends signal 9, KILL: no warning, no goodbye.
- `queue` → **143** = 128 + 15, TERM. `docker compose stop` asks politely first, and `queue` listened. 143 is the good kind of stop.

## Same number, different killer

`report` and `cache` both say **137**. Only `report` has `OOMKilled=true`. Before you give a container more memory, **check `OOMKilled`**: if it's `false`, memory wasn't the problem. Something else killed it: a person, a deploy, or a stop that took too long.

## The decoder

| Code | Meaning |
|---|---|
| 0 | Finished, all good |
| 1 (and other small numbers) | The app stopped itself because of an error. Read the logs. |
| 125 | Docker itself refused (for example a wrong flag). No container was made. |
| 126 | The program was found, but it isn't allowed to run |
| 127 | The program wasn't found (typo, or not installed in the image) |
| 128 + N | Killed by signal N. Look it up with `kill -l N`. |
| 130 | 128 + 2, INT: Ctrl+C |
| 137 | 128 + 9, KILL: `docker kill`, a stop that took too long, or out of memory (check `OOMKilled`) |
| 139 | 128 + 11, SEGV: crashed while touching memory it shouldn't |
| 143 | 128 + 15, TERM: asked to stop, and it did |

## The boss level

```bash
docker run --rm python:3.12-alpine python -c "import sys; sys.exit(256)"
echo $?
```

It prints **0**. Exit codes only go from 0 to 255, so 256 wraps around to 0, and an error turns into "success". Never use a count (like "number of failed tests") as an exit code. Exit with 1 for any failure.

## The interview answers

> "What does exit code 137 mean?"

137 is 128 + 9, so the process was killed with signal 9, SIGKILL. That happens when it runs out of memory, when someone runs `docker kill`, or when it doesn't stop in time after `docker stop`. I check `docker inspect` for `OOMKilled`: `true` means memory, `false` means something else killed it.

> "What's the difference between exit code 126 and 127?"

127 means the command wasn't found at all, like a typo or a tool that isn't installed in the image. 126 means it was found but couldn't run, usually because the file isn't executable. In Docker, both leave the container in `Created`, because it never started.
