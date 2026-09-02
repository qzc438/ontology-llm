# Agent-OM web interface.
#
# Only the interface and the matching pipeline are in here. The OAEI data under
# data/ and the reference results under alignment/ are left out of the image and
# mounted instead, because between them they are over 400 MB and neither is
# needed to serve a run: the interface works from uploaded files and writes into
# data/uploads and alignment/uploads, which web_app.py creates at start-up.
#
#   docker compose up --build      then open http://127.0.0.1:5000

# 3.10 because that is the version the README reports its results with, and the
# versions pinned in requirements.txt all publish wheels for it. On 3.12 several
# of them, pandas 2.0.3 among them, have no wheel and have to be compiled.
FROM python:3.10-slim

# curl is only here so the container can report its own health
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Requirements first, so a change to the application does not reinstall them.
# The whole file is used rather than a trimmed copy, so the container has the
# same packages the README asks for and cannot drift away from it.
COPY requirements.txt ./
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

COPY . .

# these are volume mount points, created so the image works without them too
RUN mkdir -p data/uploads alignment/uploads

# Run as an ordinary user rather than root. Without this, everything the
# pipeline writes to the mounted data/uploads and alignment/uploads belongs to
# root on the host, and the person who started the stack cannot delete their own
# results. 1000 is the first user id on a typical Linux host; docker-compose.yml
# passes the real one through if it differs.
#
# That override is the reason /app is handed to group 0 rather than to the user.
# The pipeline writes into /app itself, not only into the mounts: run_config.py
# appends to time.csv before it starts anything, om_database_matching.py writes
# agent.log and om_ontology_to_csv.py writes subgraph.ttl. Owning it as uid 1000
# would leave every one of those failing for anyone whose host id is not 1000.
# Group 0 is added to whatever user compose asks for, so any id can write here.
RUN useradd --create-home --uid 1000 agentom \
    && chown -R agentom:0 /app \
    && chmod -R g=u /app
USER agentom

# stream the pipeline's output instead of holding it in an 8 KB buffer
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

EXPOSE 5000

# 0.0.0.0 so the port can be published; it is still only reachable through
# whatever the host publishes, which docker-compose.yml binds to 127.0.0.1
CMD ["python", "web_app.py", "--host", "0.0.0.0", "--port", "5000"]
