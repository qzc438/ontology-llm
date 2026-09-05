# Running Agent-OM with Docker

This brings up the web interface, the PostgreSQL database it needs, and an
Ollama for the open models. Nothing else has to be installed: no PostgreSQL, no
pgvector, no `ontology` database, no virtual environment, no Ollama.

```bash
./docker-start.sh --build
```

Then open **http://127.0.0.1:5000**.

`docker-start.sh` uses an NVIDIA GPU if the machine has a usable one and the
CPU if it does not, so the same command works everywhere.
`docker compose up --build` does the same thing without ever looking for a GPU.

### Before you start

| You need | Check it with |
| --- | --- |
| **Docker, with the Compose plugin** | `docker compose version` |
| **A `.env` file** beside `docker-compose.yml` | `ls .env` |

`.env` holds both keys:

```
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
```

Both have to be there, because `run_config.py` reads both when it starts,
whichever model you use. `.env` is never copied into the image.

---

## Contents

| | Section | For |
| --- | --- | --- |
| 1 | [Docker Images](#1-docker-images) | the three services |
| 2 | [Starting and stopping](#2-starting-and-stopping) | start, stop, logs, rebuild |
| 3 | [Settings](#3-settings) | ports, ids, keys, URLs |
| 4 | [File locations](#4-file-locations) | uploads, results, volumes |
| 5 | [Using open models with Ollama](#5-using-open-models-with-ollama) | Ollama and the model menu |
| 6 | [Running with NVIDIA GPUs](#6-running-with-nvidia-gpus) | setup, and why it is not being used |
| 7 | [Troubleshooting](#7-troubleshooting) | when something is wrong |
| 8 | [Notes](#8-notes) | the design decisions, and why |

---

## 1. Docker Images

| Service | Image | Purpose |
| --- | --- | --- |
| `db` | `pgvector/pgvector:pg16` | PostgreSQL 16 with the `vector` extension the embeddings need |
| `ollama` | `ollama/ollama:0.15.0` | Runs the open models |
| `web` | built from `Dockerfile` | The interface and the matching pipeline |

`web` waits until the other two report healthy, so a run never arrives before
the database is accepting connections.

The first build takes a few minutes, downloading the images and installing the
Python packages. Later starts take seconds.

---

## 2. Starting and stopping

```bash
docker compose up --build -d    # start in the background
docker compose down             # stop, keeping the database and the models
docker compose down -v          # stop, discarding them

docker compose ps               # what is up, and healthy
docker compose logs -f web      # follow the interface log
docker compose exec web bash    # a shell inside the container
docker compose exec db psql -U postgres -d ontology    # the database itself
```

### After editing the code

The page and the stylesheet are re-read on a browser refresh.

Everything else is in the image — `web_app.py`, `web_overrides.py` and the
`om_*.py` pipeline included — so rebuild:

```bash
docker compose up --build -d
```

> That restarts the container, and a run in progress is lost with it. Let it
> finish first.

---

## 3. Settings

Ordinary environment variables. Put them in front of the command, or in `.env`.

| Variable | Default | What it does |
| --- | --- | --- |
| `WEB_PORT` | `5000` | The port published on your machine |
| `DOCKER_UID`, `DOCKER_GID` | `1000` | The user the container runs as |
| `OPENAI_API_KEY`, `ANTHROPIC_API_KEY` | — | Passed through to the pipeline |
| `ONTOLOGY_DB_URL` | the `db` service | Where the pipeline looks for PostgreSQL |
| `OLLAMA_URL` | the `ollama` service | Where it looks for Ollama, see [section 5](#5-using-open-models-with-ollama) |

```bash
WEB_PORT=8080 docker compose up -d                              # another port
DOCKER_UID=$(id -u) DOCKER_GID=$(id -g) docker compose up -d    # your own id
```

Pass your own id if your account is not 1000, so that what the container writes
into the shared folders belongs to you.

> The interface is published on `127.0.0.1` only. It has no login and it holds
> API keys, so it is deliberately not offered to the rest of the network.

---

## 4. File locations

| Path | Holds | Lives |
| --- | --- | --- |
| `data/uploads/…` | the ontologies you uploaded | on your own disk |
| `alignment/uploads/…` | what the run produced | on your own disk |
| `db-data` | the database | docker volume |
| `ollama-models` | the models you download | docker volume |

The first two are on your machine: they outlive the containers, open in any
editor, and belong to you. **Download all** on the page gives you one archive of
a run instead.

The two volumes survive `docker compose down` and go only with `down -v`.

---

## 5. Using open models with Ollama

Ollama comes up with the stack, so the open models need nothing on the host.
Choose one on the page and press **Download** beside it if the menu says it is
not there; the pull runs in the `ollama` service and its progress is shown on
the page.

Every open model is marked **✓ downloaded** or **— not downloaded** once Ollama
has answered, and pressing Start with one that cannot run is refused straight
away rather than failing minutes later.

### Why Ollama is pinned to 0.15.0

`run_config.py` offers `OllamaEmbeddings(model="llama3:8b")`, and the project's
results were produced with it.

Somewhere after 0.15, Ollama stopped producing embeddings from a model that does
not declare the embedding capability — a test that every chat model fails — and
answers instead with:

```
This server does not support embeddings. Start it with `--embeddings`
```

So the `ollama` service is pinned to `0.15.0`, where `llama3:8b` embeds as it
always did. Left on `latest` it silently moved to a version that refuses, and a
setting that worked on the host stopped working in the container.

**The cost** is that models released since need a newer Ollama. If you raise the
pin, switch to a model built for embeddings at the same time. Adding these two
lines to `run_config.py` puts one in the Embeddings menu, commented out like the
other alternatives there, and the **Download** button fetches it:

```python
# embeddings_service = OllamaEmbeddings(model="nomic-embed-text")
# vector_length = 768
```

Either way the interface asks Ollama for one embedding before a run starts, so a
combination that cannot work is refused at the button rather than minutes in.
That check tests the server rather than trusting what a model says about itself,
because 0.15.0 reports `llama3:8b` as completion-only and then embeds with it
anyway.

### Using the Ollama on your host instead

Worth doing when your host Ollama already has the GPU and the models:

```bash
OLLAMA_URL=http://host.docker.internal:11434 docker compose up -d
```

The name resolves, but by default Ollama listens on `127.0.0.1` only and refuses
the container anyway. The symptom is a page saying nothing answered at that
address.

On Linux with systemd, run `sudo systemctl edit ollama` and add:

```
[Service]
Environment="OLLAMA_HOST=0.0.0.0:11434"
```

then:

```bash
sudo systemctl restart ollama
ss -ltn | grep 11434     # should no longer say 127.0.0.1
```

> `0.0.0.0` means every interface, not only Docker, so put a firewall in front
> of it on a shared network.

`OLLAMA_URL` points anywhere, so another machine's GPU works the same way. The
`ollama` service still starts and sits idle, costing one image download and a
little memory.

None of this applies to the OpenAI and Anthropic models, which are called over
the internet.

---

## 6. Running with NVIDIA GPUs

The open models are far quicker on a GPU than on a CPU, which is slow at 7b and
above.

### Starting with the card

`./docker-start.sh` looks for a card and uses it, so on a machine with one
there is nothing to do:

```bash
./docker-start.sh              # GPU if there is one, CPU if not
./docker-start.sh --cpu        # ignore the card
```

It says which it chose. If the driver is there but Docker cannot hand the card
over, it says that too and starts on the CPU rather than not starting at all.

To skip the detection and ask for the GPU directly:

```bash
docker compose -f docker-compose.yml -f docker-compose.gpu.yml up -d
```

Either way the host needs two things: the NVIDIA driver and the NVIDIA
container toolkit.

### Installing the NVIDIA container toolkit

The driver on its own is not enough. Without the toolkit,
`./docker-start.sh` says the card cannot be handed over and falls back to the
CPU, and `./docker-check-gpu.sh` stops at step 2. Installing it is a one-off,
and takes three steps:

```bash
# 1. add NVIDIA's package repository
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey \
  | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg

echo 'deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://nvidia.github.io/libnvidia-container/stable/deb/$(ARCH) /' \
  | sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list

# 2. install it
sudo apt-get update && sudo apt-get install -y nvidia-container-toolkit

# 3. register it with Docker
sudo nvidia-ctk runtime configure --runtime=docker
sudo systemctl restart docker
```

> Type `$(ARCH)` exactly as it appears, inside single quotes. It is apt that
> expands it, and the shell must not expand it first.

Step 3 writes `/etc/docker/daemon.json` and adds `nvidia` to Docker's runtimes,
which is the part that actually lets a container reach the card. Check both:

```bash
docker info | grep -i -A3 Runtimes    # nvidia should be in the list

# should name your card; uses the ollama image, which the stack pulls anyway
docker run --rm --gpus all --entrypoint nvidia-smi ollama/ollama:0.15.0 -L
```

Then start the stack with `./docker-start.sh`. A container keeps whatever it was
started with, so one that is already up will not pick up the card on its own;
`./docker-start.sh` recreates it.

The upstream instructions, for a distribution other than Debian or Ubuntu, are
in the [NVIDIA container toolkit install guide](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html).

### If you have a card and it is not being used

```bash
./docker-check-gpu.sh
```

It tests four links in turn, stopping at the first one that is broken and
telling you what to do about it:

| | Link | Broken when |
| --- | --- | --- |
| 1 | The driver sees the card | no driver, or no card |
| 2 | Docker can pass it through | the container toolkit is missing |
| 3 | The running container was given it | started by a plain `docker compose up` |
| 4 | Ollama sees it | the reservation is there but `nvidia-smi` fails inside |

The commonest answer is **3**, because a plain `docker compose up` starts the
container with no GPU reservation and looks entirely normal doing it.

The script also says how to check which processor a model actually loaded onto,
which is the only direct answer to whether the card is being used:

```bash
docker compose exec ollama ollama ps
```

`PROCESSOR` reads `100% GPU` when the card is doing the work, `100% CPU` when it
is not, and a split such as `40%/60% CPU/GPU` when the model is too large for
the card's memory and only part of it fits.

### A known-good configuration

Verified working on 4 September 2026:

| Part | Version |
| --- | --- |
| GPU | NVIDIA GeForce RTX 4090, 24 GB |
| Driver | 595.84, CUDA 13.2 |
| NVIDIA container toolkit | 1.20.0 |
| Docker Engine | 29.8.0 |
| Docker Compose | v5.5.1 |
| Host | Ubuntu 24.04 |
| `ollama` image | `ollama/ollama:0.15.0` |
| `db` image | `pgvector/pgvector:pg16` |

With that in place, `./docker-check-gpu.sh` reports all four links holding, and
Ollama names the card as it starts:

```bash
docker compose logs ollama | grep "inference compute"
```

```
inference compute id=GPU-… library=CUDA compute=8.9 name=CUDA0
description="NVIDIA GeForce RTX 4090" driver=13.2 total="24.0 GiB"
```

---

## 7. Troubleshooting

| Symptom | Go to |
| --- | --- |
| `address already in use` | [Port 5000 is taken](#port-5000-is-taken) |
| The page says a key is missing | [A key is missing](#a-key-is-missing) |
| The Database check is red | [The database check is red](#the-database-check-is-red) |
| An open model fails as the run reaches it | [An open model fails](#an-open-model-fails) |
| An open model runs, but very slowly | [Running with NVIDIA GPUs](#6-running-with-nvidia-gpus) |
| Results are owned by root | [Results are owned by root](#results-are-owned-by-root) |
| No colours, or a code change did nothing | [A code change did nothing](#a-code-change-did-nothing) |

### Port 5000 is taken

Something else holds it, usually a copy started with `python web_app.py`. Stop
that copy, or move Agent-OM out of its way:

```bash
WEB_PORT=8080 docker compose up -d
```

### A key is missing

Compose did not see your `.env`. It must sit beside `docker-compose.yml` and
hold both keys. Check what arrived:

```bash
docker compose exec web printenv | grep API_KEY
```

You can also type a key into the page, which keeps it while the container runs.

### The database check is red

See whether it came up at all:

```bash
docker compose ps
docker compose logs db | tail -20
```

If it reports the extension is missing, the volume predates the init script.

> Recreating it **erases the database**:
> `docker compose down -v && docker compose up -d`

### An open model fails

Find out which Ollama is being asked, and whether it answers:

```bash
docker compose exec web sh -c 'echo $OLLAMA_URL; curl -s "$OLLAMA_URL/api/tags"'
```

| It says | Meaning |
| --- | --- |
| `ollama:11434`, and answers | the model is simply not downloaded |
| `host.docker.internal`, answers with nothing | see [Using the Ollama on your host instead](#using-the-ollama-on-your-host-instead) |

To download it: press **Download** on the page, or

```bash
docker compose exec ollama ollama pull llama3:8b
```

### Results are owned by root

An older container ran as root. Rebuild with your own id, then clear what it
left:

```bash
DOCKER_UID=$(id -u) DOCKER_GID=$(id -g) docker compose up --build -d
docker run --rm -v "$PWD/data/uploads:/a" -v "$PWD/alignment/uploads:/b" \
  alpine sh -c "rm -rf /a/* /b/*"
```

### A code change did nothing

Both the code and the terminal colours live in the image. Rebuild:

```bash
docker compose up --build -d
```

### Starting over completely

```bash
docker compose down -v          # containers, database and models
docker rmi ontology-llm-web     # the built image
docker compose up --build
```

---

## 8. Notes

Five decisions, each fixing something that otherwise breaks.

### Python 3.10

The version the README reports its results with. Several pinned packages publish
no wheel for 3.12, so a 3.12 image tries to compile `pandas` during the build
and fails.

### `numpy` pinned to 1.26.4

Unpinned, a fresh install takes numpy 2 while `pandas==2.0.3` is built against
numpy 1, and the pipeline cannot import pandas at all:
`numpy.dtype size changed`. The pin is in `requirements.txt`, so it helps a
local install just as much.

### `ONTOLOGY_DB_URL`

`run_config.py` names `127.0.0.1`, which inside a container is the container
itself. Compose points this at the `db` service instead and `web_overrides.py`
applies it while the pipeline runs, so `run_config.py` is never modified.

The same variable works outside Docker when the database is on another host. Its
password is masked wherever it is printed.

### The container is not root

Otherwise everything written into the two shared folders would belong to root on
your machine, and you could not delete your own results.

Those folders are kept in the repository with a `.gitkeep` for the same reason:
Docker creates a missing mount point owned by root, which a non-root container
then cannot write into.

### `/app` belongs to group 0

The container carries that group as well. The pipeline writes into `/app`
itself, not only the mounts — `run_config.py` appends to `time.csv` before it
starts anything — so owning it as one fixed user id would break every run for
anyone passing a different `DOCKER_UID`.
