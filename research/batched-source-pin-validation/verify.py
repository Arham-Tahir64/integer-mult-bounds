#!/usr/bin/env python3
"""Compare exact validation decisions and optionally benchmark the same fixture.

Arham Tahir, with substantial OpenAI Codex assistance. Apache-2.0.
"""
import argparse
from contextlib import contextmanager
import hashlib
import importlib.util
import json
from pathlib import Path
import platform
import statistics
import subprocess
import sys
import tempfile
import time
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
BASE = "c5108f0f68d482e5712a8e26a5978d47762dfc16"


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


current = load("current_package", ROOT / "scripts/research_package.py")
reference = type(current)("reference_package")
reference.__file__ = str(ROOT / "scripts/research_package.py")
source = current.git(ROOT, "show", BASE + ":scripts/research_package.py")
pins = json.loads((HERE / "SOURCES.json").read_text())
pin = next(row for row in pins["files"] if row["path"] == "scripts/research_package.py")
current.require(hashlib.sha256(source).hexdigest() == pin["sha256"], "baseline source drift")
exec(compile(source, reference.__file__, "exec"), reference.__dict__)


@contextmanager
def fixture():
    """One fixed 34-source package; binary contents, 32 live inputs, two provenance pins."""
    with tempfile.TemporaryDirectory(prefix="source-pin-fixture-") as tmp:
        root = Path(tmp)
        current.git(root, "init", "-q")
        (root / "docs/research").mkdir(parents=True)
        (root / "certificates").mkdir()
        (root / "inputs").mkdir()
        card = {"id": "fixture", "question": "Validate every exact source pin"}
        catalog = {"tracks": [{"tasks": [card]}]}
        (root / "docs/research/agent-task-catalog.json").write_text(json.dumps(catalog))
        (root / "certificates/selected-result.json").write_text('{}')
        names = ["docs/research/agent-task-catalog.json", "certificates/selected-result.json"]
        for i in range(32):
            name = f"inputs/input-{i:02d}.bin"
            (root / name).write_bytes(bytes(range(256)) * 16 + bytes([i]))
            names.append(name)
        current.git(root, "add", ".")
        current.git(root, "-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid",
                    "-c", "maintenance.auto=false", "-c", "gc.auto=0", "commit", "-qm", "fixture")
        base = current.git(root, "rev-parse", "HEAD").decode().strip()
        rows = [{"path": name, "usage": "input" if name.startswith("inputs/") else "provenance",
                 "git_blob": current.git(root, "rev-parse", base + ":" + name).decode().strip(),
                 "sha256": hashlib.sha256((root / name).read_bytes()).hexdigest()} for name in names]
        target = root / "research/fixture"
        target.mkdir(parents=True)
        task = dict(schema_version=1, task_id="fixture", base_commit=base,
                    original_card=card, scope_status="unchanged", actual_scope=card["question"],
                    bottleneck_link="Review exact evidence sooner", stop_rule="One fixed fixture",
                    outcome="completed", evidence="Exact positive and negative controls",
                    author="Fixture", ai_assistance="OpenAI Codex", open_questions=[],
                    no_open_questions_reason="Fixture only")
        manifest = dict(schema_version=1, status="ready", python="3.12", requirements=[],
                        inputs=names[2:], commands=[dict(argv=["{python}", "fixture.py"],
                        timeout_seconds=1, checks="Fixture only; command is not executed")])
        documents = {"TASK.json": task, "VERIFY.json": manifest,
                     "SOURCES.json": dict(schema_version=1, base_commit=base, files=rows)}
        for name, value in documents.items():
            (target / name).write_text(json.dumps(value))
        (target / "README.md").write_text("## Open next questions\nFixture only.\n")
        yield root, target, documents


