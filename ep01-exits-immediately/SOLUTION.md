# Lab 01 — Solution

## What we found

**STATUS.** `docker ps` is empty, because it only lists running containers. `docker ps -a` lists all of them:

```
STATUS
Exited (1) 2 seconds ago
```

`Exited` means it stopped. The `1` means it stopped because of an error.

**LOGS.** `docker logs patient` shows what the app printed before it stopped. The last line is the reason:

```
KeyError: 'DATABASE_URL'
```

**The cause:** the app reads the setting `DATABASE_URL` when it starts. We never gave it one, so the app crashed. A container only lives as long as its main program, so the container stopped too.

## The fix

The name `patient` still belongs to the stopped container. Running the same name again gives:

```
Conflict. The container name "/patient" is already in use by container "…". You have to remove (or rename) that container to be able to reuse that name.
```

So remove the old one first, then run it again with the setting:

```bash
docker rm patient
docker run -d --name patient -p 8080:8000 -e DATABASE_URL=sqlite:///clinic.db clinic
```

## Prove it

```bash
docker ps
```

`patient` is `Up`, and http://localhost:8080 shows the **Docker Doctor Clinic** page with a visitor count. Refresh it, and the number goes up by one.

## Prevent it

Make the app explain itself. In `app.py`, replace this line:

```python
DATABASE_URL = os.environ["DATABASE_URL"]
```

with:

```python
DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    raise SystemExit("ERROR: DATABASE_URL is not set. Start the app with -e DATABASE_URL=sqlite:///clinic.db")
```

Rebuild, and test it without the setting:

```bash
docker build -t clinic .
docker run --rm clinic
```

```
ERROR: DATABASE_URL is not set. Start the app with -e DATABASE_URL=sqlite:///clinic.db
```

Now the logs tell the next person exactly what to do. (`--rm` removes the test container as soon as it stops.)

## The bonus patient

`docker ps -a` shows `box` as `Exited (0)`, and `docker logs box` is empty. The `0` means it finished **without** an error.

```bash
docker inspect --format '{{.Config.Cmd}}' box
```

```
[/bin/bash]
```

The ubuntu image's main program is `bash`, a shell that waits for someone to type. With `-d` nobody is typing, so bash ends at once, and the container ends with it. Nothing is broken; it simply had no job. Give it one:

```bash
docker rm box
docker run -d --name box ubuntu sleep infinity
```

## The interview answer

> "Your container exits right after it starts. How do you find out why?"

First I run `docker ps -a`, because `docker ps` hides stopped containers, and the status shows the exit code. Then I read `docker logs` from the bottom, which usually shows the reason, like a missing environment variable. If the logs are empty, I use `docker inspect` to check the exit code and the main command, and I remember that exit code 0 means the program simply finished.
