# Lab 07 — The notice board: my changes don't show up

From **Docker Doctor, Episode 7** on the [Systems and Signals](https://www.youtube.com/@systemsandsignals) YouTube channel. Try the lab first, then watch the episode.

## The story

The clinic's notice board is a tiny nginx website with two pages:

| Page | Address | File in this folder |
|---|---|---|
| The homepage | http://localhost:8080 | `html/index.html` |
| The notices | http://localhost:8080/notices/ | `html/notices/index.html` |

Version 1 is live. Today you ship version 2.

## Step 1: version 1 is live

```bash
docker compose up -d --build
curl localhost:8080
curl localhost:8080/notices/
```

## Step 2: ship version 2

Change both pages:

```bash
echo "clinic homepage, version 2" > html/index.html
echo "clinic notices, version 2" > html/notices/index.html
```

Now do what most people try first:

```bash
docker compose up -d
curl localhost:8080
docker compose restart
curl localhost:8080
```

Still version 1.

## Your mission

1. Make **both** pages show version 2. Before every try, answer one question: **what is this container really running?**
2. A teammate wants to change pages without rebuilding the image. In `compose.yaml`, the site's `volumes:` list becomes exactly their two lines. Put them under the site's `ports` lines, and if the site still has another `volumes:` list, replace it:
   ```yaml
       volumes:
         - ./pages:/usr/share/nginx/html
   ```
   Run `docker compose up -d`, then `curl localhost:8080`. Find out what they broke, and fix it.
3. Bonus: first delete the teammate's two lines again, and run `docker compose up -d`, so the homepage comes from the image. Then change the homepage **inside** the running container with `docker compose exec`. Find your change with `docker diff`. Then run `docker compose up -d --force-recreate`, and see what happens to it. (With the bind mount still in place, your change would land in `html/index.html` on your computer instead: `docker diff` wouldn't list it, and a recreate wouldn't remove it.)

## The chart to fill in

| What you tried | What the homepage said | What the notices said | Why |
|---|---|---|---|
| `docker compose up -d` | | | |
| `docker compose restart` | | | |
| `docker compose up -d --build` | | | |
| Your fix | | | |

## Tools you'll need

```bash
docker run --rm noticeboard-site cat /usr/share/nginx/html/index.html
docker compose exec site cat /usr/share/nginx/html/index.html
docker inspect noticeboard-site-1 --format '{{range .Mounts}}{{.Type}}  {{.Name}}  {{.Destination}}{{println}}{{end}}'
docker volume ls
docker compose logs site
docker diff noticeboard-site-1
```

The first command looks inside the **image**. The second looks inside the running **container**. When they disagree, you've found your problem.

## Hints (open one at a time)

<details>
<summary>Hint 1</summary>

`docker compose restart` restarts the same container. Does that container use a new image?
</details>

<details>
<summary>Hint 2</summary>

`docker compose up -d` builds an image only if it's missing. Your edit didn't make Compose build anything. Look at the flags `docker compose up` has.
</details>

<details>
<summary>Hint 3</summary>

After a rebuild, compare the image's notices page with the container's notices page. If they're different, something is laid on top of the image. `docker inspect` lists it under `Mounts`.
</details>

<details>
<summary>Hint 4</summary>

Remember Episode 6: Docker copies the image's folder into a volume only when the volume is empty. When did this volume get its notices?
</details>

<details>
<summary>Hint 5</summary>

Are the notices **code** (they change with each version you ship) or **data** (they change while the site runs)? Code belongs in the image.
</details>

<details>
<summary>Hint 6</summary>

`403 Forbidden`, and nginx's log says `directory index ... is forbidden`: nginx found the folder, but no `index.html` in it. Run `ls` in the lab folder. Which folder did your teammate mount?
</details>

## Clean up

```bash
docker compose down -v --rmi local
rmdir pages
```

`rmdir` removes the `pages` folder only if it's empty.

The answers are in [SOLUTION.md](SOLUTION.md). Try first!
