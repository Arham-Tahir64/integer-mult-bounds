#!/usr/bin/env python3
"""Validate and replay explicitly registered research packages, never every verify.py.

Douglas Colkitt, with OpenAI Codex assistance. Apache-2.0.
"""
import argparse
from contextlib import contextmanager
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path, PurePosixPath
import re
import signal
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]


def require(ok, message):
    if not ok:
        raise ValueError(message)


def relative_file(root, name):
    path = PurePosixPath(name)
    require(not path.is_absolute() and ".." not in path.parts, "invalid relative path: " + name)
    result = root / name
    require(result.resolve().is_relative_to(root.resolve()) and result.is_file()
            and not result.is_symlink(), "missing or external file: " + name)
    return result


def git(root, *args):
    return subprocess.run(["git", *args], cwd=root, capture_output=True, check=True).stdout


@contextmanager
def source_blobs(root, base, names):
    """Read exact pinned blobs through two Git processes, without caching checks.

    Resolve literal paths with NUL-delimited ls-tree records, then send only
    object IDs to cat-file. Read one blob at a time so memory does not grow
    with the total inventory size. Every validation opens a fresh reader.
    """
    tree = git(root, "--literal-pathspecs", "ls-tree", "-rz", "--full-tree",
               base, "--", *dict.fromkeys(names))
    objects = {}
    for record in tree.split(b"\0"):
        if record:
            metadata, name = record.split(b"\t", 1)
            _, kind, obj = metadata.split()
            objects[name.decode()] = (kind, obj)
    for name in names:
        require(name in objects and objects[name][0] == b"blob",
                "missing source blob: " + name)
    with tempfile.TemporaryFile() as errors:
        process = subprocess.Popen(["git", "cat-file", "--batch"], cwd=root,
                                   stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                   stderr=errors)
        try:
            def read(name):
                obj = objects[name][1]
                process.stdin.write(obj + b"\n")
                process.stdin.flush()
                header = process.stdout.readline().split()
                require(len(header) == 3 and header[:2] == [obj, b"blob"]
                        and header[2].isdigit(), "invalid source blob header: " + name)
                size = int(header[2])
                payload = process.stdout.read(size)
                require(len(payload) == size and process.stdout.read(1) == b"\n",
                        "truncated source blob: " + name)
                return obj.decode(), payload
            yield read
            process.stdin.close()
            code = process.wait()
            if code:
                errors.seek(0)
                raise subprocess.CalledProcessError(code, process.args, stderr=errors.read())
        finally:
            if process.poll() is None:
                process.kill()
            process.wait()
            process.stdout.close()
            if not process.stdin.closed:
                process.stdin.close()


def meaningful(value):
    return isinstance(value, str) and bool(value.strip()) and not re.search(r"\bTODO\b", value, re.I)


def validate(root, package, check_pins=True):
    parts = PurePosixPath(package).parts
    require(len(parts) == 2 and parts[0] == "research" and re.fullmatch(r"[a-z0-9][a-z0-9-]*", parts[1]),
            "package must be research/<slug>")
    data = {}
    for name in ("TASK.json", "SOURCES.json", "VERIFY.json"):
        data[name] = json.loads(relative_file(root, package + "/" + name).read_text())
        require(data[name].get("schema_version") == 1, "unsupported schema: " + name)
    task, sources, manifest = (data[n] for n in ("TASK.json", "SOURCES.json", "VERIFY.json"))
    require(task["scope_status"] in ("unchanged", "refined", "changed"), "declare scope_status")
    for field in ("actual_scope", "bottleneck_link", "stop_rule", "evidence", "author", "ai_assistance"):
        require(meaningful(task.get(field)), "complete TASK field: " + field)
    if task["scope_status"] == "unchanged":
        require(task["actual_scope"] == task["original_card"]["question"],
                "different wording/scope requires refined or changed plus a reason")
    else:
        require(meaningful(task.get("scope_change_reason")), "explain the scope refinement/change")
    require(task["outcome"] in ("partial", "completed", "blocked", "negative-result"), "declare outcome")
    questions = task.get("open_questions")
    require(isinstance(questions, list), "open_questions must be a list")
    if not questions:
        require(meaningful(task.get("no_open_questions_reason")), "explain an empty next-question list")
    for question in questions:
        for field in ("question", "why_it_matters", "first_step", "blocked_by"):
            require(meaningful(question.get(field)), "complete next-question field: " + field)
    readme = relative_file(root, package + "/README.md").read_text()
    require("## Open next questions" in readme, "README needs Open next questions")
    require(manifest.get("status") == "ready", "VERIFY.json is a draft; complete it before requesting replay")
    require(manifest.get("python") == "3.12", "generic replay currently uses Python 3.12")
    requirements = manifest.get("requirements", [])
    require(isinstance(requirements, list) and len(requirements) == len(set(requirements)), "invalid requirements")
    for item in requirements:
        require(re.fullmatch(r"(?:numpy|sympy|scipy)==[0-9]+(?:\.[0-9]+){1,2}", item),
                "generic CI supports exact numpy/sympy/scipy pins; use a dedicated workflow for other environments")
    commands = manifest.get("commands")
    require(isinstance(commands, list) and 1 <= len(commands) <= 8, "declare 1..8 explicit verification commands")
    total = 0
    for command in commands:
        argv = command.get("argv")
        require(isinstance(argv, list) and len(argv) >= 2 and all(isinstance(a, str) for a in argv), "invalid argv")
        require(argv[0] == "{python}", "commands must explicitly use {python}; no implicit shell")
        require(meaningful(command.get("checks")), "describe command coverage")
        seconds = command.get("timeout_seconds")
        require(type(seconds) is int and 1 <= seconds <= 600, "command timeout must be 1..600 seconds")
        total += seconds
    require(total <= 1200, "generic replay has a 1200-second total budget; use a dedicated job for larger checks")
    inputs = manifest.get("inputs")
    require(isinstance(inputs, list), "declare input paths for CI invalidation")
    for name in inputs:
        relative_file(root, name)
    require(sources.get("files"), "empty source inventory")
    require(re.fullmatch(r"[0-9a-f]{40,64}", sources["base_commit"]), "pin an exact base commit")
    require(task["base_commit"] == sources["base_commit"], "TASK and SOURCES base mismatch")
    require(all(r.get("usage") in ("input", "provenance") for r in sources["files"]), "declare source usage")
    require({r["path"] for r in sources["files"] if r["usage"] == "input"} <= set(inputs),
            "all live pinned inputs must be declared CI inputs")
    if check_pins:
        catalog_name = "docs/research/agent-task-catalog.json"
        require(catalog_name in {r["path"] for r in sources["files"]}, "pin the originating task catalogue")
        for row in sources["files"]:
            name = row["path"]
            p = PurePosixPath(name)
            require(not p.is_absolute() and ".." not in p.parts, "invalid source path")
        with source_blobs(root, sources["base_commit"], [r["path"] for r in sources["files"]]) as read:
            for row in sources["files"]:
                name = row["path"]
                obj, pinned = read(name)
                require(obj == row["git_blob"], "source blob provenance mismatch: " + name)
                require(hashlib.sha256(pinned).hexdigest() == row["sha256"], "source SHA256 provenance mismatch: " + name)
                if row["usage"] == "input":
                    require(pinned == relative_file(root, name).read_bytes(), "working source drift: " + name)
                if name == catalog_name:
                    catalog = json.loads(pinned)
        cards = [t for tr in catalog["tracks"] for t in tr["tasks"] if t["id"] == task["task_id"]]
        require(len(cards) == 1 and task["original_card"] == cards[0], "original card does not match pinned catalogue")
    return task, manifest


