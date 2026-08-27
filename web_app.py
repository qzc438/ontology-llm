"""Web interface for the ontology matching pipeline.

Upload a source, target and reference ontology, press "Start matching", and the
page streams the terminal output of `run_config.py` while it runs.

This is a standalone runner: it does not modify or import run_config.py. It
drives it exactly the way run_series_conference.py and run_series_multifarm.py
already do, by setting the `alignment` environment variable that run_config.py
reads, and then running `python run_config.py` as a subprocess.

Usage:
    python web_app.py                 # http://127.0.0.1:5000
    python web_app.py --port 8080     # pick another port
    python web_app.py --host 0.0.0.0  # expose on the local network

A run is filed the way the OAEI tracks are, <context>/<source>-<target>, with
the time it started on the end:

    Uploads are stored in   data/uploads/conference/cmt-confof-20260827-163210/component/
    Results are written to  alignment/uploads/conference/cmt-confof-20260827-163210/component/

so the alignment recorded in result.csv reads the same way. Everything stays
under uploads/, where it cannot touch the OAEI data shipped in data/ and
alignment/, and the timestamp keeps every run of a pair rather than replacing
the one before it.
"""

import argparse
import atexit
import csv
import io
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import threading
import time
import uuid
import zipfile
from collections import deque

# a pseudo terminal is how the pipeline's colours are kept; none of this exists
# on Windows, where the run still works but arrives without colour
try:
    import fcntl
    import pty
    import struct
    import termios
except ImportError:  # pragma: no cover - Windows
    pty = None
    fcntl = None
    struct = None
    termios = None
from datetime import datetime
from pathlib import Path

from flask import Flask, Response, jsonify, render_template, request, send_file
from werkzeug.utils import secure_filename

import web_overrides

# repository root: run_config.py and the om_*.py scripts live here
BASE_DIR = Path(__file__).resolve().parent

# uploaded ontologies, laid out the way run_config.py expects them
UPLOAD_ROOT = BASE_DIR / "data" / "uploads"
RESULT_ROOT = BASE_DIR / "alignment" / "uploads"

# Uploading and running are separate steps, so files arrive here first and are
# moved into their real folder when a run starts. The name begins with a dot so
# it can never be mistaken for one of the context folders beside it.
STAGING_ROOT = UPLOAD_ROOT / ".staging"

# a staged upload nobody ran is cleared out after this long
STAGING_MAX_AGE = 24 * 60 * 60

# run_config.find_file() only looks for these extensions
ALLOWED_EXTENSIONS = ("xml", "rdf", "owl")

# the two ontologies a run cannot happen without
REQUIRED_UPLOADS = ("source", "target")

# The reference alignment is the ground truth, needed only to score the result.
# om_ontology_to_csv.py calls find_reference() whether or not one was given, and
# that hands the path straight to rdflib, so a run without one would fail on
# rdflib.parse(None). An empty alignment is written instead: it parses, yields no
# cells, and the run proceeds with nothing to score against.
OPTIONAL_UPLOADS = ("reference",)
ALL_UPLOADS = REQUIRED_UPLOADS + OPTIONAL_UPLOADS

EMPTY_ALIGNMENT = """<?xml version='1.0' encoding='utf-8'?>
<rdf:RDF xmlns='http://knowledgeweb.semanticweb.org/heterogeneity/alignment#'
         xmlns:rdf='http://www.w3.org/1999/02/22-rdf-syntax-ns#'
         xmlns:xsd='http://www.w3.org/2001/XMLSchema#'>
<!-- No reference alignment was given for this run, so there is nothing to
     score against. This file exists because the pipeline reads one
     unconditionally; it deliberately contains no cells. -->
<Alignment>
<xml>yes</xml>
<level>0</level>
<type>??</type>
</Alignment>
</rdf:RDF>
"""

# reject upload requests larger than this
MAX_UPLOAD_BYTES = 512 * 1024 * 1024

# output lines kept in memory per job
MAX_LINES = 100000

# seconds an idle stream waits before sending a keep-alive comment
KEEP_ALIVE_SECONDS = 10

# the line run_config.py prints when one of its sub-scripts fails; it keeps
# going afterwards and still exits 0, so this is the only way to notice
SCRIPT_ERROR_PATTERN = re.compile(r"^Error running (\S+\.py):")

# run_config.py reads both of these at import time, unconditionally
API_KEY_NAMES = ("OPENAI_API_KEY", "ANTHROPIC_API_KEY")

# points the pipeline at a postgres that is not the one named in run_config.py,
# which is how the database is reached when it runs as its own container
DB_URL_ENV = "ONTOLOGY_DB_URL"

# the header util.calculate_metrics expects but never writes, because the
# create_document call that would have written it is commented out
RESULT_HEADER = ("LLM", "Alignment", "Precision", "Recall", "F1")
COST_HEADER = ("LLM", "Alignment", "Tokens", "Cost")

# run_config.py writes its timings straight to "time.csv" in the repository
# root, and that path is a literal rather than a setting, so it cannot be
# redirected the way result_path and cost_path are. The rows this run appends
# are copied out afterwards instead.
TIME_CSV = "time.csv"
TIME_HEADER = ("LLM", "Alignment", "Retrieving", "Embedding", "Matching", "Total")

# the files that summarise how the run performed rather than what it matched
PERFORMANCE_FILES = ("result.csv", "time.csv", "cost.csv")

# how much of an ontology name is kept in the job id, so a long one cannot
# produce a path nothing will accept
MAX_NAME_LENGTH = 40

