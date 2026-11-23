# Lab 08 — Solution

Measured on Docker Desktop for Mac (Docker Engine 29.9.3, Buildx 0.38.1, Apple Silicon).

In the terminal blocks below, `$` marks a command, and `⋮` marks output left out (build progress, for example).

## The detective's three clues

Read a failed build from the bottom up:

| Clue | Where it is | What it tells you |
|---|---|---|
| **The verdict** | The last line: `ERROR: failed to build: failed to solve: …` | **What** failed |
| **The scene** | The `>>>` line in the Dockerfile excerpt | **Which line** of the Dockerfile |
| **The witness** | The box between the two `------` lines | The failing command's **own words** |

A build stops at its first error. Fix that one, build again, and read the next.

## The chart

| Case | The verdict | The scene | The witness | The cause | The fix |
|---|---|---|---|---|---|
| 1 | `"/app.py": not found` | `>>> COPY app.py ./` | (empty) | `.dockerignore` only lets `main.py` and `start.sh` in; the app was renamed to `app.py` | `!app.py` in `.dockerignore` |
| 2 | `exit code: 100` | `>>> RUN apt-get install -y curl` | `E: Unable to locate package curl` | The slim image has no package lists until `apt-get update` | `apt-get update && apt-get install …` in one `RUN` |
| 3 | `exec /app/start.sh: exec format error` (at run time) | `ENTRYPOINT ["/app/start.sh"]` | `xxd`: `efbb bf` before `#!` | Three invisible bytes, a byte order mark, before `#!` | Remove the first three bytes |

## Case 1: the file that's right there

```
$ docker build -t appointments .
⋮
 => CACHED [3/5] RUN apt-get install -y curl                                                   0.0s
 => ERROR [4/5] COPY app.py ./                                                                 0.0s
------
 > [4/5] COPY app.py ./:
------
Dockerfile:5
--------------------
   3 |     # curl, for the health check
   4 |     RUN apt-get install -y curl
   5 | >>> COPY app.py ./
   6 |     COPY --chmod=755 start.sh ./
   7 |     ENTRYPOINT ["/app/start.sh"]
--------------------
ERROR: failed to build: failed to solve: failed to compute cache key: failed to calculate checksum of ref ch0m2qsyv7ea0a8h2zcui2n8k::f4tadblh4xtx9wtaojy6mgab5: "/app.py": not found
```

The verdict ends with `"/app.py": not found`. Skip the long code before it. The scene is line 5, `COPY app.py ./`. Step 3, `apt-get`, says `CACHED`. Don't believe it: it never ran. The missing file stopped the build first. (On another run, the same step said `CANCELED`: BuildKit labels the steps it never reached either way.) So don't trust anything above the first error. Case 2 proves it: the moment this step really runs, it fails.

The file is right there:

```
$ ls
Dockerfile  README.md  SOLUTION.md  app.py  start.sh
```

But Docker doesn't read your folder. It reads the **build context**, the files your folder sends it, and `.dockerignore` decides what's sent. Docker's docs: "If this file exists, the files and directories that match patterns in the files are removed from the build context before it's sent to the builder."

```
$ cat .dockerignore
# send Docker only what the image needs
*
!main.py
!start.sh
```

`*` leaves everything out, and each `!` line lets one file back in. Docker's docs: "You can prepend lines with a `!` (exclamation mark) to make exceptions to exclusions." Someone renamed `main.py` to `app.py` and updated the Dockerfile, but not `.dockerignore`.

**The fix:** in `.dockerignore`, change `!main.py` to:

```text
!app.py
```

## Case 2: the witness

```
$ docker build --progress=plain -t appointments .
⋮
#7 [3/5] RUN apt-get install -y curl
#7 0.080 Reading package lists...
#7 0.083 Building dependency tree...
#7 0.083 Reading state information...
#7 0.084 E: Unable to locate package curl
#7 ERROR: process "/bin/sh -c apt-get install -y curl" did not complete successfully: exit code: 100
------
 > [3/5] RUN apt-get install -y curl:

0.083 Building dependency tree...
0.083 Reading state information...
0.084 E: Unable to locate package curl
------
Dockerfile:4
⋮
ERROR: failed to build: failed to solve: process "/bin/sh -c apt-get install -y curl" did not complete successfully: exit code: 100
```

The verdict only says the command failed, with `exit code: 100`. That's apt-get's own number for "something went wrong": its manual says "apt-get returns zero on normal operation, decimal 100 on error." The reason is in the witness box: `E: Unable to locate package curl`.

`--progress=plain` prints every line of every step, the way CI logs do. Docker's docs on `--progress`: "Use plain to show container output".

Now run the failing step by hand, in the same base image:

```
$ docker run --rm python:3.12-slim apt-get install -y curl
Reading package lists...
Building dependency tree...
Reading state information...
E: Unable to locate package curl
```