def decisions(root, target, documents):
    expected = reference.validate(root, "research/fixture")
    current.require(current.validate(root, "research/fixture") == expected, "validation return differs")
    controls = []
    def reject(label, filename, update):
        original = (target / filename).read_bytes()
        value = json.loads(original)
        update(value)
        (target / filename).write_text(json.dumps(value))
        try:
            for module in (reference, current):
                try:
                    module.validate(root, "research/fixture")
                except (ValueError, subprocess.SubprocessError):
                    pass
                else:
                    raise ValueError(label + " accepted")
            controls.append(label)
        finally:
            (target / filename).write_bytes(original)
    reject("wrong blob", "SOURCES.json", lambda v: v["files"][2].update(git_blob="0" * 40))
    reject("wrong SHA256", "SOURCES.json", lambda v: v["files"][2].update(sha256="0" * 64))
    reject("missing pinned source", "SOURCES.json", lambda v: v["files"][2].update(path="missing.bin", usage="provenance"))
    reject("wrong base", "SOURCES.json", lambda v: v.update(base_commit="0" * 40))
    reject("missing catalogue", "SOURCES.json", lambda v: v["files"].pop(0))
    reject("undeclared live input", "VERIFY.json", lambda v: v["inputs"].pop())
    reject("altered original card", "TASK.json", lambda v: v["original_card"].update(question="different"))
    reject("scope drift", "TASK.json", lambda v: v.update(actual_scope="different"))
    # An earlier successful validation never authorizes later working bytes.
    live = root / "inputs/input-00.bin"
    original = live.read_bytes()
    live.write_bytes(b"drift")
    for module in (reference, current):
        try:
            module.validate(root, "research/fixture")
        except ValueError as exc:
            current.require("working source drift" in str(exc), "wrong drift rejection")
        else:
            raise ValueError("working source drift accepted")
    controls.append("working drift after successful validation")
    live.write_bytes(original)
    historical = root / "docs/research/agent-task-catalog.json"
    historical.write_text('{"new":"priority"}')
    current.require(reference.validate(root, "research/fixture") == current.validate(root, "research/fixture"),
                    "historical catalogue semantics changed")
    return controls


def timed(module, root):
    popen = subprocess.Popen
    calls = []
    def capture(*args, **kwargs):
        calls.append(args[0])
        return popen(*args, **kwargs)
    with patch.object(subprocess, "Popen", side_effect=capture):
        start = time.perf_counter()
        result = module.validate(root, "research/fixture")
        seconds = time.perf_counter() - start
    return seconds, len(calls), result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--benchmark", type=Path, help="write seven alternating-order before/after pairs")
    args = parser.parse_args()
    with fixture() as (root, target, documents):
        controls = decisions(root, target, documents)
        old = timed(reference, root)
        new = timed(current, root)
        current.require(old[1] == 69 and new[1] == 2 and old[2] == new[2], "coverage/process count differs")
        if args.benchmark:
            rows = []
            for i in range(7):
                order = (reference, current) if i % 2 == 0 else (current, reference)
                pair = {"order": ["reference" if m is reference else "batched" for m in order]}
                for module in order:
                    seconds, processes, result = timed(module, root)
                    current.require(result == old[2], "benchmark validation return differs")
                    pair["reference" if module is reference else "batched"] = dict(seconds=seconds, processes=processes)
                rows.append(pair)
            medians = {k: statistics.median(row[k]["seconds"] for row in rows) for k in ("reference", "batched")}
            receipt = dict(base_commit=BASE, fixture="34 pinned sources; 32 binary live inputs of 4097 bytes",
                           python=sys.version, platform=platform.platform(), git=current.git(ROOT, "--version").decode().strip(),
                           source_sha256=pin["sha256"],
                           candidate_checkout_sha256=hashlib.sha256((ROOT / "scripts/research_package.py").read_bytes()).hexdigest(),
                           candidate_git_blob=current.git(ROOT, "hash-object", "--path=scripts/research_package.py", "scripts/research_package.py").decode().strip(),
                           controls=controls, pairs=rows, median_seconds=medians,
                           median_speedup=medians["reference"] / medians["batched"],
                           scope="Metadata/source-pin validation only, not circuit replay or kappa. No timing threshold.")
            args.benchmark.write_text(json.dumps(receipt, indent=2) + "\n")
            print(json.dumps({"median_seconds": medians, "median_speedup": receipt["median_speedup"]}))
    print("PASS_BATCHED_SOURCE_PIN_VALIDATION sources=34 processes=69->2 controls=9")


if __name__ == "__main__":
    main()