# util.calculate_metrics is called once per stage; the README says the final
# figure is the row whose alignment ends with this one
FINAL_STAGE = "llm_with_agent"

# keys typed on the page, held for this server session unless saved to .env
ENTERED_KEYS = {}
KEYS_LOCK = threading.Lock()

# used to notice that the source files changed after this process started
SERVER_STARTED_AT = time.time()

# files uploaded but not yet run, by upload id
STAGED = {}
STAGING_LOCK = threading.Lock()


class Job:
    """One `python run_config.py` run and the terminal output it produced."""

    def __init__(self, job_id, alignment, uploads, overrides=None):
        self.id = job_id
        self.alignment = alignment
        self.uploads = uploads
        self.overrides = overrides or {}
        self.created_at = time.time()
        self.finished_at = None
        self.returncode = None
        self.error = None
        self.cancelled = False
        self.process = None
        # names of sub-scripts that failed, see failed_scripts below
        self.script_errors = []
        # uploads that were deleted while the run was in progress
        self.vanished = []
        # rows already in the shared time.csv when this job started
        self.time_rows_before = 0
        # what the reader called the two ontologies, empty when they said nothing
        self.ontology_names = {"source": "", "target": ""}
        # whether a reference alignment was given, and so whether this run can
        # be scored at all
        self.has_reference = True
        # where the files live, under uploads, in the OAEI shape
        # <context>/<source>-<target>. It holds a slash, so it cannot double as
        # the identifier, which has to survive being a single URL segment.
        self.folder = job_id
        # `lines` is capped, `total` counts every line ever produced so that a
        # reconnecting browser can ask for output starting at an absolute index
        self.lines = deque(maxlen=MAX_LINES)
        self.total = 0
        self.condition = threading.Condition()

    @property
    def running(self):
        return self.finished_at is None

    @property
    def status(self):
        if self.running:
            return "running"
        if self.cancelled:
            return "cancelled"
        # run_config.py catches a failing sub-script and still exits 0, so the
        # return code alone would report a completely failed run as a success
        if self.error or self.returncode or self.script_errors or self.vanished:
            return "failed"
        return "finished"

    def append(self, text):
        match = SCRIPT_ERROR_PATTERN.match(text)
        with self.condition:
            if match:
                self.script_errors.append(match.group(1))
            self.lines.append(text)
            self.total += 1
            self.condition.notify_all()

    def finish(self, returncode=None, error=None):
        with self.condition:
            self.returncode = returncode
            self.error = error
            self.finished_at = time.time()
            self.condition.notify_all()

    def summary(self):
        return {
            "id": self.id,
            "alignment": self.alignment,
            "folder": self.folder,
            "uploads": self.uploads,
            "ontology_names": dict(self.ontology_names),
            "has_reference": self.has_reference,
            "overrides": web_overrides.format_overrides(self.overrides),
            "status": self.status,
            "script_errors": list(self.script_errors),
            "vanished": list(self.vanished),
            "returncode": self.returncode,
            "error": self.error,
            "created_at": self.created_at,
            "finished_at": self.finished_at,
            "duration": (self.finished_at or time.time()) - self.created_at,
            "total_lines": self.total,
        }


# every job started in this server process
JOBS = {}
JOBS_LOCK = threading.Lock()


def active_job():
    """The job that is currently running, if any.

    The pipeline writes to a single postgres database and to shared CSV files,
    so only one run may be in flight at a time.
    """
    with JOBS_LOCK:
        for job in JOBS.values():
            if job.running:
                return job
    return None


def make_python_shim():
    """A directory holding a `python` that runs the current interpreter.

    run_config.py launches its sub-scripts with a bare `python`, which does not
    exist on systems that only ship `python3`. Putting this directory first on
    PATH makes that call resolve without changing run_config.py.

    This has to be a launcher script rather than a symlink: a venv's `python`
    is itself usually a symlink to the system interpreter, so a symlink to it
    resolves all the way through and the child would start outside the venv,
    without any of the project's packages.

    It goes through web_overrides.py rather than straight to the interpreter so
    that the sub-scripts run_config.py starts also see the chosen settings.
    """
    directory = Path(tempfile.mkdtemp(prefix="ontology-web-"))
    atexit.register(shutil.rmtree, directory, True)
    entry = BASE_DIR / "web_overrides.py"
    if os.name == "nt":
        launcher = directory / "python.bat"
        launcher.write_text(f'@echo off\r\n"{sys.executable}" "{entry}" %*\r\n')
    else:
        launcher = directory / "python"
        launcher.write_text(f'#!/bin/sh\nexec "{sys.executable}" "{entry}" "$@"\n')
        launcher.chmod(0o755)
    return directory


PYTHON_SHIM_DIR = None


def build_environment(job):
    """Environment for the child process.

    `alignment` is the setting run_config.py already reads from the environment.
    The settings chosen on the page travel in ONTOLOGY_WEB_OVERRIDES and are
    applied by web_overrides.py, which never writes to run_config.py.
    """
    environment = os.environ.copy()
    # stream output line by line instead of in 8 KB blocks
    environment["PYTHONUNBUFFERED"] = "1"
    # keep colorama's escape codes, the browser renders them
    environment.pop("NO_COLOR", None)
    environment["FORCE_COLOR"] = "1"
    environment["alignment"] = job.alignment
    # load_dotenv() will not overwrite these, so what is set here is what is used
    for name, (value, _source) in resolve_api_keys().items():
        if value is not None:
            environment[name] = value
    if job.overrides:
        environment[web_overrides.ENVIRONMENT_VARIABLE] = json.dumps(job.overrides)
    else:
        environment.pop(web_overrides.ENVIRONMENT_VARIABLE, None)
    if PYTHON_SHIM_DIR is not None:
        environment["PATH"] = os.pathsep.join(
            [str(PYTHON_SHIM_DIR), environment.get("PATH", "")]
        )
    return environment


