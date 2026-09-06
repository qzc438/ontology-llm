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
import itertools
import json
import os
import re
import shutil
import signal
import socket
import subprocess
import sys
import tempfile
import threading
import time
import urllib.error
import urllib.request
import uuid
import zipfile
from collections import deque
from concurrent.futures import ThreadPoolExecutor

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

from flask import (Flask, Response, jsonify, render_template, request, send_file,
                   send_from_directory)
from werkzeug.utils import secure_filename

import web_overrides
from csv_to_alignment_api import csv_to_alignment_api

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

# above this many lines to send at once, walk the buffer rather than index into
# it: see the batching in the stream below
REPLAY_THRESHOLD = 256

# finished runs kept in memory. Each holds up to MAX_LINES of output, and the
# server is long-lived, so they cannot all be kept. The page only ever reattaches
# to the most recent one.
MAX_JOBS = 50

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

# Points the pipeline at an Ollama that is not on localhost, which is what
# localhost means inside a container. ChatOllama in langchain_community ignores
# OLLAMA_HOST and only takes base_url as an argument, so the chosen statement
# has the argument added to it before it runs.
OLLAMA_URL_ENV = "OLLAMA_URL"
OLLAMA_CLASSES = ("ChatOllama", "OllamaEmbeddings")

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

# the settings this run was given, written once at the start so they are on
# record even for a run that fails part way
SETTINGS_CSV = "settings.csv"

# The run's terminal output, kept beside its results. Until this was written the
# only copy was job.lines, a deque in process memory, so the header web_overrides
# prints — the database URL among it — was gone the moment the server restarted.
#
# Named run.log rather than agent.log because om_database_matching.py already
# writes an agent.log of its own into /app. Two different files sharing a name —
# the matcher's own logging there, everything the terminal showed here — would be
# read as one thing.
RUN_LOG = "run.log"

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

# where this process is listening, worked out once by main()
SERVER_ADDRESS = None

# files uploaded but not yet run, by upload id
STAGED = {}
STAGING_LOCK = threading.Lock()

# Ollama model pulls in progress, by model name
PULLS = {}
PULL_LOCK = threading.Lock()

# Held for the whole of starting a run. The check for one already in progress
# and the registration of the new one have to be a single step, or two requests
# arriving together both find nothing running and both start a pipeline against
# the one database. It is not JOBS_LOCK because the work in between moves the
# uploaded files, and no other request should wait on that.
START_LOCK = threading.Lock()


class Job:
    """One `python run_config.py` run and the terminal output it produced."""

    def __init__(self, job_id, folder, uploads, ontology_names,
                 has_reference, overrides=None):
        self.id = job_id
        # where the files live, under uploads, in the OAEI shape
        # <context>/<source>-<target>. It holds a slash, so it cannot double as
        # the identifier, which has to survive being a single URL segment.
        self.folder = folder
        self.uploads = uploads
        # what the reader called the two ontologies, empty when they said nothing
        self.ontology_names = ontology_names
        # whether a reference alignment was given, and so whether this run can
        # be scored at all
        self.has_reference = has_reference
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
        # `lines` is capped, `total` counts every line ever produced so that a
        # reconnecting browser can ask for output starting at an absolute index
        self.lines = deque(maxlen=MAX_LINES)
        self.total = 0
        self.condition = threading.Condition()
        # the same output written straight to disk. `lines` is capped for the
        # browser, so a long run loses its beginning — including the settings
        # header — and that is exactly the part worth keeping.
        self.log = None

    @property
    def alignment(self):
        """What run_config.py is given in the environment, which is the folder
        again as a relative path. Derived rather than stored, so it cannot name
        a different run than `folder` does."""
        return f"uploads/{self.folder}/component/"

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

    def open_log(self, path):
        """Start writing this run's output to `path` as well as to memory.

        Line buffered, so the log on disk is current if the server is killed
        rather than shut down.
        """
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            self.log = open(path, "w", buffering=1)
        except OSError:
            self.log = None

    def close_log(self):
        """Close the log if it is open. Safe to call more than once."""
        with self.condition:
            if self.log is None:
                return
            try:
                self.log.close()
            except OSError:
                pass
            self.log = None

    def append(self, text):
        match = SCRIPT_ERROR_PATTERN.match(text)
        with self.condition:
            if match:
                self.script_errors.append(match.group(1))
            self.lines.append(text)
            self.total += 1
            # written here rather than rebuilt from `lines` at the end, which
            # would only ever hold the last MAX_LINES of a long run
            if self.log is not None:
                try:
                    self.log.write(text + "\n")
                except OSError:
                    self.log = None
            self.condition.notify_all()

    def finish(self, returncode=None, error=None):
        with self.condition:
            self.returncode = returncode
            self.error = error
            self.finished_at = time.time()
            self.condition.notify_all()
        self.close_log()

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


def upload_folder(job):
    """Where this run's ontologies were put."""
    return UPLOAD_ROOT / job.folder / "component"


def result_folder(job):
    """Where this run's own result files are written.

    The pipeline calls it `component` under the alignment folder, which is the
    layout the OAEI tracks already use, so a web run is filed the same way the
    repository's own results are.
    """
    return RESULT_ROOT / job.folder / "component"