The same error, so it isn't your Dockerfile's fault: it's the image. Slim images ship without the lists of packages that apt-get reads, to stay small. Docker's docs on why: "when you clean up the apt cache by removing `/var/lib/apt/lists` it reduces the image size". `apt-get update` downloads the lists:

```
$ docker run --rm python:3.12-slim sh -c "apt-get update && apt-get install -y curl"
⋮
Setting up curl (8.14.1-2+deb13u7) ...
Processing triggers for libc-bin (2.41-12+deb13u4) ...
```

**The fix:** in the Dockerfile, update and install in **one** `RUN` line, and remove the lists again afterwards:

```dockerfile
RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*
```

Docker's docs: "Always combine `RUN apt-get update` with `apt-get install` in the same `RUN` statement." Two separate `RUN` lines can leave you installing from an old, cached list.

Build again:

```
$ docker build -t appointments .
⋮
```

## Case 3: green, and still dead

The build passes. Run it:

```
$ docker run -d --name appointments -p 8000:8000 appointments
⋮
$ docker logs appointments
exec /app/start.sh: exec format error
$ curl localhost:8000
curl: (7) Failed to connect to localhost port 8000 after 0 ms: Couldn't connect to server
$ docker ps -a --filter name=appointments --format "table {{.Names}}\t{{.Status}}"
NAMES          STATUS
appointments   Exited (255) 1 second ago
```

`docker run -d` prints an ID as if all is well (Episode 1's lesson). The logs say `exec format error`: the kernel looked at the file it was told to run, `/app/start.sh`, and didn't recognise its format. A script must begin with `#!` and the path to its interpreter, as its very first two bytes. The first line looks right:

```
$ head -1 start.sh
#!/bin/sh
```

So look at the raw bytes:

```
$ xxd start.sh | head -1
00000000: efbb bf23 212f 6269 6e2f 7368 0a23 2073  ...#!/bin/sh.# s
```

Before `#!` (`23 21`) come three bytes, `ef bb bf`: a **byte order mark**, an invisible marker some editors put at the start of a file. Your editor and `head` show nothing, but the kernel sees them, so `#!` is no longer first. `file` names it too:

```
$ file start.sh
start.sh: POSIX shell script text executable, Unicode text, UTF-8 (with BOM) text
```

**The fix:** remove the first three bytes, then build and run again:

```
$ tail -c +4 start.sh > start.tmp && mv start.tmp start.sh
$ xxd start.sh | head -1
00000000: 2321 2f62 696e 2f73 680a 2320 7374 6172  #!/bin/sh.# star
$ docker rm -f appointments
appointments
$ docker build -t appointments .
⋮
$ docker run -d --name appointments -p 8000:8000 appointments
⋮
$ docker logs appointments
appointments: listening on port 8000
$ curl localhost:8000
appointments: open
```

(The Dockerfile copies the script with `COPY --chmod=755`, so it doesn't matter that `mv` left the new file without its execute permission on your computer.) In your editor, you can also save the file as "UTF-8" instead of "UTF-8 with BOM".

### The other famous cause: a different processor

```
$ docker image inspect appointments --format '{{.Os}}/{{.Architecture}}'
linux/arm64
```

An image built on an Apple Silicon Mac is for ARM processors. A server with an Intel or AMD processor (`linux/amd64`) can't run its programs, and you get the same `exec format error`. Docker's docs: "Containers share the host kernel, which means that the code that's running inside the container must be compatible with the host's architecture." Build for the server with `--platform`:

```
$ docker build --platform linux/amd64 -t appointments:amd64 .
⋮
$ docker image inspect appointments:amd64 --format '{{.Os}}/{{.Architecture}}'
linux/amd64
```

(Not run here: an `amd64` image failing on an ARM machine. Docker Desktop emulates other processors, so on a Mac both run.)

## Before you blame CI

The build works on your laptop and fails in CI? Ask what CI has that your laptop doesn't, or the other way round:

1. **The cache.** Your laptop reuses old steps. CI often starts empty. Build the way CI does:

   ```bash
   docker build --no-cache -t appointments .
   ```

   Docker's docs on `--no-cache`: "Do not use cache when building the image".
2. **The files.** CI only has what's in git. A file that only lives on your laptop, or one that `.dockerignore` leaves out, breaks the build there.
3. **The processor.** Check the image's platform, as above, and build for the one CI and your servers use.

## Next episode

`curl` is in the image now, for a health check. Episode 9: a container stuck in a restart loop, and a health check that says "unhealthy" while the app works fine.

## The interview answer

> "The build works on your laptop but fails in CI. How do you find out why?"

I read the error from the bottom up. The last line says what failed, the `>>>` arrow shows which line of the Dockerfile, and the box above it has the failing command's own words. Then I reproduce the build the way CI runs it: with no cache, with only the files in git, and for the same processor. If a step still fails, I run it by hand in the base image until I understand it.