def clean_line(text):
    """One line of terminal output as it should be stored.

    A terminal ends its lines with a carriage return before the newline, so
    that one is dropped. Any carriage return left inside the line is the child
    rewriting what it had already written, as a progress counter does, so only
    what follows the last one is kept.
    """
    if text.endswith("\r"):
        text = text[:-1]
    return text.rsplit("\r", maxsplit=1)[-1]


def pump_output(job, descriptor):
    """Forward the child's combined stdout/stderr into the job, line by line."""
    buffer = ""
    while True:
        try:
            chunk = os.read(descriptor, 8192)
        except OSError:
            # a pseudo terminal reports EIO rather than end of file when the
            # child on the other side has gone
            break
        if not chunk:
            break
        buffer += chunk.decode("utf-8", errors="replace")
        *complete, buffer = buffer.split("\n")
        for line in complete:
            job.append(clean_line(line))
        # flush a very long line that has not been terminated yet
        if len(buffer) > 8192:
            job.append(buffer)
            buffer = ""
    if buffer:
        job.append(clean_line(buffer))


def missing_inputs(job):
    """Uploaded ontologies that are no longer on disk.

    run_config.py resolves these with find_file() and passes the result straight
    to rdflib. If a file has gone, find_file() returns None and rdflib raises
    "exactly one of source, location, file or data must be given", which says
    nothing about the real problem.
    """
    component = UPLOAD_ROOT / job.folder / "component"
    gone = []
    for name in REQUIRED_UPLOADS:
        if not any((component / f"{name}.{ext}").is_file() for ext in ALLOWED_EXTENSIONS):
            gone.append(name)
    return gone


def prepare_result_files(job):
    """Create the job's own result.csv and cost.csv, with their headers.

    run_config.py points both at a single file in the repository root that every
    run appends to, so a run's own scores are mixed in with every other run's.
    web_overrides.py redirects them into this job's folder instead. The header
    is written here because util.calculate_metrics only ever appends rows.
    """
    folder = RESULT_ROOT / job.folder / "component"
    folder.mkdir(parents=True, exist_ok=True)
    for name, header in (("result.csv", RESULT_HEADER), ("cost.csv", COST_HEADER)):
        path = folder / name
        if not path.exists():
            with open(path, "w", newline="") as handle:
                csv.writer(handle).writerow(header)
    return {
        "result_path": f"alignment/uploads/{job.folder}/component/result.csv",
        "cost_path": f"alignment/uploads/{job.folder}/component/cost.csv",
    }


def count_time_rows():
    """How many rows the shared time.csv holds right now."""
    try:
        with open(BASE_DIR / TIME_CSV, newline="") as handle:
            return sum(1 for _ in csv.reader(handle))
    except OSError:
        return 0


def write_time_summary(job):
    """Copy this run's timing row out of the shared time.csv into its folder.

    run_config.py appends one row per run to a file every run shares. The rows
    added since this job started are filtered by its own alignment name, so an
    unrelated append cannot be mistaken for this run's.
    """
    try:
        with open(BASE_DIR / TIME_CSV, newline="") as handle:
            rows = list(csv.reader(handle))
    except OSError:
        return
    added = [
        row for row in rows[job.time_rows_before:]
        if len(row) > 1 and job.folder in row[1]
    ]
    if not added:
        return
    path = RESULT_ROOT / job.folder / "component" / TIME_CSV
    try:
        with open(path, "w", newline="") as handle:
            writer = csv.writer(handle)
            writer.writerow(TIME_HEADER)
            writer.writerows(added)
    except OSError:
        pass


def read_metrics(job):
    """The precision, recall and F1 rows this job wrote, best row last."""
    path = RESULT_ROOT / job.folder / "component" / "result.csv"
    if not path.is_file():
        return {"rows": [], "final": None}
    rows = []
    try:
        with open(path, newline="") as handle:
            for row in csv.DictReader(handle):
                stage = (row.get("Alignment") or "").rstrip("/").rsplit("/", 1)[-1]
                try:
                    rows.append(
                        {
                            "llm": row.get("LLM"),
                            "stage": stage,
                            "precision": float(row["Precision"]),
                            "recall": float(row["Recall"]),
                            "f1": float(row["F1"]),
                        }
                    )
                except (TypeError, ValueError, KeyError):
                    continue
    except OSError:
        return {"rows": [], "final": None}
    # the last llm_with_agent row is the headline figure; fall back to the last
    # row so a partial run still shows whatever it managed to measure
    final = next((row for row in reversed(rows) if row["stage"] == FINAL_STAGE), None)
    return {"rows": rows, "final": final or (rows[-1] if rows else None)}


def start_process(job, command):
    """Start the pipeline and return the descriptor its output arrives on.

    The output goes through a pseudo terminal rather than a plain pipe. util.py
    calls colorama.init(), and colorama removes its own escape codes when
    stdout is not a terminal, which a pipe is not, so every colour the pipeline
    prints would be stripped before it ever reached the page. A pseudo terminal
    is a terminal as far as that check is concerned, and the colours survive.

    Returns the descriptor to read, and the one to close afterwards, if any.
    """
    settings = dict(
        cwd=str(BASE_DIR),
        env=build_environment(job),
        stdin=subprocess.DEVNULL,
        # own process group, so Stop also kills the om_*.py sub-scripts
        start_new_session=True,
    )
    if pty is None:
        # Windows has no pty module; the run still works, without colour
        job.process = subprocess.Popen(
            command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, **settings
        )
        return job.process.stdout.fileno(), None

    reader, writer = pty.openpty()
    widen(writer)
    try:
        job.process = subprocess.Popen(
            command, stdout=writer, stderr=writer, **settings
        )
    finally:
        # the child holds the only copy that matters now
        os.close(writer)
    return reader, reader


