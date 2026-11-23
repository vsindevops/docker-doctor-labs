# Lab 08 — The case file: a build that fails three times

From **Docker Doctor, Episode 8** on the [Systems and Signals](https://www.youtube.com/@systemsandsignals) YouTube channel. Try the lab first, then watch the episode.

## The story

The clinic's appointments service should build into an image called `appointments`, start, and answer on port 8000:

```
appointments: open
```

It doesn't. Build it:

```bash
docker build -t appointments .
```

The build fails, with a wall of text.

## How to read a failed build

Read it like a detective, from the bottom up:

| Clue | Where it is | What it tells you |
|---|---|---|
| **The verdict** | The last line, starting `ERROR: failed to build` | **What** failed |
| **The scene** | The line marked `>>>`, in the Dockerfile excerpt | **Which line** of the Dockerfile |
| **The witness** | The box between the two `------` lines | The failing command's **own words** |

## Your mission

1. Make the image build. A build stops at its first error, so fix one, build again, and read the next one.
2. Make it run. Start it in the background, then check it:
   ```bash
   docker run -d --name appointments -p 8000:8000 appointments
   docker logs appointments
   curl localhost:8000
   ```
   If something's wrong, `docker logs appointments` tells you. Remove the container with `docker rm -f appointments` before you try again.
3. The rules: keep `.dockerignore` (it keeps the image small), and keep `curl` (the next episode's health check needs it).
4. Bonus: build it the way CI does, from an empty cache, and check which processor the image is for:
   ```bash
   docker build --no-cache -t appointments .
   docker image inspect appointments --format '{{.Os}}/{{.Architecture}}'
   ```

## The chart to fill in

| Case | The verdict | The scene | The witness | The cause | The fix |
|---|---|---|---|---|---|
| 1 | | | | | |
| 2 | | | | | |
| 3 (it builds, but won't run) | | | | | |

## Tools you'll need

```bash
ls -a
cat .dockerignore
docker build --progress=plain -t appointments .
docker run --rm python:3.12-slim apt-get install -y curl
xxd start.sh | head -1
```

`--progress=plain` prints every line of every step, the way CI logs do. The `docker run` line runs a failing step by hand, in the same base image the Dockerfile starts from. `xxd` shows a file's raw bytes, including ones your editor never shows you.

## Hints (open one at a time)

<details>
<summary>Hint 1</summary>

In the last line, skip the long code with `::` in the middle (yours will look different). Read the words at the end.
</details>

<details>
<summary>Hint 2</summary>

`ls` shows the file, but Docker doesn't read your folder. It reads the **build context**: the files your folder sends it. One file in this folder decides what gets sent. `ls -a` shows it.
</details>

<details>
<summary>Hint 3</summary>

In `.dockerignore`, `*` leaves everything out, and a line starting with `!` lets one file back in.
</details>

<details>
<summary>Hint 4</summary>

`exit code: 100` only says the command failed. Its reason is in the witness box. Then run the same command by hand, in the same base image: does it fail the same way? What does the image need before it can install anything?
</details>

<details>
<summary>Hint 5</summary>

`exec format error`: the kernel didn't recognise the file it was told to run. A script must start with `#!`, as its very first two bytes. Look at the raw bytes with `xxd`.
</details>

<details>
<summary>Hint 6</summary>

`tail -c +4 FILE` prints a file from its fourth byte on, leaving out the first three.
</details>

## Clean up

```bash
docker rm -f appointments
docker rmi appointments
```

The answers are in [SOLUTION.md](SOLUTION.md). Try first!
