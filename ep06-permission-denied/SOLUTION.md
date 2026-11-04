# Lab 06 — Solution

Measured on Docker Desktop for Mac (Docker Engine 29.9.2, Compose 5.6.1, Apple Silicon). The lab's volume is a named volume, which lives inside Docker's own Linux, so it behaves the same on a Linux server.

In the terminal blocks below, `$` marks a command, and `⋮` marks output left out (Compose's build progress, for example).

## The two questions

Every `Permission denied` comes down to two questions:

1. **Who am I?** `id` tells you which user the app runs as.
2. **Who owns it?** `ls -l` tells you who owns the file or folder, and what everyone else may do.

Read the first column of `ls -l` in groups:

| `-` | `rw-` | `---` | `---` |
|---|---|---|---|
| The type: `-` a file, `d` a folder | What the **owner** may do | What the owner's **group** may do | What **everyone else** may do |

`r` is read, `w` is write, and `x` is run (for a folder: go in). The two names after it are the owner and the group.

## What broke

Last week, as root:

```
$ curl localhost:8080
settings  /app/settings.ini  loaded
uploads   /app/uploads       saved scan.txt
notes     /data              saved note 1
$ docker compose exec records whoami
root
```

After `USER app`:

```
$ curl localhost:8080
settings  /app/settings.ini  [Errno 13] Permission denied: '/app/settings.ini'
uploads   /app/uploads       [Errno 13] Permission denied: '/app/uploads/scan.txt'
notes     /data              [Errno 13] Permission denied: '/data/notes.txt'
```

Same words, three different locks.

## The chart

| Job | Path | Who owns it | The fix |
|---|---|---|---|
| `settings` | `/app/settings.ini` | `root`, and only the owner may read it | `COPY --chown=app:app --chmod=600 settings.ini ./` |
| `uploads` | `/app/uploads` | `root`: `RUN mkdir` ran as root | `RUN mkdir uploads && chown app:app uploads` |
| `notes` | `/data` | `root`: the volume, and last week's note in it | Once, as root: `docker compose run --rm --user root records chown -R app:app /data`. Also in the Dockerfile, for new volumes: `RUN mkdir /data && chown app:app /data` |

## Job 1: `settings`, a file the app can't open

```
$ docker compose exec records ls -l /app/settings.ini
-rw-------    1 root     root            53 Nov  4 05:36 /app/settings.ini
$ docker compose exec records cat /app/settings.ini
cat: can't open '/app/settings.ini': Permission denied
$ docker compose exec records id
uid=1000(app) gid=1000(app) groups=1000(app)
```

`-rw-------`: the owner may read and write, and nobody else may do anything. The owner is `root`, and you're `app`, so you're "everyone else".

Two things made it this way. `COPY` gives every file to root, unless you say otherwise. And the Dockerfile locked the file on purpose, with `--chmod=600`, to keep the settings private. That's a good habit for settings, keys and certificates. It just locked the file with root's key.

**The fix:** keep the lock, change the owner:

```dockerfile
COPY --chown=app:app --chmod=600 settings.ini ./
```

```
$ docker compose up -d --build
⋮
$ curl localhost:8080
settings  /app/settings.ini  loaded
uploads   /app/uploads       [Errno 13] Permission denied: '/app/uploads/scan.txt'
notes     /data              [Errno 13] Permission denied: '/data/notes.txt'
$ docker compose exec records ls -l /app/settings.ini
-rw-------    1 app      app             53 Nov  4 05:36 /app/settings.ini
```

Don't "fix" it with `chmod 644` or `chmod 777`. That opens the settings to every user in the container, instead of giving them to the one user that needs them.

## Job 2: `uploads`, a folder made by root

```
$ docker compose exec records ls -ld /app/uploads
drwxr-xr-x    2 root     root          4096 Nov  4 05:42 /app/uploads
```

`RUN mkdir uploads` runs before `USER app`, so it runs as root, and root owns the folder. Everyone else may read and go in (`r-x`), but not write.

**The fix:** give the folder to `app` right where you make it:

```dockerfile
RUN mkdir uploads && chown app:app uploads
```

```
$ docker compose up -d --build
⋮
$ curl localhost:8080
settings  /app/settings.ini  loaded
uploads   /app/uploads       saved scan.txt
notes     /data              [Errno 13] Permission denied: '/data/notes.txt'
```

You'll meet this with every app that writes something: logs, caches, uploads, temporary files.

## Job 3: `notes`, the volume that remembers

```
$ docker compose exec records ls -la /data
total 12
drwxr-xr-x    2 root     root          4096 Nov  4 05:47 .
drwxr-xr-x    1 root     root          4096 Nov  4 05:48 ..
-rw-r--r--    1 root     root            11 Nov  4 05:47 notes.txt
```

The folder and last week's note both belong to root. Same problem as uploads, so try the same fix: make `/data` in the Dockerfile, owned by `app`:

```dockerfile
RUN mkdir /data && chown app:app /data
```

```
$ docker compose up -d --build
⋮
$ curl localhost:8080
settings  /app/settings.ini  loaded
uploads   /app/uploads       saved scan.txt
notes     /data              [Errno 13] Permission denied: '/data/notes.txt'
$ docker run --rm keycard-records ls -ld /data
drwxr-xr-x    2 app      app           4096 Nov  4 05:36 /data
```

Still denied. Yet in the image, `/data` belongs to `app`. The container doesn't use the image's `/data`: the volume is mounted on top of it. And Docker copies a folder from the image into a volume only when the volume is **empty**. Docker's docs: "If you mount an _empty volume_ into a directory in the container in which files or directories exist, these files or directories are propagated (copied) into the volume by default." This volume isn't empty. It holds last week's note, so it keeps root's folder, and your fixed image can't change it.

**The fix:** change the volume itself, once, as root, in a fresh container that uses the same volume:

```
$ docker compose run --rm --user root records chown -R app:app /data
⋮
$ curl localhost:8080
settings  /app/settings.ini  loaded
uploads   /app/uploads       saved scan.txt
notes     /data              saved note 2
$ docker compose exec records ls -la /data
total 12
drwxr-xr-x    2 app      app           4096 Nov  4 05:47 .
drwxr-xr-x    1 root     root          4096 Nov  4 05:48 ..
-rw-r--r--    1 app      app             22 Nov  4 05:48 notes.txt
```

`-R` changes the folder and everything in it, including last week's note. Note **2**: last week's note survived.

Keep the Dockerfile line anyway. A new, empty volume gets the image's `/data`, owned by `app`, so the next server starts right.

Two fixes you'll see online, and why not to use them:

- **`docker compose down -v`, then start again.** It works, because the new volume is empty. But `-v` deletes the volume, and every note in it.
- **`user: root`, or removing `USER app`.** It works, and it undoes the security review.

## The fixed Dockerfile

```dockerfile
FROM python:3.12-alpine
RUN adduser -D app
WORKDIR /app
# keep the settings private
COPY --chown=app:app --chmod=600 settings.ini ./
RUN mkdir uploads && chown app:app uploads
RUN mkdir /data && chown app:app /data
COPY app.py ./
# security review: don't run as root
USER app
CMD ["python", "app.py"]
```

## One thing that doesn't break: port 80

People often expect a normal user to lose port 80. Inside a Docker container, it doesn't:

```
$ docker compose exec records python -c "import socket; socket.socket().bind(('', 80)); print('port 80 is fine')"
port 80 is fine
```

Since Docker 20.10, containers start with a setting that lets any user use low ports. The release notes: "Add default sysctls to allow ping sockets and privileged ports with no capabilities".

## On Linux: when `docker` itself says permission denied

Not run here: Docker Desktop doesn't have this problem. On a Linux server, the most famous permission error happens before any container starts. Any `docker` command says `permission denied while trying to connect to the docker API`, followed by the address of Docker's socket (on Linux, usually `unix:///var/run/docker.sock`). (That's Docker 29's wording. Older versions say `Got permission denied while trying to connect to the Docker daemon socket`.)

Your user isn't allowed to use Docker's socket, the file the `docker` command talks through. The fix from Docker's docs:

```bash
sudo usermod -aG docker $USER
```

Then log out and back in ("Log out and log back in so that your group membership is re-evaluated."). Know what you're giving away: "The `docker` group grants root-level privileges to the user." Only add people you'd trust with root.

## Next episode

You change the code, rebuild, and the page still shows the old version. Episode 7: my changes don't show up.

## The interview answer

> "Your app gets permission denied writing to a volume. Why, and how do you fix it safely?"

I ask two questions: who is the app running as, with `id`, and who owns the folder, with `ls -l`. Usually the app runs as a normal user, and the volume's folder belongs to root, often because the volume was created when the app still ran as root. I fix the owner, not the permissions. In the Dockerfile, I create the folder owned by the app's user. For a volume that already exists, I `chown` it once, as root. I don't use `chmod 777`, and I don't go back to running as root.