def widen(descriptor):
    """Tell the pseudo terminal it is wide, so nothing wraps at 80 columns."""
    if termios is None:
        return
    try:
        fcntl.ioctl(descriptor, termios.TIOCSWINSZ,
                    struct.pack("HHHH", 50, 200, 0, 0))
    except OSError:
        pass


def run_job(job):
    """Run `python run_config.py` and collect its output."""
    command = [sys.executable, str(BASE_DIR / "web_overrides.py"), "run_config.py"]
    job.time_rows_before = count_time_rows()
    job.append(f"$ alignment={job.alignment} python run_config.py")
    job.append("")
    try:
        descriptor, to_close = start_process(job, command)
    except OSError as error:
        job.append(f"Failed to start run_config.py: {error}")
        job.finish(error=str(error))
        return
    try:
        pump_output(job, descriptor)
        returncode = job.process.wait()
    except Exception as error:  # pragma: no cover - defensive
        job.append(f"Error while reading output: {error}")
        job.finish(error=str(error))
        return
    finally:
        if to_close is not None:
            try:
                os.close(to_close)
            except OSError:
                pass
    # take this run's timings out of the shared file while they are identifiable
    write_time_summary(job)

    # something outside this server deleted the job's files while it was running
    gone = missing_inputs(job)
    if gone and not job.cancelled:
        job.vanished = gone
        job.append("")
        job.append(
            "The uploaded " + ", ".join(gone) + " file(s) disappeared from "
            f"{UPLOAD_ROOT / job.folder / 'component'} while the run was in progress, "
            "so the pipeline was reading files that no longer existed. "
            "Nothing else was wrong with the run; start it again."
        )

    job.append("")
    if job.cancelled:
        job.append("Run stopped by user.")
    elif job.vanished:
        job.append("Run failed because its input files were removed underneath it.")
    elif job.script_errors:
        failed = ", ".join(dict.fromkeys(job.script_errors))
        job.append(f"run_config.py completed, but these steps failed: {failed}")
    elif returncode == 0:
        job.append("run_config.py finished successfully.")
    else:
        job.append(f"run_config.py exited with code {returncode}.")
    job.finish(returncode=returncode)


def stop_job(job):
    """Terminate the child and everything it spawned."""
    process = job.process
    if process is None or process.poll() is not None:
        return False
    job.cancelled = True
    try:
        os.killpg(os.getpgid(process.pid), signal.SIGTERM)
    except (ProcessLookupError, PermissionError):
        process.terminate()

    # give the pipeline a moment to shut down before forcing it
    def force_kill():
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            try:
                os.killpg(os.getpgid(process.pid), signal.SIGKILL)
            except (ProcessLookupError, PermissionError):
                process.kill()

    threading.Thread(target=force_kill, daemon=True).start()
    return True


def as_name(value):
    """An ontology name reduced to what is safe in a folder and a URL.

    The name becomes part of the job id, which is a path segment on disk and in
    every request, so anything outside letters, digits, dot, dash and underscore
    is replaced. An empty result means the run falls back to the plain
    timestamp, which is what happened before names existed.
    """
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "-", (value or "").strip()).strip("-._")
    return cleaned[:MAX_NAME_LENGTH]


def read_uploads(files):
    """Validate what arrived, without writing anything yet.

    Returns the storages keyed by role, or raises ValueError with the message
    the page should show.
    """
    accepted = {}
    for name in ALL_UPLOADS:
        storage = files.get(name)
        if storage is None or not storage.filename:
            if name in REQUIRED_UPLOADS:
                raise ValueError(f"Please choose a {name} ontology file.")
            # the reference is optional; without it the run simply has nothing
            # to score itself against
            continue
        extension = extension_of(storage.filename)
        if extension is None:
            allowed = ", ".join("." + item for item in ALLOWED_EXTENSIONS)
            raise ValueError(
                f"'{storage.filename}' is not a supported {name} file. "
                f"Use one of: {allowed}."
            )
        accepted[name] = (storage, extension)
    return accepted


def clear_old_staging():
    """Forget uploads that were never run."""
    cutoff = time.time() - STAGING_MAX_AGE
    with STAGING_LOCK:
        for upload_id, staged in list(STAGED.items()):
            if staged["created_at"] < cutoff:
                shutil.rmtree(STAGING_ROOT / upload_id, ignore_errors=True)
                STAGED.pop(upload_id, None)
    if STAGING_ROOT.is_dir():
        for path in STAGING_ROOT.iterdir():
            if path.is_dir() and path.name not in STAGED:
                shutil.rmtree(path, ignore_errors=True)


def archive_name(job):
    """A filename for the whole run, from its folder."""
    return job.folder.replace("/", "-") or job.id


def free_folder(relative):
    """The given folder, or the next free one beside it.

    The name already ends in a timestamp taken to the second, so this only
    matters if two runs are somehow started within the same second. It is here
    so that could never quietly write one run over another.
    """
    def taken(candidate):
        return (UPLOAD_ROOT / candidate).exists() or (RESULT_ROOT / candidate).exists()

    if not taken(relative):
        return relative
    for attempt in range(2, 1000):
        candidate = f"{relative}-{attempt}"
        if not taken(candidate):
            return candidate
    # a thousand runs of one pair: fall back to something certainly unused
    return f"{relative}-{uuid.uuid4().hex[:8]}"


