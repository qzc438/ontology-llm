"""Apply the settings chosen in the web interface without editing run_config.py.

run_config.py keeps every setting as a plain module-level assignment, with the
alternatives sitting next to it as comments. This module reads those lines to
build the list of options the web page offers, and then applies the chosen ones
at run time.

Nothing is written back to run_config.py. The chosen settings travel to the
pipeline in the ONTOLOGY_WEB_OVERRIDES environment variable, and an import hook
re-applies them the moment python finishes executing the run_config module, in
every process that imports it. That works because run_config.py derives nothing
from these settings at module level: the folder paths come from `alignment`, and
the settings themselves are only read later by om_ontology_to_csv.py,
om_csv_to_database.py and om_database_matching.py.

It is also the launcher used for the pipeline:

    python web_overrides.py run_config.py

runs run_config.py with the overrides applied. web_app.py puts a `python` on
PATH that points here, so the sub-scripts run_config.py starts are covered too.
"""

import ast
import importlib
import importlib.abc
import importlib.util
import json
import os
import re
import runpy
import sys
from pathlib import Path

# the module whose settings are overridden
TARGET_MODULE = "run_config"

# carries the chosen settings to every process in the pipeline
ENVIRONMENT_VARIABLE = "ONTOLOGY_WEB_OVERRIDES"

# Settings that are a plain value rather than a whole statement. vector_length
# is here because it belongs to the chosen embedding model rather than being
# picked on the page: it travels as the number it is, not as a line of source
# synthesized to carry it.
VALUE_SETTINGS = ("context", "o1_is_code", "o2_is_code", "similarity_threshold",
                  "top_k", "num_matches", "vector_length")

# Locations that may be redirected. The two output files so a run does not
# append its scores to the result.csv every run shares, and the database so the
# pipeline can reach a server that is not on localhost, which is what happens
# as soon as postgres is a container of its own. run_config.py writes all three
# as plain assignments, so the import hook can replace them.
PATH_SETTINGS = ("result_path", "cost_path", "connection_string")

# A database URL carries a password, so it is hidden wherever the URL is
# printed. The user is left showing: it is part of what you check when the
# connection is refused, and it is not a secret on its own. A URL with no
# password in it is left exactly as it is.
CREDENTIALS = re.compile(r"(//[^:@/]+):[^@/]*@")

# only these classes are imported by run_config.py, so only these can be offered
LLM_CLASSES = ("ChatOpenAI", "ChatAnthropic", "ChatOllama")
EMBEDDING_CLASSES = ("OpenAIEmbeddings", "OllamaEmbeddings")

# an assignment, whether it is commented out or not
ASSIGNMENT = re.compile(r"^\s*(?:#\s*)?(?P<body>{name}\s*=\s*(?P<value>.+?))\s*$")

# the model identifier inside a constructor call
MODEL_ARGUMENT = re.compile(r"\bmodel(?:_name)?\s*=\s*['\"]([^'\"]+)['\"]")


def _assignment_pattern(name):
    return re.compile(ASSIGNMENT.pattern.format(name=re.escape(name)))


def _is_commented(line):
    return line.lstrip().startswith("#")


def read_source(base_dir):
    try:
        return (Path(base_dir) / "run_config.py").read_text()
    except OSError:
        return ""


def _statement_options(lines, name, classes):
    """Every `name = SomeClass(...)` line in the file, commented out or not.

    Re-using the author's own line keeps the constructor arguments exactly as
    they were written, which matters because the models do not accept the same
    ones, and it means the page can only ever offer code that already exists in
    run_config.py.
    """
    pattern = _assignment_pattern(name)
    options = []
    seen = set()
    for number, line in enumerate(lines):
        match = pattern.match(line)
        if not match:
            continue
        body = match.group("body")
        class_match = re.match(r"\w+\s*=\s*(\w+)\s*\(", body)
        if not class_match or class_match.group(1) not in classes:
            continue
        if body in seen:
            continue
        seen.add(body)
        model = MODEL_ARGUMENT.search(body)
        options.append(
            {
                "statement": body,
                "label": model.group(1) if model else body,
                "provider": class_match.group(1),
                "line": number,
                "active": not _is_commented(line),
            }
        )
    return options


def _vector_length_for(lines, start):
    """The vector_length that belongs to the embeddings line at `start`.

    run_config.py writes each embeddings model with its dimension underneath, so
    the first vector_length at or after the model line is the matching one.
    """
    pattern = _assignment_pattern("vector_length")
    for line in lines[start + 1:]:
        match = pattern.match(line)
        if match:
            try:
                return int(match.group("value"))
            except ValueError:
                return None
    return None


def _literal_options(lines, name):
    """Every string literal assigned to `name`, commented out or not."""
    pattern = _assignment_pattern(name)
    options = []
    seen = set()
    for line in lines:
        match = pattern.match(line)
        if not match:
            continue
        try:
            value = ast.literal_eval(match.group("value"))
        except (ValueError, SyntaxError):
            continue
        if not isinstance(value, str) or value in seen:
            continue
        seen.add(value)
        options.append({"value": value, "active": not _is_commented(line)})
    return options


def active_value(lines, name):
    """The value python would end up with, that is the last live assignment."""
    pattern = _assignment_pattern(name)
    result = None
    for line in lines:
        if _is_commented(line):
            continue
        match = pattern.match(line)
        if match:
            try:
                result = ast.literal_eval(match.group("value"))
            except (ValueError, SyntaxError):
                result = match.group("value")
    return result


