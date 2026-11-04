# Lab 07 — Solution

Measured on Docker Desktop for Mac (Docker Engine 29.9.2, Compose 5.6.1, nginx 1.31.8, Apple Silicon).

In the terminal blocks below, `$` marks a command, and `⋮` marks output left out (Compose's progress lines, for example).

## The one question

When your change doesn't show up, ask: **what is this container really running?** Look at three layers, from the bottom up:

| Layer | What it is | How to look |
|---|---|---|
| The image | What was built | `docker run --rm noticeboard-site cat FILE` |
| The container | What's running now | `docker compose exec site cat FILE` |
| Mounts | Volumes and folders laid **on top** of the image | `docker inspect` (the `Mounts` part) |

## Try 1: `docker compose up -d`

```
$ docker compose up -d
[+] up 1/1
 ✔ Container noticeboard-site-1 Running                                                         0.0s
$ curl localhost:8080
clinic homepage, version 1
```

`Running`: Compose did nothing. It recreates a container only when something it watches has changed. Docker's docs: "If there are existing containers for a service, and the service’s configuration or image was changed after the container’s creation, `docker compose up` picks up the changes by stopping and recreating the containers". You changed neither. You changed a file in the build folder, and nothing rebuilt the image.

## Try 2: `docker compose restart`

```
$ docker compose restart
⋮
$ curl localhost:8080
clinic homepage, version 1
```

`restart` stops and starts the **same** container, with the same image. Docker's docs: "If you make changes to your `compose.yml` configuration, these changes are not reflected after running this command." Your page edits aren't even in the configuration, so `restart` can never show them.

## The proof: the image never saw your edit

```
$ docker run --rm noticeboard-site cat /usr/share/nginx/html/index.html
clinic homepage, version 1
```

`docker run --rm IMAGE COMMAND` starts a throwaway container from the image, runs one command, and removes it. The image itself still holds version 1.

## The fix: build, and recreate

```
$ docker compose up -d --build
⋮
$ curl localhost:8080
clinic homepage, version 2
```

`--build` builds a new image first. The image changed, so Compose replaces the container.

## The notices: half the site

```
$ curl localhost:8080/notices/
clinic notices, version 1
$ docker run --rm noticeboard-site cat /usr/share/nginx/html/notices/index.html
clinic notices, version 2
$ docker compose exec site cat /usr/share/nginx/html/notices/index.html
clinic notices, version 1
$ docker inspect noticeboard-site-1 --format '{{range .Mounts}}{{.Type}}  {{.Name}}  {{.Destination}}{{println}}{{end}}'
volume  noticeboard_notices  /usr/share/nginx/html/notices
```

The image has version 2, and the container shows version 1. Something lies on top of the image: a volume, mounted on the notices folder.

This is Episode 6's rule, working against you. On the very first start, the volume was empty, so Docker copied the image's notices into it: version 1. After that, the volume was never empty again, so Docker never copied anything again. And when Compose recreates a container, it keeps the volume: the docs say Compose recreates "(preserving mounted volumes)". So the volume's version 1 covers the image's version 2. The docs: "If you mount a _non-empty volume_ into a directory in the container in which files or directories exist, the pre-existing files are obscured by the mount."

**The fix:** decide what the notices are. They change with every version you ship, so they're **code**, and code belongs in the image. Delete the volume lines from `compose.yaml`, the one under the site:

```yaml
    volumes:
      - notices:/usr/share/nginx/html/notices   # keep the notices when the container is replaced
```

and the one at the bottom:

```yaml
volumes:
  notices:
```

```
$ docker compose up -d
⋮
$ curl localhost:8080/notices/
clinic notices, version 2
$ docker volume rm noticeboard_notices
noticeboard_notices
```

The last command removes the old volume, which nothing uses any more.

If the notices were **data**, changed while the site runs, you'd keep the volume. Then they shouldn't be in the image at all: the image would only ever fill an empty volume once.

### When the volume has no name: `node_modules` and friends

A volume written as just a path, like `- /app/node_modules` in a Node.js project, has no name. Compose still moves it to every new container, so `--build` isn't enough there either. We measured it with the notices folder, written as `- /usr/share/nginx/html/notices`: after `--build`, the notices still said version 1. After `docker compose up -d --build -V`, they said version 2. Docker's docs on `-V`, `--renew-anon-volumes`: "Recreate anonymous volumes instead of retrieving data from the previous containers". The old unnamed volume is left behind, unused.

## The teammate's bind mount: 403 Forbidden

The teammate's two lines, under the site's ports lines:

```yaml
    volumes:
      - ./pages:/usr/share/nginx/html
```

```
$ docker compose up -d
⋮
$ curl localhost:8080
<html>
<head><title>403 Forbidden</title></head>
<body>
<center><h1>403 Forbidden</h1></center>
<hr><center>nginx/1.31.8</center>
</body>
</html>
$ docker compose logs site | grep forbidden
site-1  | 2026/11/04 16:08:46 [error] 30#30: *1 directory index of "/usr/share/nginx/html/" is forbidden, client: 192.168.65.1, server: localhost, request: "GET / HTTP/1.1", host: "localhost:8080"
$ ls
Dockerfile  compose.yaml  html  pages
```

A bind mount lays a folder from your computer over a folder in the container. The teammate wrote `./pages`, but the pages live in `./html`. There was no `pages` folder, so Docker made an empty one. Docker's docs: "If you use `--volume` to bind-mount a file or directory that does not yet exist on the Docker host, Docker automatically creates the directory on the host for you." That empty folder now covers all of the image's pages. nginx finds the folder, but no `index.html` in it, so it refuses: `403 Forbidden`, "directory index ... is forbidden".

**The fix:** mount the right folder:

```yaml
    volumes:
      - ./html:/usr/share/nginx/html
```

```
$ docker compose up -d
⋮
$ curl localhost:8080
clinic homepage, version 2
$ echo "clinic homepage, version 3" > html/index.html
$ curl localhost:8080
clinic homepage, version 3
$ docker run --rm noticeboard-site cat /usr/share/nginx/html/index.html
clinic homepage, version 2
```

Now an edit on your computer shows up at once, with no rebuild. That's great while you develop. But the image still says version 2: the image only changes when you build it. Before you ship, remove the bind mount and build.

## The hot fix that vanishes

First, take the bind mount out again: delete its two lines, so the homepage comes from the image.

```
$ docker compose up -d
⋮
$ curl localhost:8080
clinic homepage, version 2
```

Now change the homepage by hand, inside the running container:

```
$ docker compose exec site sh -c 'echo "clinic homepage, hot fix" > /usr/share/nginx/html/index.html'
$ curl localhost:8080
clinic homepage, hot fix
$ docker diff noticeboard-site-1 | grep html
C /usr/share/nginx/html
C /usr/share/nginx/html/index.html
$ docker compose up -d --force-recreate
⋮
$ curl localhost:8080
clinic homepage, version 2
```

`docker diff` lists what changed inside a container since it was created: `A` added, `C` changed, `D` deleted. (Without `| grep html`, it also lists files nginx changes by itself when it starts.) A change made inside a container lives only as long as that container. The next recreate, from any deploy, starts again from the image, and the hot fix is gone. Put the fix in the image instead.

Why take the bind mount out first? With it still in place, the "inside" change goes through the mount, into `html/index.html` on your computer. We measured it: the page said `clinic homepage, hot fix`, so did the file on the Mac, `docker diff` listed nothing, and after `docker compose up -d --force-recreate` the page still said `hot fix`. A bind mount writes straight to your computer, and outlives every container.

## Prevent it next time

- **Never forget `--build`.** Tell Compose to build on every `up` (try it after the lab: it changes what the steps above print):

  ```yaml
    site:
      build: .
      pull_policy: build
  ```

  Docker's docs on `pull_policy`: "`build`: Compose builds the image. Compose rebuilds the image if it's already present."
- **Code in the image, data in volumes.** A volume is filled from the image only while it's empty.
- **Develop with a bind mount, ship with a build.** Your edits show at once, but the image doesn't have them.
- **No hot fixes inside containers.** Put the fix in the image, and ship it.

## Next episode

You build, and the build itself fails, with a wall of text. Episode 8: read a failed build like a detective.

## The interview answer

> "You deployed a fix, but users still see the old version. Where do you look?"

I check what the container is really running, layer by layer. First the image: was it rebuilt? `docker compose up` only builds with `--build`, and `restart` never changes the image. Then the container: I compare a file in the image, with `docker run --rm`, against the same file in the container, with `docker exec`. If they differ, something is mounted on top: a volume filled by an old version, or a bind mount. If someone changed files inside the container, `docker diff` shows it. And if the container serves the new version, I look past Docker, at caches between the server and the user.