def extension_of(filename):
    """The uploaded file's extension, if run_config.py can resolve it."""
    suffix = Path(secure_filename(filename or "")).suffix.lower().lstrip(".")
    return suffix if suffix in ALLOWED_EXTENSIONS else None


def result_files(job):
    """The files this job produced, split into the two groups the page shows.

    "original" is what the matching itself wrote; "performance" is the summary
    of how it went. They are separate because they answer different questions
    and are usually wanted separately.
    """
    folder = RESULT_ROOT / job.folder / "component"
    groups = {"original": [], "performance": []}
    if not folder.is_dir():
        return groups
    for path in sorted(folder.iterdir()):
        if not path.is_file():
            continue
        entry = {
            "name": path.name,
            "size": path.stat().st_size,
            "modified": path.stat().st_mtime,
        }
        if path.name in PERFORMANCE_FILES:
            groups["performance"].append(entry)
        else:
            groups["original"].append(entry)
    # keep the summary in the order it is usually read
    order = {name: index for index, name in enumerate(PERFORMANCE_FILES)}
    groups["performance"].sort(key=lambda item: order.get(item["name"], 99))
    return groups


def read_connection_string():
    """Where the pipeline should look for postgres.

    ONTOLOGY_DB_URL wins when it is set, which is how the database is reached
    when it is a container of its own rather than localhost. Otherwise the URL
    written in run_config.py is used, read as text: importing run_config.py
    would load both ontologies and require an API key, which is far too much
    work for a health check.
    """
    override = os.environ.get(DB_URL_ENV)
    if override:
        return override
    try:
        source = (BASE_DIR / "run_config.py").read_text()
    except OSError:
        return None
    live = [line for line in source.splitlines() if not line.lstrip().startswith("#")]
    matches = re.findall(r"^connection_string\s*=\s*['\"](.+?)['\"]", "\n".join(live), re.M)
    return matches[-1] if matches else None


def parse_settings(form, options):
    """Turn the settings chosen on the page into an overrides payload.

    The statement settings are only accepted when they match a line that is
    already present in run_config.py, so the page can never inject arbitrary
    code, and the model always keeps the constructor arguments its author wrote.
    """
    statements = []
    values = {}
    current = options["current"]
    choices = options["options"]

    chosen = form.get("llm")
    if chosen and chosen != current.get("llm"):
        if not any(item["statement"] == chosen for item in choices["llm"]):
            raise ValueError("That LLM is not one of the options in run_config.py.")
        statements.append(chosen)

    chosen = form.get("embeddings_service")
    if chosen and chosen != current.get("embeddings_service"):
        option = next((item for item in choices["embeddings_service"]
                       if item["statement"] == chosen), None)
        if option is None:
            raise ValueError("That embedding model is not one of the options in run_config.py.")
        statements.append(chosen)
        # the dimension belongs to the model, the database table uses it
        if option.get("vector_length"):
            statements.append(f"vector_length = {option['vector_length']}")

    context = (form.get("context") or "").strip()
    if context and context != current.get("context"):
        if len(context) > 100:
            raise ValueError("The context is too long.")
        values["context"] = context

    for name in ("o1_is_code", "o2_is_code"):
        raw = form.get(name)
        if raw is None or raw == "":
            continue
        if raw not in ("true", "false"):
            raise ValueError(f"{name} must be true or false.")
        value = raw == "true"
        if value != current.get(name):
            values[name] = value

    raw = form.get("similarity_threshold")
    if raw:
        try:
            threshold = float(raw)
        except ValueError as error:
            raise ValueError("The similarity threshold must be a number.") from error
        if not 0.0 <= threshold <= 1.0:
            raise ValueError("The similarity threshold must be between 0 and 1.")
        if threshold != current.get("similarity_threshold"):
            values["similarity_threshold"] = threshold

    for name, limit in (("top_k", 1000), ("num_matches", 1000000)):
        raw = form.get(name)
        if not raw:
            continue
        try:
            number = int(raw)
        except ValueError as error:
            raise ValueError(f"{name} must be a whole number.") from error
        if not 1 <= number <= limit:
            raise ValueError(f"{name} must be between 1 and {limit}.")
        if number != current.get(name):
            values[name] = number

    payload = {}
    if statements:
        payload["statements"] = statements
    if values:
        payload["values"] = values
    return payload


def check_database(url):
    """Whether the pipeline's postgres database is reachable."""
    if not url:
        return {"ok": False, "detail": "no connection_string found in run_config.py"}
    masked = re.sub(r"//[^@/]+@", "//***@", url)
    try:
        import psycopg2
    except ImportError:
        return {"ok": False, "detail": "psycopg2 is not installed"}
    try:
        connection = psycopg2.connect(url, connect_timeout=3)
    except Exception as error:
        message = str(error).strip()
        return {"ok": False, "detail": message.splitlines()[0] if message else "connection failed"}
    try:
        with connection.cursor() as cursor:
            cursor.execute("select extname from pg_extension where extname = 'vector'")
            has_vector = cursor.fetchone() is not None
    finally:
        connection.close()
    if not has_vector:
        return {"ok": False, "detail": f"{masked} is reachable, but pgvector is not installed"}
    return {"ok": True, "detail": masked}


