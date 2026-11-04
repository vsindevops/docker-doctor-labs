# Lab 06 — The keycard: permission denied

From **Docker Doctor, Episode 6** on the [Systems and Signals](https://www.youtube.com/@systemsandsignals) YouTube channel. Try the lab first, then watch the episode.

## The story

The clinic's records app runs in one container. On every visit it does three jobs:

| Job | What it does | The path it needs |
|---|---|---|
| `settings` | Reads its own settings | `/app/settings.ini` |
| `uploads` | Saves a scan | `/app/uploads` |
| `notes` | Adds a note to the clinic's notes | `/data`, a volume |

Until now, the app ran as root. The security review says: **don't run containers as root.** Your job is to make that change, and fix everything it breaks.

## Step 1: last week, as root

```bash
docker compose up -d --build
curl localhost:8080
```

All three jobs work, and the first note is saved in the volume. (`--build` makes Docker build the image from this `Dockerfile`, even if an old `keycard-records` image is still around from an earlier try.)

## Step 2: the security review

In the `Dockerfile`, remove the `#` in front of `USER app`, so the line reads:

```dockerfile
USER app
```

Then rebuild, and visit again:

```bash
docker compose up -d --build
curl localhost:8080
```

Three jobs. Three times `Permission denied`.

## Your mission

1. For each job, answer two questions: **who is the app running as**, and **who owns the file or folder it needs?**
2. Fix all three, so the board says `loaded`, `saved` and `saved` again. The rules:
   - the app keeps running as `app`;
   - no `chmod 777`;
   - the note already in the volume must survive.
3. After each change, run `docker compose up -d --build`, then `curl localhost:8080`.

## The chart to fill in

| Job | Path | Who owns it | The fix |
|---|---|---|---|
| `settings` | `/app/settings.ini` | | |
| `uploads` | `/app/uploads` | | |
| `notes` | `/data` | | |

## Tools you'll need

```bash
docker compose exec records id
docker compose exec records ls -l /app/settings.ini
docker compose exec records ls -ld /app/uploads
docker compose exec records ls -la /data
docker run --rm keycard-records ls -ld /data
docker compose exec --user root records id
```

## Hints (open one at a time)

<details>
<summary>Hint 1</summary>

Read the first column of `ls -l` in groups. `-rw-------` is: the type (`-` is a file, `d` is a folder), then three letters for the **owner**, three for the owner's **group**, and three for **everyone else**. `r` is read, `w` is write, `x` is run (or, for a folder, go in). The two names after it are the owner and the group.
</details>

<details>
<summary>Hint 2</summary>

`COPY` gives every file to root, unless you tell it otherwise. Look at what else `COPY` can do besides `--chmod`.
</details>

<details>
<summary>Hint 3</summary>

Every `RUN` line before `USER app` runs as root. So everything it creates belongs to root.
</details>

<details>
<summary>Hint 4</summary>

The image's `/data` and the volume's `/data` aren't the same folder. Compare `docker run --rm keycard-records ls -ld /data` with `docker compose exec records ls -la /data`.
</details>

<details>
<summary>Hint 5</summary>

Docker copies a folder from the image into a volume only when the volume is empty. This volume isn't empty: last week's note is in it.
</details>

<details>
<summary>Hint 6</summary>

You can run one command as root, in a fresh container that uses the same volume: `docker compose run --rm --user root records ...`
</details>

## Clean up

```bash
docker compose down -v --rmi local
```

`-v` also deletes the lab's notes volume. That's fine here, because it's a lab. On a real server, think twice before you add `-v`.

The answers are in [SOLUTION.md](SOLUTION.md). Try first!
