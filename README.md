# Docker Doctor Labs

Broken Docker projects from the **Docker Doctor** series on the [Systems and Signals](https://www.youtube.com/@systemsandsignals) YouTube channel.

Every lab is a small app that is broken in a way real apps break. Your job is to find out **why**, fix it, and make sure it can't happen again. Try it yourself first, then watch the episode.

## How to use a lab

```bash
git clone https://github.com/vsindevops/docker-doctor-labs.git
cd docker-doctor-labs/ep01-exits-immediately
```

1. Read the lab's `README.md`. It shows how to start the app and what goes wrong.
2. Find the cause with the 5 checks below. Open a hint only if you are stuck.
3. Fix it, and prove it works.
4. Read `SOLUTION.md`, or watch the episode, and compare.

## The Docker Doctor's 5 checks

Run them in this order, every time.

| # | Check | The question | First command |
|---|---|---|---|
| 0 | **IS DOCKER UP?** | Is the hospital open? | `docker version` |
| 1 | **STATUS** | Is the patient alive? | `docker ps -a` |
| 2 | **LOGS** | What is the patient saying? | `docker logs <name>` |
| 3 | **INSPECT** | What does the medical report say? | `docker inspect <name>` |
| 4 | **INSIDE** | Let's look inside. | `docker exec -it <name> sh` |
| 5 | **AROUND** | Is something around it making it sick? | ports, networks, volumes, memory, disk |

Then: **fix it, prove it, prevent it.**

## Labs

| Episode | Lab | The symptom |
|---|---|---|
| 1 | [ep01-exits-immediately](ep01-exits-immediately) | `docker run` prints an ID, but the app never opens, and `docker ps` is empty |

A new lab arrives with every episode.

## Stay safe

- Labs only use small images and the names shown in each README (like `patient` and `box`). Clean up with the commands at the end of each lab.
- Never practise on a computer or server you use for real work.

## License

MIT. See [LICENSE](LICENSE).