def env_file_values():
    """The contents of .env, or nothing if it cannot be read."""
    try:
        import dotenv

        return dotenv.dotenv_values(BASE_DIR / ".env")
    except ImportError:
        return {}


def resolve_api_keys():
    """Each key's value and where it came from, newest source first.

    A key typed on the page beats .env, which beats the server's own
    environment. run_config.py calls dotenv.load_dotenv(), which does not
    overwrite variables that are already set, so a key put into the child
    process environment is the one the pipeline ends up using.
    """
    values = env_file_values()
    with KEYS_LOCK:
        entered = dict(ENTERED_KEYS)
    resolved = {}
    for name in API_KEY_NAMES:
        if entered.get(name):
            resolved[name] = (entered[name], "entered on this page")
        elif values.get(name):
            resolved[name] = (values[name], ".env")
        elif os.environ.get(name):
            resolved[name] = (os.environ[name], "server environment")
        else:
            resolved[name] = (None, None)
    return resolved


def check_freshness():
    """Whether this server process is still running the code that is on disk.

    web_app.py is imported once, so editing it changes nothing until the server
    is restarted, and the page can then disagree with the source in a way that
    is very hard to notice.
    """
    # templates and the stylesheet reload on their own, so only this module,
    # which python imports exactly once, needs a restart to take effect
    path = BASE_DIR / "web_app.py"
    started = datetime.fromtimestamp(SERVER_STARTED_AT).strftime("%d %b %Y at %H.%M")
    if path.is_file() and path.stat().st_mtime > SERVER_STARTED_AT:
        return {
            "ok": False,
            "detail": f"started {started}, but web_app.py changed since. "
            "Restart the server to pick the change up.",
        }
    return {"ok": True, "detail": f"started {started}"}


# What the page says beside a key, per source. The server environment is where
# a key arrives from in a container, and naming it there told the reader nothing
# they could act on, so that one just reports that the key is set.
# Only a key read out of .env is worth a word beside it, because that names a
# file to go and edit. A key typed into the page, or handed to the server in
# its environment, gets nothing: the box beside the name already holds it, so
# saying it is there again is noise.
SOURCE_WORDING = {
    ".env": "set from .env",
    "entered on this page": "",
    "server environment": "",
}


def describe_api_keys():
    """What the page shows about the keys, never the keys themselves."""
    resolved = resolve_api_keys()
    keys = []
    for name in API_KEY_NAMES:
        value, source = resolved[name]
        keys.append(
            {
                "name": name,
                "label": name.split("_")[0].title(),
                "configured": value is not None,
                "source": source,
                "shown_as": SOURCE_WORDING.get(source, "") if source else "",
                # The key itself, so the page can show what is in use rather
                # than an empty box. This does put the key in the response, so
                # a server published beyond 127.0.0.1 hands it to anyone who
                # loads the page; the README says so.
                "value": value or "",
            }
        )
    missing = [item["name"] for item in keys if not item["configured"]]
    if missing:
        # worth spelling out, because the run cannot start until it is fixed
        detail = "missing " + ", ".join(missing)
    else:
        detail = ", ".join(f"{item['name']} from {item['source']}" for item in keys)
    return {"ok": not missing, "detail": detail, "missing": missing, "keys": keys}


def store_api_keys(submitted, save_to_env):
    """Keep the keys the user typed, and optionally persist them to .env."""
    cleaned = {}
    for name, raw in submitted.items():
        value = (raw or "").strip()
        if not value:
            # an empty box means "leave whatever is already configured alone"
            continue
        if len(value) > 500 or any(character in value for character in "\r\n"):
            raise ValueError(f"{name} does not look like a valid key.")
        cleaned[name] = value
    if not cleaned:
        return []
    with KEYS_LOCK:
        ENTERED_KEYS.update(cleaned)
    if save_to_env:
        write_env_keys(cleaned)
    return sorted(cleaned)


def write_env_keys(updates):
    """Update .env in place, leaving every other line untouched."""
    path = BASE_DIR / ".env"
    try:
        lines = path.read_text().splitlines()
    except OSError:
        lines = []
    remaining = dict(updates)
    output = []
    for line in lines:
        match = re.match(r"\s*([A-Za-z_][A-Za-z0-9_]*)\s*=", line)
        name = match.group(1) if match else None
        if name in remaining:
            output.append(f"{name}={remaining.pop(name)}")
        else:
            output.append(line)
    for name, value in remaining.items():
        output.append(f"{name}={value}")
    path.write_text("\n".join(output) + "\n")
    try:
        # a file holding secrets should not be readable by everyone
        os.chmod(path, 0o600)
    except OSError:
        pass


app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = MAX_UPLOAD_BYTES
# templates are cached unless this is set, so an edited page would keep serving
# the old markup until the server was restarted
app.config["TEMPLATES_AUTO_RELOAD"] = True
# and the same for the stylesheet
app.config["SEND_FILE_MAX_AGE_DEFAULT"] = 0


@app.get("/")
def index():
    return render_template("index.html")


@app.get("/design-system")
def design_system():
    """The design system notes this interface is built from."""
    return render_template("design_system.html")


@app.get("/api/health")
def health():
    settings = web_overrides.describe(BASE_DIR)
    return jsonify(
        {
            "python": sys.executable,
            "base_dir": str(BASE_DIR),
            "options": settings["options"],
            "current": settings["current"],
            "api_keys": describe_api_keys(),
            "database": check_database(read_connection_string()),
            "server": check_freshness(),
        }
    )