def describe(base_dir):
    """What the web page needs: the options to offer and the current values."""
    lines = read_source(base_dir).splitlines()
    if not lines:
        return {"options": {}, "current": {}}

    embeddings = _statement_options(lines, "embeddings_service", EMBEDDING_CLASSES)
    for option in embeddings:
        option["vector_length"] = _vector_length_for(lines, option["line"])

    # the thresholds run_series_similarity.py sweeps, 1.00 down to 0.50
    thresholds = [round(1.00 - 0.05 * step, 2) for step in range(11)]

    llms = _statement_options(lines, "llm", LLM_CLASSES)

    current = {name: active_value(lines, name) for name in VALUE_SETTINGS}
    active_llm = next((item for item in llms if item["active"]), None)
    active_embeddings = next((item for item in embeddings if item["active"]), None)
    current["llm"] = active_llm["statement"] if active_llm else None
    current["embeddings_service"] = active_embeddings["statement"] if active_embeddings else None

    return {
        "options": {
            "llm": llms,
            "embeddings_service": embeddings,
            "context": _literal_options(lines, "context"),
            "similarity_threshold": thresholds,
        },
        "current": current,
    }


def _allowed(data):
    """The name and value of every setting the page is permitted to change.

    Both channels are allow-listed the same way, so what gets applied and what
    gets printed in the header cannot describe different things.
    """
    for channel, permitted in (("values", VALUE_SETTINGS), ("paths", PATH_SETTINGS)):
        for name, value in (data.get(channel) or {}).items():
            if name in permitted:
                yield name, value


def hide_password(url):
    """The same URL with its password replaced, ready to be shown or logged."""
    return CREDENTIALS.sub(r"\1:***@", url)


def readable(name, value):
    """A setting as it should appear in the log, with any password removed."""
    if name == "connection_string" and isinstance(value, str):
        return repr(hide_password(value))
    return repr(value)


def load():
    """The overrides handed down by web_app.py, if any."""
    raw = os.environ.get(ENVIRONMENT_VARIABLE)
    if not raw:
        return {}
    try:
        data = json.loads(raw)
    except ValueError:
        return {}
    return data if isinstance(data, dict) else {}


def apply_to(module, overrides=None):
    """Put the chosen settings onto an already-executed run_config module."""
    data = load() if overrides is None else overrides
    if not data:
        return []
    applied = []
    # whole statements first, they may define names the values refer to
    for statement in data.get("statements", []):
        try:
            exec(compile(statement, "<web interface>", "exec"), module.__dict__)
        except Exception as error:  # keep the run going, but say what happened
            applied.append(f"{statement}  ->  FAILED: {error}")
            continue
        applied.append(statement)
    for name, value in _allowed(data):
        setattr(module, name, value)
        applied.append(f"{name} = {readable(name, value)}")
    return applied


class _Loader(importlib.abc.Loader):
    """Wraps run_config's real loader so the overrides land right after exec."""

    def __init__(self, inner):
        self.inner = inner

    def create_module(self, spec):
        return self.inner.create_module(spec)

    def exec_module(self, module):
        self.inner.exec_module(module)
        apply_to(module)


class _Finder(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname != TARGET_MODULE:
            return None
        # step aside so the normal machinery can locate the real module
        sys.meta_path.remove(self)
        try:
            spec = importlib.util.find_spec(fullname)
        except (ImportError, ValueError):
            spec = None
        finally:
            sys.meta_path.insert(0, self)
        if spec is None or spec.loader is None:
            return None
        spec.loader = _Loader(spec.loader)
        return spec


def install():
    """Make every later `import run_config` come back with the overrides."""
    if not any(isinstance(finder, _Finder) for finder in sys.meta_path):
        sys.meta_path.insert(0, _Finder())


def _main_guard(tree):
    for node in tree.body:
        if not isinstance(node, ast.If):
            continue
        test = ast.dump(node.test)
        if "__name__" in test and "__main__" in test:
            return node
    return None


def run_run_config(path):
    """Run run_config.py with the overrides applied to its own globals too.

    Importing it makes the hook patch it, but the `if __name__ == '__main__'`
    block would then be skipped, and running it as a script would bypass the
    hook and print the unpatched settings. So it is imported first, and its
    main block is executed afterwards against the patched module.
    """
    module = importlib.import_module(TARGET_MODULE)
    try:
        tree = ast.parse(Path(path).read_text(), str(path))
    except (OSError, SyntaxError):
        tree = None
    guard = _main_guard(tree) if tree is not None else None
    if guard is None:
        # the file no longer has a main block, fall back to running it plainly
        runpy.run_path(str(path), run_name="__main__")
        return
    block = ast.Module(body=guard.body, type_ignores=[])
    exec(compile(block, str(path), "exec"), module.__dict__)


def format_overrides(data):
    """The chosen settings as readable lines, without applying anything."""
    return list(data.get("statements", [])) + [
        f"{name} = {readable(name, value)}" for name, value in _allowed(data)
    ]


def main(argv):
    if not argv or argv[0].startswith("-"):
        # not a script invocation, behave like the interpreter itself
        os.execv(sys.executable, [sys.executable, *argv])
    script = argv[0]
    install()
    sys.argv = list(argv)
    if Path(script).name == "run_config.py":
        overrides = load()
        if overrides:
            print("Settings chosen in the web interface:")
            for line in format_overrides(overrides):
                print(f"  {line}")
            print()
        run_run_config(script)
    else:
        runpy.run_path(script, run_name="__main__")


if __name__ == "__main__":
    main(sys.argv[1:])