def run_command(argv, cwd, timeout):
    # A timeout ends the whole local process group, including child solvers.
    process = subprocess.Popen(argv, cwd=cwd, start_new_session=True)
    try:
        code = process.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        os.killpg(process.pid, signal.SIGKILL)
        process.wait()
        raise ValueError("verification timed out")
    require(code == 0, f"verification command exited {code}")


def run_package(root, package, install=False):
    task, manifest = validate(root, package)
    require(sys.version_info[:2] == (3, 12), "run replay with Python 3.12 (metadata check is version-independent)")
    if install and manifest["requirements"]:
        run_command([sys.executable, "-m", "pip", "install", "--disable-pip-version-check", *manifest["requirements"]], root, 300)
    for requirement in manifest["requirements"]:
        name, version = requirement.split("==")
        require(importlib.metadata.version(name) == version, "dependency version mismatch: " + requirement)
    for command in manifest["commands"]:
        argv = [sys.executable if item == "{python}" else item.replace("{package}", package) for item in command["argv"]]
        print("CHECK " + command["checks"], flush=True)
        run_command(argv, root, command["timeout_seconds"])
    print("PASS_REGISTERED_RESEARCH_PACKAGE " + package + " outcome=" + task["outcome"])


def plan(root, changed):
    changed = set(changed)
    packages = []
    for path in sorted((root / "research").glob("*/VERIFY.json")):
        package = path.parent.relative_to(root).as_posix()
        manifest = json.loads(path.read_text())
        # Parse only for selection; validate fully in the isolated replay job.
        inputs = manifest.get("inputs", [])
        if (changed.intersection(inputs) or any(p.startswith(package + "/") for p in changed)
                or "scripts/research_package.py" in changed):
            packages.append(package)
    return packages


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--package")
    ap.add_argument("--check-only", action="store_true")
    ap.add_argument("--install-deps", action="store_true", help="explicit opt-in to install manifest's allowed pinned dependencies")
    ap.add_argument("--changed-since", help="plan affected opt-in packages relative to this Git commit")
    ap.add_argument("--github-output", type=Path)
    args = ap.parse_args()
    try:
        if args.changed_since:
            if set(args.changed_since) == {"0"}:
                changed = git(ROOT, "ls-files", "-z").decode().split("\0")
            else:
                base = git(ROOT, "rev-parse", "--verify", args.changed_since + "^{commit}").decode().strip()
                changed = git(ROOT, "diff", "--name-only", "-z", base, "HEAD").decode().split("\0")
            packages = plan(ROOT, changed)
            matrix = json.dumps({"include": [{"package": p} for p in packages]})
            print(matrix)
            if args.github_output:
                with args.github_output.open("a") as out:
                    out.write(f"matrix={matrix}\ncount={len(packages)}\n")
        elif args.package:
            if args.check_only:
                validate(ROOT, args.package)
                print("PASS_PACKAGE_METADATA_AND_PINS (not a mathematical acceptance check)")
            else:
                run_package(ROOT, args.package, args.install_deps)
        else:
            ap.error("use --package or --changed-since")
    except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError, importlib.metadata.PackageNotFoundError) as exc:
        ap.exit(1, str(exc) + "\n")


if __name__ == "__main__":
    main()