@app.post("/api/keys")
def set_api_keys():
    """Accept keys typed on the page. They are never sent back to the browser."""
    submitted = {name: request.form.get(name) for name in API_KEY_NAMES}
    save_to_env = request.form.get("save_to_env") == "true"
    try:
        updated = store_api_keys(submitted, save_to_env)
    except ValueError as error:
        return jsonify({"error": str(error)}), 400
    except OSError as error:
        return jsonify({"error": f"Could not write .env: {error}"}), 500
    return jsonify(
        {
            "updated": updated,
            "saved_to_env": bool(updated) and save_to_env,
            "api_keys": describe_api_keys(),
        }
    )


@app.get("/api/jobs")
def list_jobs():
    with JOBS_LOCK:
        jobs = [job.summary() for job in JOBS.values()]
    jobs.sort(key=lambda item: item["created_at"], reverse=True)
    return jsonify({"jobs": jobs})


@app.post("/api/uploads")
def create_upload():
    """Take the files and hold them, without starting anything.

    Choosing a file in the page does nothing but name it. This is the step that
    actually sends it, so the two are not confused with one another. The files
    wait in the staging area until a run claims them, at which point they move
    into the folder that run is filed under.
    """
    try:
        accepted = read_uploads(request.files)
    except ValueError as error:
        return jsonify({"error": str(error)}), 400

    clear_old_staging()
    upload_id = datetime.now().strftime("%Y%m%d-%H%M%S") + "-" + uuid.uuid4().hex[:8]
    component = STAGING_ROOT / upload_id / "component"
    stored = {}
    try:
        component.mkdir(parents=True, exist_ok=True)
        for name, (storage, extension) in accepted.items():
            storage.save(str(component / f"{name}.{extension}"))
            stored[name] = {
                "filename": storage.filename,
                "stored_as": f"{name}.{extension}",
                "size": (component / f"{name}.{extension}").stat().st_size,
            }
    except OSError as error:
        shutil.rmtree(STAGING_ROOT / upload_id, ignore_errors=True)
        return jsonify({"error": f"Could not save the uploads: {error}"}), 500

    with STAGING_LOCK:
        STAGED[upload_id] = {
            "created_at": time.time(),
            "files": stored,
            "has_reference": "reference" in accepted,
        }
    return jsonify({"upload_id": upload_id, "files": stored,
                    "has_reference": "reference" in accepted}), 201


@app.post("/api/jobs")
def create_job():
    running = active_job()
    if running is not None:
        return (
            jsonify(
                {
                    "error": "A matching run is already in progress. "
                    "Stop it before starting another one.",
                    "job_id": running.id,
                }
            ),
            409,
        )

    # run_config.py assigns os.environ[name] = os.getenv(name) for both keys, so
    # a missing one is a TypeError several seconds in rather than a clear message
    keys = describe_api_keys()
    if keys["missing"]:
        return (
            jsonify(
                {
                    "error": "Enter " + " and ".join(keys["missing"])
                    + " before starting a run. run_config.py reads both at start-up."
                }
            ),
            400,
        )

    # the files were sent by the Upload step and are waiting to be claimed
    upload_id = (request.form.get("upload_id") or "").strip()
    with STAGING_LOCK:
        staged = STAGED.get(upload_id)
    if staged is None:
        return (
            jsonify({"error": "Upload the ontology files before starting a run."}),
            400,
        )

    try:
        overrides = parse_settings(request.form, web_overrides.describe(BASE_DIR))
    except ValueError as error:
        return jsonify({"error": str(error)}), 400

    # The run is filed the way the OAEI tracks are, <context>/<source>-<target>,
    # so the alignment recorded in result.csv reads conference/cmt-confof rather
    # than something only this interface understands. It sits under uploads/, so
    # it can never touch the OAEI data shipped in data/ and alignment/.
    ontology_names = {
        "source": as_name(request.form.get("source_name")),
        "target": as_name(request.form.get("target_name")),
    }
    for which, value in ontology_names.items():
        if not value:
            return (
                jsonify(
                    {
                        "error": f"Please give the {which} ontology a name. It is what "
                        "the run is filed under and what appears in result.csv."
                    }
                ),
                400,
            )
    pair = "-".join(ontology_names.values())
    context = as_name(request.form.get("context")
                      or web_overrides.describe(BASE_DIR)["current"].get("context"))
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    # the time goes on the end, so every run of a pair keeps its own folder and
    # they sort into the order they were run
    folder = "/".join(part for part in (context, f"{pair}-{stamp}") if part)

    # the identifier stays a single URL segment and stays unique
    job_id = f"{pair}-{stamp}-{uuid.uuid4().hex[:6]}"
    folder = free_folder(folder)
    destination = UPLOAD_ROOT / folder
    names = staged["files"]
    try:
        # The files are already on the server. Moving them is what files the run
        # under the name it was given, and it happens now rather than at upload
        # time because the name depends on the context, which can still change.
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(STAGING_ROOT / upload_id), str(destination))
        if not staged["has_reference"]:
            # stands in for the ground truth the reader did not supply, so the
            # pipeline's unconditional read of it succeeds and finds no cells
            (destination / "component" / "reference.xml").write_text(EMPTY_ALIGNMENT)
    except OSError as error:
        return jsonify({"error": f"Could not place the uploaded files: {error}"}), 500
    with STAGING_LOCK:
        STAGED.pop(upload_id, None)

    job = Job(job_id, f"uploads/{folder}/component/", names, overrides)
    job.folder = folder
    job.ontology_names = ontology_names
    job.has_reference = staged["has_reference"]
    # keep this run's scores in its own folder rather than the shared result.csv
    job.overrides.setdefault("paths", {}).update(prepare_result_files(job))
    # and point it at the database this server was told to use, if any
    database = os.environ.get(DB_URL_ENV)
    if database:
        job.overrides["paths"]["connection_string"] = database
    with JOBS_LOCK:
        JOBS[job_id] = job
    threading.Thread(target=run_job, args=(job,), daemon=True).start()
    return jsonify(job.summary()), 201


