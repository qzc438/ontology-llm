# Running Agent-OM in Docker

This brings up the web interface, the PostgreSQL database it needs, and an
Ollama for the open models. Nothing else has to be installed: no PostgreSQL, no
pgvector, no `ontology` database, no virtual environment, no Ollama.

```bash
docker compose up --build
```

Then open **http://127.0.0.1:5000**.

You need two things beforehand:

- **Docker with the Compose plugin.** Check with `docker compose version`.
- **A `.env` file** beside `docker-compose.yml`, holding both keys:

  ```
  OPENAI_API_KEY=sk-...
  ANTHROPIC_API_KEY=sk-ant-...
  ```

  Both have to be there, because `run_config.py` reads both when it starts,
  whichever model you use. `.env` is never copied into the image.

---

## Contents

1. [What is running](#1-what-is-running)
2. [Everyday commands](#2-everyday-commands)
3. [Settings](#3-settings)
4. [Where your files go](#4-where-your-files-go)
5. [Open models](#5-open-models)
6. [Troubleshooting](#6-troubleshooting)
7. [Why it is built this way](#7-why-it-is-built-this-way)

---

## 1. What is running

| Service | Image | Purpose |
| --- | --- | --- |
| `db` | `pgvector/pgvector:pg16` | PostgreSQL 16 with the `vector` extension the embeddings need |
| `ollama` | `ollama/ollama:0.33.2` | Runs the open models |
| `web` | built from `Dockerfile` | The interface and the matching pipeline |

`web` waits until the other two report healthy, so a run never arrives before
the database is accepting connections.

The first build takes a few minutes, downloading the images and installing the
Python packages. Later starts take seconds.

## 2. Everyday commands

```bash
docker compose up --build -d    # start in the background
docker compose down             # stop, keeping the database and the models
docker compose down -v          # stop, discarding them

docker compose ps               # what is up, and healthy
docker compose logs -f web      # follow the interface log
docker compose exec web bash    # a shell inside the container
docker compose exec db psql -U postgres -d ontology    # the database itself
```

**After editing the code.** The page and the stylesheet are re-read on a browser
refresh. Everything else is in the image, `web_app.py`, `web_overrides.py` and
the `om_*.py` pipeline included, so rebuild:

```bash
docker compose up --build -d
```

That restarts the container, and a run in progress is lost with it. Let it
finish first.

## 3. Settings

Ordinary environment variables. Put them in front of the command, or in `.env`.

| Variable | Default | What it does |
| --- | --- | --- |
| `WEB_PORT` | `5000` | The port published on your machine |
| `DOCKER_UID`, `DOCKER_GID` | `1000` | The user the container runs as |
| `OPENAI_API_KEY`, `ANTHROPIC_API_KEY` | — | Passed through to the pipeline |
| `ONTOLOGY_DB_URL` | the `db` service | Where the pipeline looks for PostgreSQL |
| `OLLAMA_URL` | the `ollama` service | Where it looks for Ollama, see [Open models](#5-open-models) |

```bash
WEB_PORT=8080 docker compose up -d                              # another port
DOCKER_UID=$(id -u) DOCKER_GID=$(id -g) docker compose up -d    # your own id
```

Pass your own id if your account is not 1000, so that what the container writes
into the shared folders belongs to you.

The interface is published on `127.0.0.1` only. It has no login and it holds API
keys, so it is deliberately not offered to the rest of the network.

## 4. Where your files go

```
data/uploads/…        the ontologies you uploaded    on your own disk
alignment/uploads/…   what the run produced          on your own disk
db-data               the database                   docker volume
ollama-models         the models you download        docker volume
```

The first two are on your machine: they outlive the containers, open in any
editor, and belong to you. **Download all** on the page gives you one archive of
a run instead.

The two volumes survive `docker compose down` and go only with `down -v`.

## 5. Open models

Ollama comes up with the stack, so the open models need nothing on the host.
Choose one on the page and press **Download** beside it if the menu says it is
not there; the pull runs in the `ollama` service and its progress is shown on
the page.

Every open model is marked **✓ downloaded** or **— not downloaded** once Ollama
has answered, and pressing Start with one that cannot run is refused straight
away rather than failing minutes later.

### Embeddings need a model built for them

`run_config.py` offers `OllamaEmbeddings(model="llama3:8b")`. That works on
older Ollama versions and is refused by current ones, which check that a model
declares the embedding capability before using it for embeddings:

```
This server does not support embeddings. Start it with `--embeddings`
```

`llama3:8b` is a chat model, so pick one built for embeddings instead. Adding
these two lines to `run_config.py` puts it in the Embeddings menu, commented out
like the other alternatives there, and the **Download** button will fetch it:

```python
# embeddings_service = OllamaEmbeddings(model="nomic-embed-text")
# vector_length = 768
```

The interface asks Ollama for one embedding before a run starts, so a model that
cannot do it is refused at the button rather than several minutes in.

### The GPU

The service runs on the **CPU**, which works but is slow at 7b and above. To
give it the GPU, install the
[NVIDIA container toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html)
and uncomment the `deploy` block already written in the `ollama` service. It is
commented out because without the toolkit that block stops the stack starting.

### Using the Ollama on your host instead

Worth doing when your host Ollama already has the GPU and the models:

```bash
OLLAMA_URL=http://host.docker.internal:11434 docker compose up -d
```

The name resolves, but by default Ollama listens on `127.0.0.1` only and refuses
the container anyway. The symptom is a page saying nothing answered at that
address. On Linux with systemd, `sudo systemctl edit ollama` and add:

```
[Service]
Environment="OLLAMA_HOST=0.0.0.0:11434"
```

then:

```bash
sudo systemctl restart ollama
ss -ltn | grep 11434     # should no longer say 127.0.0.1
```

`0.0.0.0` means every interface, not only Docker, so put a firewall in front of
it on a shared network. `OLLAMA_URL` points anywhere, so another machine's GPU
works the same way. The `ollama` service still starts and sits idle, costing one
image download and a little memory.

None of this applies to the OpenAI and Anthropic models, which are called over
the internet.

## 6. Troubleshooting

**`address already in use`** — something else holds port 5000, usually a copy
started with `python web_app.py`. Stop it, or `WEB_PORT=8080 docker compose up -d`.

**The page says a key is missing** — Compose did not see your `.env`. It must sit
beside `docker-compose.yml` and hold both keys. Check what arrived:

```bash
docker compose exec web printenv | grep API_KEY
```

You can also type a key into the page, which keeps it while the container runs.

**The Database check is red** — see whether it came up at all:

```bash
docker compose ps
docker compose logs db | tail -20
```

If it reports the extension is missing, the volume predates the init script.
Recreating it **erases the database**: `docker compose down -v && docker compose up -d`.

**An open model fails as the run reaches it** — find out which Ollama is being
asked, and whether it answers:

```bash
docker compose exec web sh -c 'echo $OLLAMA_URL; curl -s "$OLLAMA_URL/api/tags"'
```

If it names `ollama:11434` and answers, the model is simply not downloaded:
press **Download** on the page, or `docker compose exec ollama ollama pull llama3:8b`.
If it names `host.docker.internal` and answers with nothing, see
[Using the Ollama on your host instead](#using-the-ollama-on-your-host-instead).

**An open model runs but is very slow** — it is on the CPU. See [The GPU](#the-gpu).

**Results are owned by root** — an older container ran as root. Rebuild with your
own id, then clear what it left:

```bash
DOCKER_UID=$(id -u) DOCKER_GID=$(id -g) docker compose up --build -d
docker run --rm -v "$PWD/data/uploads:/a" -v "$PWD/alignment/uploads:/b" \
  alpine sh -c "rm -rf /a/* /b/*"
```

**No colours in the terminal output**, or **a change to the code did nothing** —
both live in the image. Rebuild: `docker compose up --build -d`.

**Starting over completely**

```bash
docker compose down -v          # containers, database and models
docker rmi ontology-llm-web     # the built image
docker compose up --build
```

## 7. Why it is built this way

Five decisions, each fixing something that otherwise breaks.

**Python 3.10**, the version the README reports its results with. Several pinned
packages publish no wheel for 3.12, so a 3.12 image tries to compile `pandas`
during the build and fails.

**`numpy` pinned to 1.26.4.** Unpinned, a fresh install takes numpy 2 while
`pandas==2.0.3` is built against numpy 1, and the pipeline cannot import pandas
at all: `numpy.dtype size changed`. The pin is in `requirements.txt`, so it helps
a local install just as much.

**`ONTOLOGY_DB_URL`.** `run_config.py` names `127.0.0.1`, which inside a
container is the container itself. Compose points this at the `db` service
instead and `web_overrides.py` applies it while the pipeline runs, so
`run_config.py` is never modified. The same variable works outside Docker when
the database is on another host. Its password is masked wherever it is printed.

**The container is not root**, or everything written into the two shared folders
would belong to root on your machine and you could not delete your own results.
Those folders are kept in the repository with a `.gitkeep` for the same reason:
Docker creates a missing mount point owned by root, which a non-root container
then cannot write into.

**`/app` belongs to group 0**, and the container carries that group. The pipeline
writes into `/app` itself, not only the mounts — `run_config.py` appends to
`time.csv` before it starts anything — so owning it as one fixed user id would
break every run for anyone passing a different `DOCKER_UID`.
