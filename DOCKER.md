# Running the Agent-OM web interface in Docker

This brings up the web interface and the PostgreSQL database it needs, so
neither the database, nor pgvector, nor the pinned Python packages have to be
installed by hand.

```
docker compose up --build
```

Then open **http://127.0.0.1:5000**.

---

## Contents

1. [What you get](#1-what-you-get)
2. [Before you start](#2-before-you-start)
3. [Starting and stopping](#3-starting-and-stopping)
4. [Settings](#4-settings)
5. [Where your files go](#5-where-your-files-go)
6. [Everyday commands](#6-everyday-commands)
7. [After changing the code](#7-after-changing-the-code)
8. [What is in the image, and what is not](#8-what-is-in-the-image-and-what-is-not)
9. [Troubleshooting](#9-troubleshooting)
10. [Why it is built this way](#10-why-it-is-built-this-way)

---

## 1. What you get

Two services, defined in `docker-compose.yml`:

| Service | Image | Purpose |
| --- | --- | --- |
| `db` | `pgvector/pgvector:pg16` | PostgreSQL 16 with the `vector` extension the pipeline stores embeddings in |
| `web` | built from `Dockerfile` | The web interface and the matching pipeline |

`web` waits until `db` reports healthy before it starts, so the first run never
arrives before the database is accepting connections.

The files involved:

```
Dockerfile                 how the web image is built
docker-compose.yml         the two services, their volumes and settings
.dockerignore              what is kept out of the image
docker/init-pgvector.sql   creates the vector extension when the database is first made
```

## 2. Before you start

- **Docker with the Compose plugin.** Check with `docker compose version`.
- **A `.env` file** in the project root holding your API keys, the same file
  step 5 of the README already asks for:

  ```
  OPENAI_API_KEY=sk-...
  ANTHROPIC_API_KEY=sk-ant-...
  ```

  Compose reads it and passes the keys to the container. It is never copied
  into the image; `.dockerignore` excludes it. Both keys have to be present,
  because `run_config.py` reads both when it starts, whichever model you use.

You do **not** need to install PostgreSQL, create a database, run
`CREATE EXTENSION vector`, or make a virtual environment. The two services
handle all of it.

## 3. Starting and stopping

Run these from the project root, the folder holding `docker-compose.yml`.

```bash
docker compose up --build          # build if needed, then run in the foreground
docker compose up --build -d       # the same, in the background
```

The first build takes a few minutes: it downloads the PostgreSQL image and
installs the Python packages. Later starts take seconds, because both are
cached.

```bash
docker compose down                # stop, and keep the database
docker compose down -v             # stop, and delete the database as well
```

`docker compose down` leaves your matching results untouched either way: they
live on your own disk, not inside the container. See
[Where your files go](#5-where-your-files-go).

## 4. Settings

All of these are ordinary environment variables. Put them in front of the
command, or add them to `.env`.

| Variable | Default | What it does |
| --- | --- | --- |
| `WEB_PORT` | `5000` | The port on your machine the interface is published on |
| `DOCKER_UID` | `1000` | The user id the container runs as |
| `DOCKER_GID` | `1000` | The group id the container runs as |
| `OPENAI_API_KEY` | — | Passed through to the pipeline |
| `ANTHROPIC_API_KEY` | — | Passed through to the pipeline |
| `ONTOLOGY_DB_URL` | the `db` service | Where the pipeline looks for PostgreSQL |

**A different port**, useful when a copy is already running outside Docker:

```bash
WEB_PORT=8080 docker compose up -d      # → http://127.0.0.1:8080
```

**A different user id.** The container runs as user id 1000, the first user id
on a typical Linux host, so what it writes belongs to you. If your account is a
different id, say so once:

```bash
DOCKER_UID=$(id -u) DOCKER_GID=$(id -g) docker compose up -d
```

The interface is published on `127.0.0.1` only. It has no login and it accepts
API keys, so it is deliberately not offered to the rest of the network.

## 5. Where your files go

Two folders are shared between the container and your machine:

```
data/uploads/<job-id>/component/        the ontologies you uploaded
alignment/uploads/<job-id>/component/   what the run produced
```

They are on your own disk. They survive `docker compose down`, they can be
opened in any editor, and they belong to you rather than to root. The interface
also offers them through **Download all**, which gives you one archive with the
original files and the performance summary in separate folders.

The database keeps its data in a named Docker volume, `db-data`. That one is
managed by Docker and is removed only by `docker compose down -v`.

## 6. Everyday commands

```bash
docker compose ps                  # are both services up and healthy
docker compose logs -f web         # follow the interface log
docker compose logs -f db          # follow the database log
docker compose exec web bash       # a shell inside the container, as agentom
docker compose restart web         # restart just the interface
```

To look at the database directly:

```bash
docker compose exec db psql -U postgres -d ontology
```

## 7. After changing the code

The page, the stylesheet and `web_overrides.py` are read from disk each time
they are used, so a **refresh of the browser** is enough for those.

Everything else, `web_app.py` and the `om_*.py` pipeline included, is baked
into the image. After changing one of those:

```bash
docker compose up --build -d
```

This restarts the container. **A run in progress is lost when you do that**, so
let it finish first.

## 8. What is in the image, and what is not

In:

- Python 3.10 and everything in `requirements.txt`
- The interface, `run_config.py`, and the `om_*.py` pipeline

Out, by way of `.dockerignore`:

- `.env`, so the keys are never baked in
- `data/` and `alignment/`, the OAEI data and the reference results, together
  over 400 MB and needed by none of a web run, which works from what you upload
- The competition material, benchmarks, figures and notebooks

The result is a build context of about 8 MB and an image of about 1.2 GB, most
of which is the Python packages.

If you want to run the bundled OAEI alignments from inside the container, mount
the folders yourself by adding these to the `web` service:

```yaml
      - ./data:/app/data
      - ./alignment:/app/alignment
```

## 9. Troubleshooting

**`address already in use` when starting**

Something already holds port 5000, usually a copy of the interface started with
`python web_app.py`. Stop that one, or publish elsewhere:

```bash
WEB_PORT=8080 docker compose up -d
```

**The page says a key is missing**

Compose did not see your `.env`. It has to be in the same folder as
`docker-compose.yml`, and both `OPENAI_API_KEY` and `ANTHROPIC_API_KEY` have to
be in it. Check what reached the container:

```bash
docker compose exec web printenv | grep API_KEY
```

You can also type a key straight into the page, which keeps it for as long as
the container is running.

**The Database check is red**

Look at whether the database came up:

```bash
docker compose ps
docker compose logs db | tail -20
```

If it says the extension is missing, the database volume was made before the
init script existed. Recreate it, which **erases the database**:

```bash
docker compose down -v && docker compose up -d
```

**Results are owned by root and you cannot delete them**

An older container ran as root. Rebuild, and pass your own id:

```bash
DOCKER_UID=$(id -u) DOCKER_GID=$(id -g) docker compose up --build -d
```

To clear what the old one left behind:

```bash
docker run --rm -v "$PWD/data/uploads:/a" -v "$PWD/alignment/uploads:/b" \
  alpine sh -c "rm -rf /a/* /b/*"
```

**The terminal output has no colours**

Rebuild. The pipeline's colours are only produced when it believes it is
talking to a terminal, and the interface arranges that; the change is in
`web_app.py`, which lives in the image.

```bash
docker compose up --build -d
```

**A change to the code did nothing**

`web_app.py` and the pipeline are in the image. See
[After changing the code](#7-after-changing-the-code).

**Starting over completely**

```bash
docker compose down -v                     # containers and the database
docker rmi ontology-llm-web                # the built image
docker compose up --build                  # from scratch
```

## 10. Why it is built this way

Four decisions are worth knowing about, because each fixes something that
otherwise breaks.

**Python 3.10.** The version the README reports its results with. Several of
the pinned packages publish no wheel for 3.12, so a 3.12 image tries to compile
`pandas` during the build and fails.

**`numpy` is pinned to 1.26.4.** It used to be unpinned, so a fresh install
took numpy 2 while `pandas==2.0.3` is built against numpy 1. The pipeline then
could not import pandas at all, with `numpy.dtype size changed`. The pin is in
`requirements.txt` and helps a plain local install just as much.

**`ONTOLOGY_DB_URL`.** `run_config.py` names
`postgresql://postgres:postgres@127.0.0.1/ontology`, and inside a container
`127.0.0.1` is the container itself, not your machine. Compose sets this
variable to the `db` service instead, and `web_overrides.py` applies it while
the pipeline runs, so `run_config.py` is never modified. The same variable works
outside Docker when the database is on another host. Its password is masked
wherever the settings are printed.

**The container is not root.** Without that, everything written into the two
mounted folders belongs to root on your machine and you cannot delete your own
results. For the same reason those two folders are kept in the repository with
a `.gitkeep`: Docker creates a missing mount point owned by root, and a
container that is not root then cannot write into it.