@app.get("/api/jobs/<job_id>")
def get_job(job_id):
    job = JOBS.get(job_id)
    if job is None:
        return jsonify({"error": "Unknown job."}), 404
    summary = job.summary()
    summary["results"] = result_files(job)
    summary["metrics"] = read_metrics(job)
    return jsonify(summary)


@app.post("/api/jobs/<job_id>/stop")
def cancel_job(job_id):
    job = JOBS.get(job_id)
    if job is None:
        return jsonify({"error": "Unknown job."}), 404
    stopped = stop_job(job)
    return jsonify({"stopped": stopped, "status": job.status})


@app.get("/api/jobs/<job_id>/output")
def job_output(job_id):
    """Whole-buffer fetch, used when the page is reloaded mid-run."""
    job = JOBS.get(job_id)
    if job is None:
        return jsonify({"error": "Unknown job."}), 404
    with job.condition:
        lines = list(job.lines)
        total = job.total
    return jsonify({"lines": lines, "next_index": total, "status": job.status})


@app.get("/api/jobs/<job_id>/stream")
def job_stream(job_id):
    """Server-sent events carrying every new line of terminal output."""
    job = JOBS.get(job_id)
    if job is None:
        return jsonify({"error": "Unknown job."}), 404
    try:
        start_index = int(request.args.get("from", 0))
    except ValueError:
        start_index = 0

    def generate():
        index = max(start_index, 0)
        while True:
            # collect a batch under the lock, but never yield while holding it
            with job.condition:
                earliest = job.total - len(job.lines)
                if index < earliest:
                    index = earliest
                if index >= job.total and job.running:
                    job.condition.wait(timeout=KEEP_ALIVE_SECONDS)
                    earliest = job.total - len(job.lines)
                    if index < earliest:
                        index = earliest
                batch = list(job.lines)[index - earliest:] if index < job.total else []
                if batch:
                    index = job.total
                finished = not job.running and index >= job.total
            if batch:
                payload = json.dumps({"index": index, "lines": batch})
                yield f"event: output\ndata: {payload}\n\n"
            else:
                yield ": keep-alive\n\n"
            if finished:
                summary = job.summary()
                summary["results"] = result_files(job)
                summary["metrics"] = read_metrics(job)
                yield f"event: done\ndata: {json.dumps(summary)}\n\n"
                return

    return Response(
        generate(),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )


@app.get("/api/jobs/<job_id>/results.zip")
def download_all_results(job_id):
    """Every file this job produced, in one archive.

    The two groups the page shows become two folders inside the archive, so
    the download keeps the same shape as the page.
    """
    job = JOBS.get(job_id)
    if job is None:
        return jsonify({"error": "Unknown job."}), 404
    folder = (RESULT_ROOT / job.folder / "component").resolve()
    if not folder.is_dir():
        return jsonify({"error": "This job produced no files."}), 404

    archive = io.BytesIO()
    written = 0
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as bundle:
        for path in sorted(folder.iterdir()):
            if not path.is_file():
                continue
            group = "performance summary" if path.name in PERFORMANCE_FILES else "original files"
            bundle.write(path, arcname=f"{archive_name(job)}/{group}/{path.name}")
            written += 1
    if not written:
        return jsonify({"error": "This job produced no files."}), 404
    archive.seek(0)
    return send_file(
        archive,
        mimetype="application/zip",
        as_attachment=True,
        download_name=f"{archive_name(job)}.zip",
    )


@app.get("/api/jobs/<job_id>/results/<path:filename>")
def download_result(job_id, filename):
    job = JOBS.get(job_id)
    if job is None:
        return jsonify({"error": "Unknown job."}), 404
    folder = (RESULT_ROOT / job.folder / "component").resolve()
    target = (folder / filename).resolve()
    # never serve anything outside the job's own result folder
    if not target.is_file() or folder not in target.parents:
        return jsonify({"error": "Unknown result file."}), 404
    return send_file(target, as_attachment=True, download_name=target.name)


@app.errorhandler(413)
def too_large(_error):
    limit = MAX_UPLOAD_BYTES // (1024 * 1024)
    return jsonify({"error": f"The upload is larger than {limit} MB."}), 413


def main():
    global PYTHON_SHIM_DIR

    parser = argparse.ArgumentParser(description="Ontology matching web interface.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=5000)
    parser.add_argument("--debug", action="store_true")
    options = parser.parse_args()

    UPLOAD_ROOT.mkdir(parents=True, exist_ok=True)
    # anything left staged belongs to a server that is no longer running
    shutil.rmtree(STAGING_ROOT, ignore_errors=True)
    STAGING_ROOT.mkdir(parents=True, exist_ok=True)
    RESULT_ROOT.mkdir(parents=True, exist_ok=True)
    PYTHON_SHIM_DIR = make_python_shim()
    print(f"Ontology matching web interface: http://{options.host}:{options.port}")
    print(f"Uploads: {UPLOAD_ROOT}")
    print(f"Results: {RESULT_ROOT}")
    # threaded=True keeps the event streams from blocking other requests
    app.run(host=options.host, port=options.port, debug=options.debug, threaded=True)


if __name__ == "__main__":
    main()