def missing_inputs(job):
    """Uploaded ontologies that are no longer on disk.

    run_config.py resolves these with find_file() and passes the result straight
    to rdflib. If a file has gone, find_file() returns None and rdflib raises
    "exactly one of source, location, file or data must be given", which says
    nothing about the real problem.
    """
    component = upload_folder(job)
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
    folder = result_folder(job)
    folder.mkdir(parents=True, exist_ok=True)
    for name, header in (("result.csv", RESULT_HEADER), ("cost.csv", COST_HEADER)):
        path = folder / name
        if not path.exists():
            with open(path, "w", newline="") as handle:
                csv.writer(handle).writerow(header)
    # relative to the repository root, which is where the pipeline runs, and
    # derived from the folder above so the two cannot name different places
    return {
        f"{name.removesuffix('.csv')}_path":
            (folder / name).relative_to(BASE_DIR).as_posix()
        for name in ("result.csv", "cost.csv")
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
    path = result_folder(job) / TIME_CSV
    try:
        with open(path, "w", newline="") as handle:
            writer = csv.writer(handle)
            writer.writerow(TIME_HEADER)
            writer.writerows(added)
    except OSError:
        pass


def write_alignment_xml(job):
    """Write this run's predict.csv out again as Alignment API RDF/XML.

    The OAEI wants an alignment in that format and the pipeline only writes CSV.
    It is done here rather than in om_database_matching.py so that the matching
    scripts are untouched: a terminal run of run_config.py behaves exactly as it
    did, and only a run started from this interface gains the extra file.
    """
    source = result_folder(job) / "predict.csv"
    if not source.is_file():
        return
    target = source.with_suffix(".xml")
    try:
        csv_to_alignment_api(str(source), str(target), relation="=")
    except Exception as error:  # the run itself succeeded and predict.csv is intact
        job.append(f"Could not write {target.name}: {error}")
        return
    job.append(f"Wrote {target.name}, the same alignment in the Alignment API format.")


def read_metrics(job):
    """The precision, recall and F1 rows this job wrote, best row last."""
    path = result_folder(job) / "result.csv"
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
    # The headline figure is the llm_with_agent row and nothing else. A run that
    # stopped early leaves whatever stages it reached, and the last of those is
    # not the result: showing it as one reports the score of an intermediate
    # stage, source say, as though the matching had finished.
    final = next((row for row in reversed(rows) if row["stage"] == FINAL_STAGE), None)
    # the stage name travels with the figures, so the page can say which stage
    # it is waiting for without spelling it out a second time
    return {"rows": rows, "final": final, "final_stage": FINAL_STAGE}


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
    """Run `python run_config.py` and collect its output.

    Wrapped so that however it ends the job is finished and its log is closed.
    Without that an exception on the way out — a malformed shared time.csv is
    enough — leaves finished_at as None, which means a job that is "running" for
    ever: never deletable, never listed with its buttons, holding a file handle.
    """
    try:
        _run_job(job)
    except Exception as error:  # pragma: no cover - defensive
        job.append(f"The run ended unexpectedly: {error}")
        job.finish(error=str(error))
    finally:
        # finish() closes the log, but only if it was reached at all
        job.close_log()


def _run_job(job):
    command = [sys.executable, str(BASE_DIR / "web_overrides.py"), "run_config.py"]
    job.open_log(result_folder(job) / RUN_LOG)
    if job.cancelled:
        # stopped before this thread got as far as starting anything
        job.append("Stopped before the run began.")
        job.finish()
        return
    job.time_rows_before = count_time_rows()
    job.append(f"$ alignment={job.alignment} python run_config.py")
    job.append("")
    try:
        descriptor, to_close = start_process(job, command)
    except OSError as error:
        job.append(f"Failed to start run_config.py: {error}")
        job.finish(error=str(error))
        return
    # A Stop arriving while the process was starting found job.process still
    # None, so it recorded the cancellation and had nothing to signal. Now that
    # there is something to signal, honour it: without this the reader is told
    # the run stopped while it carries on for hours, holding the database.
    if job.cancelled:
        stop_job(job)
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
            f"{upload_folder(job)} while the run was in progress, "
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
        write_alignment_xml(job)
    else:
        job.append(f"run_config.py exited with code {returncode}.")
    job.finish(returncode=returncode)


def stop_job(job):
    """Terminate the child and everything it spawned."""
    process = job.process
    if process is not None and process.poll() is not None:
        return False
    # Stop can arrive in the moment between the run being registered and the
    # worker thread reaching Popen. Recording the cancellation is what makes it
    # count then: run_job checks it before it starts anything, so the request is
    # honoured rather than quietly dropped.
    job.cancelled = True
    if process is None:
        return True
    try:
        # the whole group, so the om_*.py scripts run_config.py spawned go too;
        # neither call exists on Windows, where terminate() is all there is
        os.killpg(os.getpgid(process.pid), signal.SIGTERM)
    except (AttributeError, ProcessLookupError, PermissionError):
        process.terminate()

    # give the pipeline a moment to shut down before forcing it
    def force_kill():
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            try:
                os.killpg(os.getpgid(process.pid), signal.SIGKILL)
            except (AttributeError, ProcessLookupError, PermissionError):
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
                STAGED.pop(upload_id, None)
    # One sweep does the deleting, so there is a single place in the server that
    # removes an upload: anything on disk that no longer has an entry, which
    # covers both the expired ones just forgotten and any left by an earlier run.
    if STAGING_ROOT.is_dir():
        for path in STAGING_ROOT.iterdir():
            if path.is_dir() and path.name not in STAGED:
                shutil.rmtree(path, ignore_errors=True)


def archive_name(job):
    """A filename for the whole run, from its folder.

    Both callers always have one: a live job takes it from free_folder(), and a
    PastRun is only ever built from a folder that is on disk.
    """
    return job.folder.replace("/", "-")


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

    "input" is what the run was given; "original" is what the matching itself
    wrote; "performance" is the summary of how it went. They are separate
    because they answer different questions and are usually wanted separately.
    """
    folder = result_folder(job)
    groups = {"input": [], "original": [], "performance": [], "settings": []}
    uploads = upload_folder(job)
    if uploads.is_dir():
        for path in sorted(uploads.iterdir()):
            if not path.is_file():
                continue
            info = path.stat()
            groups["input"].append(
                {"name": path.name, "size": info.st_size, "modified": info.st_mtime}
            )
    if not folder.is_dir():
        return groups
    for path in sorted(folder.iterdir()):
        if not path.is_file():
            continue
        info = path.stat()
        entry = {"name": path.name, "size": info.st_size, "modified": info.st_mtime}
        groups[file_group(path.name)].append(entry)
    # keep the summary in the order it is usually read
    order = {name: index for index, name in enumerate(PERFORMANCE_FILES)}
    groups["performance"].sort(key=lambda item: order.get(item["name"], 99))
    # the log goes last: it is the record of the run rather than one of its
    # outputs, and alphabetically it would otherwise lead the group
    groups["original"].sort(key=lambda item: item["name"] == RUN_LOG)
    return groups


def file_group(name):
    """Which group a result file belongs to.

    One classifier for the page and the archive both. They were two, in two
    vocabularies, which is how settings.csv came to be filed under the heading
    the page had stopped using.
    """
    if name == SETTINGS_CSV:
        return "settings"
    if name in PERFORMANCE_FILES:
        return "performance"
    return "original"


# what each group is called inside a downloaded archive
ARCHIVE_FOLDERS = {
    "input": "input files",
    "settings": "hyperparameter files",
    "performance": "scoring files",
    "original": "matching files",
}


def bundle_run(bundle, run):
    """Write one run's files into an open archive. Returns how many.

    The ontologies it was given go in as well as what it produced, under the same
    groups the results panel shows, so an unpacked archive holds the whole run
    rather than only half of it.
    """
    prefix = archive_name(run)
    written = 0
    for folder, group in ((upload_folder(run), "input"), (result_folder(run), None)):
        if not folder.is_dir():
            continue
        for path in sorted(folder.iterdir()):
            if not path.is_file():
                continue
            where = ARCHIVE_FOLDERS[group or file_group(path.name)]
            bundle.write(path, arcname=f"{prefix}/{where}/{path.name}")
            written += 1
    return written


def open_archive():
    """Somewhere to build a zip that is not the server's memory.

    An archive now carries the run's ontologies as well as its results, and an
    upload is allowed to be MAX_UPLOAD_BYTES on its own, so "Download all" over
    a full disk would otherwise allocate the lot at once. A temp file costs a
    little disk for the length of one request and cannot exhaust anything; the
    file is unlinked as soon as it is closed.
    """
    return tempfile.TemporaryFile()


def zip_response(archive, name):
    """Hand a finished archive to the browser, and close it afterwards."""
    archive.seek(0)
    return send_file(
        archive, mimetype="application/zip",
        as_attachment=True, download_name=f"{name}.zip",
    )


def write_settings_csv(job, settings=None):
    """Record the hyperparameters this run used, beside its results.

    Every setting, not only the ones chosen on the page. web_overrides.describe()
    reports what run_config.py would resolve to, and the run's own overrides are
    laid over the top, so a setting left alone is still written down. A file that
    recorded only the differences would say nothing about a run that changed
    nothing, and could not be read back months later without knowing which commit
    of run_config.py was checked out at the time.

    The redirected paths are left out: result_path, cost_path and the database
    URL are how this server files the run, not settings that shaped the matching,
    and the folder they name is the folder this file is sitting in.

    readable() renders the values the same way the header printed into the run
    log does, so the two cannot disagree.
    """
    folder = result_folder(job)
    folder.mkdir(parents=True, exist_ok=True)
    # describe() reads run_config.py through read_source(), which returns "" if
    # the file cannot be read, so this is {} rather than an exception in that case
    # describe() returns llm and embeddings_service as whole assignments and
    # everything else as a value, so each is rendered as it arrives and the dict
    # holds finished strings from there on
    def rendered(name, value):
        # describe() hands back llm and embeddings_service as whole assignments,
        # spaced however run_config.py wrote them, so the name is compared rather
        # than a fixed "name =" prefix
        if isinstance(value, str) and value.partition("=")[0].strip() == name:
            return value.partition("=")[2].strip()
        return web_overrides.readable(name, value)

    if settings is None:
        settings = web_overrides.describe(BASE_DIR)
    current = settings.get("current") or {}
    effective = {name: rendered(name, value) for name, value in current.items()}
    effective.update({
        name: web_overrides.readable(name, value)
        for name, value in (job.overrides.get("values") or {}).items()
    })
    for statement in job.overrides.get("statements") or []:
        name, separator, value = statement.partition("=")
        if separator:
            effective[name.strip()] = value.strip()
    rows = list(effective.items())
    try:
        with open(folder / SETTINGS_CSV, "w", newline="") as handle:
            writer = csv.writer(handle)
            writer.writerow(("Setting", "Value"))
            writer.writerows(rows)
    except OSError:
        pass


class PastRun:
    """A finished run found on disk rather than held in memory.

    result_folder(), result_files(), read_metrics() and archive_name() all only
    ever look at .folder, so a run recovered from disk can be passed to them
    exactly as a live job is, and none of them needed changing.
    """

    def __init__(self, folder):
        self.folder = folder


def run_folder_is_safe(folder):
    """Whether this URL-supplied folder names a real run under the result root.

    The name arrives from the client, so it is resolved and checked to be inside
    the root rather than trusted: "../.." would otherwise reach the repository.
    """
    if not folder or folder.startswith("/"):
        return False
    try:
        target = (RESULT_ROOT / folder).resolve()
    except (OSError, ValueError):
        return False
    root = RESULT_ROOT.resolve()
    return target != root and root in target.parents and (target / "component").is_dir()


def run_is_going(folder):
    """Whether the pipeline is still writing into this run's folder."""
    with JOBS_LOCK:
        return any(job.folder == folder and job.running for job in JOBS.values())


def discover_runs():
    """Every run with a result folder on disk, newest first.

    The main page's results panel is served from JOBS, which is process memory:
    it reattaches to the newest job on a reload, but only that one, it is capped
    at MAX_JOBS, and after a restart every per-file URL 404s while the files sit
    on disk untouched. This reads the folders back instead, so a run outlives the
    process that produced it.
    """
    runs = []
    if not RESULT_ROOT.is_dir():
        return runs
    for context in sorted(RESULT_ROOT.iterdir()):
        if not context.is_dir() or context.name.startswith("."):
            continue
        for entry in sorted(context.iterdir()):
            component = entry / "component"
            if not component.is_dir():
                continue
            folder = f"{context.name}/{entry.name}"
            run = PastRun(folder)
            metrics = read_metrics(run)
            # counted across both folders because bundle_run archives both: a
            # run that died before writing results still has its ontologies, and
            # the button must not be disabled over an archive with files in it
            files = [
                path
                for folder in (component, upload_folder(run))
                if folder.is_dir()
                for path in folder.iterdir()
                if path.is_file()
            ]
            try:
                modified = component.stat().st_mtime
            except OSError:
                modified = 0
            runs.append({
                "folder": folder,
                "context": context.name,
                "name": entry.name,
                "modified": modified,
                "files": len(files),
                # None when the run never reached the final stage, which the
                # page shows as a dash rather than inventing a zero
                "final": metrics.get("final"),
                # a run being written to cannot be deleted, and the page leaves
                # the button out rather than offering one that gets refused
                "running": run_is_going(folder),
            })
    runs.sort(key=lambda item: item["modified"], reverse=True)
    return runs


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
        lines = web_overrides.read_source(BASE_DIR).splitlines()
    except OSError:
        return None
    return web_overrides.active_value(lines, "connection_string")


def full_summary(job):
    """Everything the page shows about a finished run.

    Both the job endpoint and the stream's closing event send this, so a field
    added here reaches a reader whether they waited for the run or came back to
    it afterwards.
    """
    summary = job.summary()
    summary["results"] = result_files(job)
    summary["metrics"] = read_metrics(job)
    return summary


# the class being constructed on the right of an assignment
CONSTRUCTED = re.compile(r"=\s*(\w+)\s*\(")


def uses_ollama(statement):
    """Whether this assignment builds one of the Ollama classes.

    Matched on the name being called rather than on a fixed amount of space
    around it, so a line written `llm=ChatOllama(...)` is recognised too.
    """
    found = CONSTRUCTED.search(statement)
    return bool(found) and found.group(1) in OLLAMA_CLASSES


def with_base_url(statement, url):
    """The same assignment, told where Ollama is.

    The statement is one of run_config.py's own lines, already matched against
    the file, so the only thing being added here is the argument.
    """
    # Some of these lines carry a trailing comment, so the argument goes in
    # before the last bracket rather than at the end of the line.
    opened = statement.find("(")
    closed = statement.rfind(")")
    if opened == -1 or closed < opened:
        return statement
    inner = statement[opened + 1:closed].strip().rstrip(",")
    if "base_url" in inner:
        return statement
    joined = f"{inner}, base_url={url!r}" if inner else f"base_url={url!r}"
    return statement[:opened + 1] + joined + statement[closed:]


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

    for name, complaint in (
        ("llm", "That LLM is not one of the options in run_config.py."),
        ("embeddings_service",
         "That embedding model is not one of the options in run_config.py."),
    ):
        chosen = form.get(name)
        if not chosen or chosen == current.get(name):
            continue
        option = next((item for item in choices[name]
                       if item["statement"] == chosen), None)
        if option is None:
            raise ValueError(complaint)
        statements.append(chosen)
        # the dimension belongs to the model, the database table uses it
        if option.get("vector_length"):
            values["vector_length"] = option["vector_length"]

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

    # An Ollama model has to be told where Ollama is, and localhost is not it
    # once this is running in a container. This covers the model that is
    # already selected in run_config.py as well as one chosen on the page,
    # since the first produces no statement of its own.
    ollama_url = os.environ.get(OLLAMA_URL_ENV)
    if ollama_url:
        for setting in ("llm", "embeddings_service"):
            effective = form.get(setting) or current.get(setting) or ""
            if not uses_ollama(effective):
                continue
            statements = [item for item in statements if not item.startswith(f"{setting} =")]
            statements.append(with_base_url(effective, ollama_url))

    payload = {}
    if statements:
        payload["statements"] = statements
    if values:
        payload["values"] = values
    return payload


def ollama_url():
    """Where Ollama is expected to be answering."""
    return (os.environ.get(OLLAMA_URL_ENV) or "http://localhost:11434").rstrip("/")


def ollama_models(statements):
    """The Ollama models named by these assignments, if any."""
    wanted = []
    for statement in statements:
        if statement and uses_ollama(statement):
            match = web_overrides.MODEL_ARGUMENT.search(statement)
            if match:
                wanted.append(match.group(1))
    return wanted


def ollama_request(path, payload=None):
    """A request to Ollama, built the one way. Send it with urlopen.

    Only the addressing lives here. Each caller keeps its own error handling,
    which genuinely differs: the health check swallows everything, the pre-run
    probe wants the body of an HTTPError, and the pull reads a stream. What they
    should not each decide is where Ollama is and how a JSON body is framed.
    """
    if payload is None:
        return urllib.request.Request(f"{ollama_url()}{path}")
    return urllib.request.Request(
        f"{ollama_url()}{path}", data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"})


def check_ollama(wanted=()):
    """Whether Ollama is answering, and has the models a run is about to use.

    Ollama is not part of the image and neither are its models: they are
    installed on the machine and pulled there. Without this check a run starts,
    spends minutes loading both ontologies, and only then fails on a refused
    connection or a model that was never pulled.
    """
    url = ollama_url()
    try:
        with urllib.request.urlopen(ollama_request("/api/tags"), timeout=5) as response:
            payload = json.load(response)
    except Exception as error:  # any failure here means it cannot be used
        reason = str(error).strip() or error.__class__.__name__
        return {
            "reachable": False,
            "url": url,
            "installed": [],
            "missing": list(wanted),
            # a refused connection, an unknown host and a timeout all mean
            # "no answer", and which one it was is the whole diagnosis
            "reason": reason,
        }

    installed = sorted(
        str(item.get("name", "")) for item in payload.get("models", []) if item.get("name")
    )
    missing = [name for name in wanted if name not in installed]
    return {
        "reachable": True,
        "url": url,
        "installed": installed,
        "missing": missing,
    }


def embeddings_refused(statement):
    """Why this Ollama will not embed with the chosen model, or None if it will.

    The model being installed is not enough. Whether a chat model can produce
    embeddings depends on the Ollama version: 0.15 will do it for llama3:8b and
    0.33 refuses, and both report the same capabilities for it, so the answer
    cannot be worked out from what the model says about itself. The only honest
    test is to ask for one embedding and see what comes back.

    It costs one short request, and loading the model, which the run is about to
    do anyway. Without it the refusal arrives at the first real embedding call,
    where om_csv_to_database.py retries it ten times over about six hours before
    giving up.
    """
    models = ollama_models([statement])
    if not models:
        return None
    model = models[0]
    request_ = ollama_request("/api/embed", {"model": model, "input": "test"})
    try:
        with urllib.request.urlopen(request_, timeout=120) as response:
            answer = json.load(response)
    except urllib.error.HTTPError as error:
        try:
            detail = json.load(error).get("error", "")
        except Exception:
            detail = ""
        return f"{model} cannot be used for embeddings: {detail or error}"
    except Exception:
        # unreachable or too slow: the checks above already cover reachability,
        # so this is not the place to fail a run
        return None
    if not answer.get("embeddings") and not answer.get("embedding"):
        return f"{model} returned no embeddings: {answer.get('error', answer)}"
    return None


def known_ollama_models():
    """Every Ollama model named in run_config.py, pulled or not.

    A pull may only ask for one of these. Passing a model name to Ollama makes
    it fetch from the internet, so the name has to come from the project's own
    file rather than from the request.
    """
    options = web_overrides.describe(BASE_DIR)["options"]
    names = set()
    for group in ("llm", "embeddings_service"):
        for option in options.get(group, []):
            if uses_ollama(option["statement"]):
                names.add(option["label"])
    return names


def pull_ollama_model(model):
    """Ask Ollama to fetch a model, following its progress as it goes."""
    request_ = ollama_request("/api/pull", {"model": model})
    try:
        with urllib.request.urlopen(request_, timeout=None) as response:
            for line in response:
                line = line.strip()
                if not line:
                    continue
                try:
                    update = json.loads(line)
                except ValueError:
                    continue
                if update.get("error"):
                    raise RuntimeError(update["error"])
                with PULL_LOCK:
                    state = PULLS.setdefault(model, {})
                    state["status"] = update.get("status", "")
                    state["completed"] = update.get("completed", 0)
                    state["total"] = update.get("total", 0)
    except Exception as error:
        with PULL_LOCK:
            PULLS.setdefault(model, {}).update(
                {"done": True, "ok": False, "error": str(error)}
            )
        return
    with PULL_LOCK:
        PULLS.setdefault(model, {}).update(
            {"done": True, "ok": True, "status": "ready", "error": None}
        )


def pull_state(model):
    """What to tell the page about a pull, including how far along it is."""
    with PULL_LOCK:
        state = dict(PULLS.get(model) or {})
    if not state:
        return None
    total = state.get("total") or 0
    completed = state.get("completed") or 0
    state["percent"] = round(completed * 100 / total) if total else None
    state["model"] = model
    return state


def check_database(url):
    """Whether the pipeline's postgres database is reachable."""
    if not url:
        return {"ok": False, "detail": "no connection_string found in run_config.py"}
    # the same masking that keeps the password out of the run's log line
    masked = web_overrides.hide_password(url)
    try:
        import psycopg2
    except ImportError:
        return {"ok": False, "detail": "psycopg2 is not installed"}
    try:
        connection = psycopg2.connect(url, connect_timeout=3)
    except Exception as error:
        message = str(error).strip()
        return {"ok": False, "detail": message.splitlines()[0] if message else "connection failed"}
    # A failure here is still only this one check failing. Letting it escape
    # would return 500 for the whole health reply, and the page builds the
    # settings and the key fields from that same reply, so a database that
    # answered and then faltered would leave the reader with an empty form.
    try:
        with connection.cursor() as cursor:
            cursor.execute("select extname from pg_extension where extname = 'vector'")
            has_vector = cursor.fetchone() is not None
    except Exception as error:
        message = str(error).strip()
        return {"ok": False,
                "detail": f"{masked} answered, but "
                          f"{message.splitlines()[0] if message else 'the query failed'}"}
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

    Both modules here are imported once, so editing them changes nothing until
    the server is restarted, and the page can then disagree with the source in a
    way that is very hard to notice.
    """
    # Templates and the stylesheet reload on their own. These two do not: python
    # imports each exactly once. web_overrides.py is included because the server
    # calls describe(), parse_settings() and format_overrides() from its own
    # copy; the pipeline's own processes re-run the file and so do pick an edit
    # up, which is exactly what makes a stale server here easy to miss.
    changed = [
        name for name in ("web_app.py", "web_overrides.py")
        if (BASE_DIR / name).is_file()
        and (BASE_DIR / name).stat().st_mtime > SERVER_STARTED_AT
    ]
    where = SERVER_ADDRESS or "address unknown"
    if changed:
        return {
            "ok": False,
            "detail": f"{where}. {' and '.join(changed)} changed since "
            "this server started; restart it to pick the change up.",
        }
    return {"ok": True, "detail": where}


def server_url(host, port):
    """Where this process is listening, as it would be typed into a browser.

    Worked out once, by main(). Nothing it reads can change afterwards, and in
    a container it opens a socket to find the answer, which is not something to
    repeat on every request that asks where the server is.
    """
    # 0.0.0.0 means every interface, which is not something anyone can type in,
    # so the address of the interface this machine actually answers on is used
    if host in ("0.0.0.0", "::"):
        host = own_address() or host
    return f"http://{host}:{port}"


def own_address():
    """This machine's address on the network it can reach.

    Inside a container that is the container's own address on the docker
    network, which is what you would use to reach it from another container.
    Nothing is sent: connecting a UDP socket only picks the route, and the
    local end of it is the answer.
    """
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as probe:
            probe.connect(("8.8.8.8", 80))
            return probe.getsockname()[0]
    except OSError:
        return None


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


@app.before_request
def refuse_cross_site():
    """Refuse a request another website told the browser to make.

    Listening on 127.0.0.1 keeps other machines out; it does not keep other
    pages out. A form post is a simple request, so any site the reader visits
    while this is running could post to /api/keys and overwrite the keys in
    .env, or start runs, without ever seeing a reply. Browsers say where a
    request came from and that is enough to refuse it.

    Requests with neither header are left alone: curl and the tests send
    neither, and a browser always sends at least one.
    """
    if request.method in ("GET", "HEAD", "OPTIONS"):
        return None
    site = request.headers.get("Sec-Fetch-Site")
    if site is not None and site not in ("same-origin", "same-site", "none"):
        return jsonify({"error": "This request did not come from the interface."}), 403
    origin = request.headers.get("Origin")
    if origin and origin.rstrip("/") != request.host_url.rstrip("/"):
        return jsonify({"error": "This request did not come from the interface."}), 403
    return None


@app.get("/")
def index():
    return render_template("index.html")


@app.get("/design-system")
def design_system():
    """The design system notes this interface is built from."""
    return render_template("design_system.html")


@app.get("/runs")
def runs_page():
    """Runs already on disk, on their own page.

    Separate from the interface rather than a panel inside it: the results panel
    there belongs to the run in front of you, and this is the history behind it.
    """
    return render_template("runs.html")


@app.get("/api/health")
def health():
    settings = web_overrides.describe(BASE_DIR)
    # The database and Ollama checks each wait on a machine that may not answer,
    # three and five seconds respectively, and the page builds its whole settings
    # form from this one reply. They share nothing, so waiting on them one after
    # the other only adds the two silences together.
    with ThreadPoolExecutor(max_workers=2) as pool:
        database = pool.submit(check_database, read_connection_string())
        ollama = pool.submit(check_ollama)
        return jsonify(
            {
                # the version first: it is what decides whether the pipeline's
                # pinned packages will install at all, and the path only says
                # which environment answered
                "python": f"Python {'.'.join(str(part) for part in sys.version_info[:3])}"
                          f", {sys.executable}",
                "base_dir": str(BASE_DIR),
                "options": settings["options"],
                "current": settings["current"],
                "api_keys": describe_api_keys(),
                "database": database.result(),
                "server": check_freshness(),
                # reported whether or not an open model is selected; the page
                # shows it only when one is, since it means nothing otherwise
                "ollama": ollama.result(),
            }
        )


@app.post("/api/keys")
def set_api_keys():
    """Accept keys typed on the page.

    The reply carries the keys now in use, because the page refills its boxes
    from it so that what is shown is what a run would use. They are never
    written to the log, and never leave this machine.
    """
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


@app.post("/api/ollama/pull")
def start_pull():
    """Fetch a model into the Ollama on this machine."""
    model = (request.form.get("model") or "").strip()
    if model not in known_ollama_models():
        return (
            jsonify({"error": "That is not one of the models in run_config.py."}),
            400,
        )
    ollama = check_ollama()
    if not ollama["reachable"]:
        return (
            jsonify(
                {
                    "error": f"Nothing answered at {ollama['url']}. Ollama has to "
                    "be installed and running there, and listening on more than "
                    "127.0.0.1 if this is in Docker: see the open models section "
                    "of DOCKER.md."
                }
            ),
            400,
        )
    with PULL_LOCK:
        running = PULLS.get(model)
        if running and not running.get("done"):
            return jsonify(pull_state(model)), 202
        PULLS[model] = {"status": "starting", "completed": 0, "total": 0,
                        "done": False, "ok": None, "error": None}
    threading.Thread(target=pull_ollama_model, args=(model,), daemon=True).start()
    return jsonify(pull_state(model)), 202


@app.get("/api/ollama/pull")
def read_pull():
    """How a download is getting on, and what is installed now."""
    model = (request.args.get("model") or "").strip()
    state = pull_state(model) if model else None
    # This is polled once a second for as long as a download runs, and listing
    # the installed models means another request to Ollama each time. The list
    # only changes when a download ends, so it is fetched then and not before.
    installed = check_ollama() if state is None or state.get("done") else None
    return jsonify({"pull": state, "ollama": installed})


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
    # Claim the id before a single byte is written. clear_old_staging() removes
    # any directory no entry accounts for, and a second upload arriving while
    # this one is still saving would otherwise sweep away its half-written
    # files. `complete` stays false until they are all on disk, so a run cannot
    # claim an upload that is still arriving either.
    with STAGING_LOCK:
        STAGED[upload_id] = {
            "created_at": time.time(),
            "files": {},
            "has_reference": "reference" in accepted,
            "complete": False,
        }
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
        with STAGING_LOCK:
            STAGED.pop(upload_id, None)
        shutil.rmtree(STAGING_ROOT / upload_id, ignore_errors=True)
        return jsonify({"error": f"Could not save the uploads: {error}"}), 500

    with STAGING_LOCK:
        STAGED[upload_id].update({"files": stored, "complete": True})
    return jsonify({"upload_id": upload_id, "files": stored,
                    "has_reference": "reference" in accepted}), 201


@app.post("/api/jobs")
def create_job():
    with START_LOCK:
        return start_one_job()


def start_one_job():
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

    # An open model runs on the Ollama installed on this machine, with the
    # model pulled there. Neither is part of the image, so check both are
    # actually present before a run spends minutes getting to the first call.
    settings = web_overrides.describe(BASE_DIR)
    chosen = {
        name: request.form.get(name) or settings["current"].get(name) or ""
        for name in ("llm", "embeddings_service")
    }
    # the files were sent by the Upload step and are waiting to be claimed
    upload_id = (request.form.get("upload_id") or "").strip()
    with STAGING_LOCK:
        staged = STAGED.get(upload_id)
        if staged is not None and not staged.get("complete"):
            staged = None
    if staged is None:
        return (
            jsonify({"error": "Upload the ontology files before starting a run."}),
            400,
        )

    try:
        overrides = parse_settings(request.form, settings)
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
    # Last, because it is the only check here that costs anything: it asks
    # Ollama to embed one word, which loads the model. Everything above is a
    # dict lookup, and pressing Start before uploading or before naming the
    # ontologies are the two commonest first attempts, so they answer at once
    # rather than after a model has been pulled into memory.
    wanted = ollama_models(chosen.values())
    if wanted:
        ollama = check_ollama(wanted)
        if not ollama["reachable"]:
            return (
                jsonify(
                    {
                        "error": "An open model was chosen, but nothing answered at "
                        f"{ollama['url']}. Install Ollama on this machine and start "
                        "it, then pull the model."
                    }
                ),
                400,
            )
        if ollama["missing"]:
            first = ollama["missing"][0]
            return (
                jsonify(
                    {
                        "error": f"Ollama has not got {', '.join(ollama['missing'])}. "
                        f"Pull it on this machine first: ollama pull {first}"
                    }
                ),
                400,
            )
        # Present is not the same as usable. Without this the run reaches the
        # first embedding call minutes later, and om_csv_to_database.py then
        # retries a refusal that will never succeed, ten times, for hours.
        refused = embeddings_refused(chosen["embeddings_service"])
        if refused:
            return (
                jsonify(
                    {
                        "error": refused + ". Choose a model built for embeddings, "
                        "such as nomic-embed-text, adding it to run_config.py if "
                        "it is not offered."
                    }
                ),
                400,
            )

    pair = "-".join(ontology_names.values())
    context = as_name(request.form.get("context")
                      or settings["current"].get("context"))
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

    job = Job(job_id, folder, names, ontology_names, staged["has_reference"],
              overrides)
    # keep this run's scores in its own folder rather than the shared result.csv
    job.overrides.setdefault("paths", {}).update(prepare_result_files(job))
    # and point it at the database this server was told to use, if any
    database = os.environ.get(DB_URL_ENV)
    if database:
        job.overrides["paths"]["connection_string"] = database
    write_settings_csv(job, settings)
    with JOBS_LOCK:
        JOBS[job_id] = job
        # keep the newest finished runs and let the rest go, so a server left
        # running for weeks does not hold every line of every run it ever did
        done = sorted((item for item in JOBS.values() if not item.running),
                      key=lambda item: item.created_at)
        for old in done[:max(0, len(done) - MAX_JOBS)]:
            JOBS.pop(old.id, None)
    threading.Thread(target=run_job, args=(job,), daemon=True).start()
    return jsonify(job.summary()), 201


@app.get("/api/jobs/<job_id>")
def get_job(job_id):
    job = JOBS.get(job_id)
    if job is None:
        return jsonify({"error": "Unknown job."}), 404
    return jsonify(full_summary(job))


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
    # A dropped connection is reopened by the browser on its own, and it sends
    # back the id of the last event it saw. Resuming from that rather than from
    # the query string is what stops a reconnect replaying output the reader
    # already has, which for a long run means the whole log a second time.
    resumed = request.headers.get("Last-Event-ID")
    try:
        start_index = int(resumed if resumed is not None
                          else request.args.get("from", 0))
    except ValueError:
        start_index = 0

    def generate():
        index = max(start_index, 0)
        while True:
            # collect a batch under the lock, but never yield while holding it
            with job.condition:
                if index >= job.total and job.running:
                    job.condition.wait(timeout=KEEP_ALIVE_SECONDS)
                # the buffer is capped, so a reader that fell far behind starts
                # again at the oldest line still held rather than at its own
                earliest = job.total - len(job.lines)
                index = max(index, earliest)
                # Indexing a deque costs O(min(i, n - i)), so plucking a few
                # lines off the end is nearly free while doing that for the
                # whole buffer would be quadratic. The usual case is a handful
                # of new lines; a reader starting from the beginning walks it
                # once instead.
                if job.total - index > REPLAY_THRESHOLD:
                    batch = list(itertools.islice(job.lines, index - earliest, None))
                else:
                    batch = [job.lines[position - earliest]
                             for position in range(index, job.total)]
                if batch:
                    index = job.total
                finished = not job.running and index >= job.total
            if batch:
                payload = json.dumps({"index": index, "lines": batch})
                # the id is where a reconnect should pick up from
                yield f"id: {index}\nevent: output\ndata: {payload}\n\n"
            else:
                yield ": keep-alive\n\n"
            if finished:
                yield ("event: done\n"
                       f"data: {json.dumps(full_summary(job))}\n\n")
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

    The groups the page shows become folders inside the archive, so the download
    keeps the same shape as the page.
    """
    job = JOBS.get(job_id)
    if job is None:
        return jsonify({"error": "Unknown job."}), 404
    archive = open_archive()
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as bundle:
        written = bundle_run(bundle, job)
    if not written:
        return jsonify({"error": "This job produced no files."}), 404
    return zip_response(archive, archive_name(job))


def serve_from(folder, filename):
    """One file from inside `folder`, or a 404 — never anything outside it.

    safe_join, inside send_from_directory, drops a filename that climbs out with
    .. or arrives absolute. It does not resolve symlinks, and these folders are
    bind-mounted from the host, so a link dropped in from outside would other-
    wise be followed wherever it points; resolving both ends first refuses that.
    """
    folder = Path(folder).resolve()
    try:
        target = (folder / filename).resolve()
    except (OSError, ValueError):
        return jsonify({"error": "Unknown file."}), 404
    if not target.is_file() or folder not in target.parents:
        return jsonify({"error": "Unknown file."}), 404
    return send_from_directory(folder, filename, as_attachment=True)


@app.get("/api/jobs/<job_id>/results/<path:filename>")
def download_result(job_id, filename):
    job = JOBS.get(job_id)
    if job is None:
        return jsonify({"error": "Unknown job."}), 404
    return serve_from(result_folder(job), filename)


@app.get("/api/runs")
def list_runs():
    """Every run still on disk, so the page can show them after a refresh."""
    return jsonify({"runs": discover_runs()})


@app.get("/api/runs/<path:folder>/results.zip")
def download_run(folder):
    """Every file a past run produced, in one archive.

    The same groups as the live download, so an old run and a fresh one unzip to
    the same shape.
    """
    if not run_folder_is_safe(folder):
        return jsonify({"error": "Unknown run."}), 404
    if run_is_going(folder):
        return jsonify({"error": "That run is still going. Its files are not "
                                 "finished yet."}), 409
    run = PastRun(folder)
    archive = open_archive()
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as bundle:
        written = bundle_run(bundle, run)
    if not written:
        return jsonify({"error": "This run produced no files."}), 404
    return zip_response(archive, archive_name(run))


@app.get("/api/runs.zip")
def download_all_runs():
    """Every run on disk, in one archive.

    Its own path rather than a folder named "all" under /api/runs/, so a real
    run could never shadow it. Each run keeps the two-folder shape it has on its
    own, under a folder named after the run.
    """
    archive = open_archive()
    written = 0
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as bundle:
        for run in discover_runs():
            # a run still being written to would go in half finished
            if run["running"]:
                continue
            written += bundle_run(bundle, PastRun(run["folder"]))
    if not written:
        return jsonify({"error": "There are no runs to download."}), 404
    return zip_response(archive, "agent-om-runs")


@app.delete("/api/runs/<path:folder>")
def delete_run(folder):
    """Remove a past run: its results and the ontologies it was given.

    Both folders go, so nothing is left behind under a name a new run could
    collide with. A run still in progress is refused rather than deleted out
    from under the pipeline writing into it.
    """
    if not run_folder_is_safe(folder):
        return jsonify({"error": "Unknown run."}), 404
    # still checked here as well as on the page: a run can start between the
    # listing being drawn and the button being pressed
    if run_is_going(folder):
        return jsonify({"error": "That run is still going. Stop it first."}), 409

    removed = []
    for root in (RESULT_ROOT, UPLOAD_ROOT):
        target = (root / folder).resolve()
        if root.resolve() not in target.parents or not target.is_dir():
            continue
        try:
            shutil.rmtree(target)
            removed.append(str(target.relative_to(BASE_DIR)))
        except OSError as error:
            return jsonify({"error": f"Could not delete {target.name}: {error}"}), 500
        # an emptied context folder is noise on the next listing
        parent = target.parent
        try:
            if parent != root.resolve() and not any(parent.iterdir()):
                parent.rmdir()
        except OSError:
            pass
    return jsonify({"deleted": removed})


@app.get("/api/jobs/<job_id>/inputs/<path:filename>")
def download_input(job_id, filename):
    """One of the ontologies this run was given."""
    job = JOBS.get(job_id)
    if job is None:
        return jsonify({"error": "Unknown job."}), 404
    return serve_from(upload_folder(job), filename)


@app.errorhandler(413)
def too_large(_error):
    limit = MAX_UPLOAD_BYTES // (1024 * 1024)
    return jsonify({"error": f"The upload is larger than {limit} MB."}), 413


def main():
    global PYTHON_SHIM_DIR, SERVER_ADDRESS

    parser = argparse.ArgumentParser(description="Ontology matching web interface.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=5000)
    parser.add_argument("--debug", action="store_true")
    options = parser.parse_args()
    SERVER_ADDRESS = server_url(options.host, options.port)

    UPLOAD_ROOT.mkdir(parents=True, exist_ok=True)
    # anything left staged belongs to a server that is no longer running
    shutil.rmtree(STAGING_ROOT, ignore_errors=True)
    STAGING_ROOT.mkdir(parents=True, exist_ok=True)
    RESULT_ROOT.mkdir(parents=True, exist_ok=True)
    PYTHON_SHIM_DIR = make_python_shim()
    print(f"Ontology matching web interface: {SERVER_ADDRESS}")
    print(f"Uploads: {UPLOAD_ROOT}")
    print(f"Results: {RESULT_ROOT}")
    # threaded=True keeps the event streams from blocking other requests
    app.run(host=options.host, port=options.port, debug=options.debug, threaded=True)


if __name__ == "__main__":
    main()
