# Lab 01 — The container that stops right away

From **Docker Doctor, Episode 1** on the [Systems and Signals](https://www.youtube.com/@systemsandsignals) YouTube channel. Try the lab first, then watch the episode.

## The patient

A tiny web app, the "Docker Doctor Clinic". It shows a page that counts visitors. To start, it needs one setting: where its database is.

## Check 0: is Docker up?

```bash
docker version
```

You should see a **Client** part and a **Server** part. If you only see Client, followed by an error like `failed to connect to the docker API` or `Cannot connect to the Docker daemon`, Docker itself is not running:

- **Docker Desktop (Mac or Windows):** `docker desktop start`
- **Linux:** `sudo systemctl start docker`

## Start the app

```bash
docker build -t clinic .
docker run -d --name patient -p 8080:8000 clinic
```

Then open http://localhost:8080

## The symptom

`docker run` prints a long ID, so everything looks fine. But the page won't open, and `docker ps` shows nothing.

## Your mission

1. Find out **why** the container stopped.
2. Fix it, so that http://localhost:8080 shows the **Docker Doctor Clinic** page, and the visitor count goes up every time you refresh.
3. Make sure the next person who forgets the setting gets a clear message instead of a crash.

Use the checks in order: **STATUS → LOGS → INSPECT → INSIDE → AROUND**.

## Hints (open one at a time)

<details>
<summary>Hint 1</summary>

`docker ps` only shows containers that are running. Which option also shows the stopped ones?
</details>

<details>
<summary>Hint 2</summary>

Ask the container what it said before it stopped: `docker logs patient`. Read the **last** line first.
</details>

<details>
<summary>Hint 3 (almost the answer)</summary>

The app needs an environment variable. `-e NAME=value` gives a container a setting. You must remove the old container first (`docker rm patient`), because its name is still taken.
</details>

## Bonus patient: the quiet one

```bash
docker run -d --name box ubuntu
```

This container stops too, but **nothing is wrong** with it. Can you explain why?

<details>
<summary>Hint</summary>

Check its main command: `docker inspect --format '{{.Config.Cmd}}' box`
</details>

## Clean up

```bash
docker rm -f patient box
docker rmi clinic
```

The answers are in [SOLUTION.md](SOLUTION.md). Try first!
