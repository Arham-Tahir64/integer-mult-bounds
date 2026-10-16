#!/usr/bin/env python3
"""Native Windows evidence for PR3007; no network or source mutation.

Prepared for Arham Tahir with substantial OpenAI Codex assistance. Apache-2.0.
Uses the credited predecessor fixtures; this is not independent human review.
"""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import platform
import re
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[3]
AUDITED_HEAD = "3cb500b743f36e13d21b6a46f126846bf36bad32"
BASELINE = "836b19bfa309ceafbc8ee32a15e8c4b10dde7e11"
ORIENTATION_MAIN = "d8e0f83f00191df62174b641e9fff055c357f641"
TEST = "tests/test_research_git_spelling.py"
PACKAGE = "research/replay-input-head-spelling"


def require(condition, message):
    if not condition:
        raise ValueError(message)


def git(root, *args):
    return subprocess.check_output(["git", *args], cwd=root, stderr=subprocess.PIPE, timeout=30)


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def capture(argv, env, temporary):
    result = subprocess.run(argv, cwd=ROOT, env=env, capture_output=True, timeout=180)
    def clean(raw):
        return raw.decode("utf-8", "backslashreplace").replace(str(ROOT), "<ROOT>").replace(
            str(temporary), "<TEMP>").replace(sys.executable, "<PYTHON>")
    return {"returncode": result.returncode, "stdout": clean(result.stdout), "stderr": clean(result.stderr)}


def boundary_probe(old, live):
    # Reuse the original complete source-pinned metadata fixture, with its
    # attribution. Additional VERIFY dependencies may be unpinned by contract.
    sys.path.insert(0, str(ROOT / "tests"))
    try:
        from test_research_onboarding import PackageTests
    finally:
        sys.path.pop(0)
    cases = [("ascii", "src/dep.json", "false")]
    cases += [(form, spelling, setting) for form, spelling in (
        ("NFC", "src/caf\u00e9.json"), ("NFD", "src/cafe\u0301.json"))
        for setting in ("false", "true")]
    records = []
    for form, requested, setting in cases:
        fixture = PackageTests("runTest")
        fixture.setUp()
        try:
            fixture.ready()
            git(fixture.root, "config", "core.precomposeunicode", setting)
            target = fixture.root / requested
            target.parent.mkdir()
            target.write_bytes(b"before\n")
            git(fixture.root, "add", ".")
            git(fixture.root, "-c", "gc.auto=0", "commit", "-qm", "ready")
            names = git(fixture.root, "ls-tree", "-r", "--name-only", "-z", "HEAD").decode("utf-8").split("\0")
            exact = next(name for name in names if name.startswith("src/"))
            base = git(fixture.root, "rev-parse", "HEAD").decode().strip()
            (fixture.root / exact).write_bytes(b"after\n")
            git(fixture.root, "add", ".")
            git(fixture.root, "-c", "gc.auto=0", "commit", "-qm", "target-only")
            require(git(fixture.root, "diff", "--name-only", "-z", base, "HEAD") == exact.encode() + b"\0",
                    "probe must change exactly one target")
            aliases = ("SRC/dep.json", "src/DEP.json", "SRC/DEP.json") if form == "ascii" else (
                "src/cafe\u0301.json" if exact == "src/caf\u00e9.json" else "src/caf\u00e9.json",)
            manifest_path = fixture.target / "VERIFY.json"
            manifest = json.loads(manifest_path.read_bytes())
            for alias in aliases:
                alias_path = fixture.root / alias
                aliases_physically = alias_path.exists() and alias_path.samefile(fixture.root / exact)
                manifest["inputs"] = ["input.txt", alias]
                manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
                try:
                    old.validate(fixture.root, "research/fixture")
                    old_validation = "accepted"
                except ValueError as error:
                    require("missing or external file" in str(error), "unexpected baseline validation failure")
                    old_validation = "missing-file"
                require((old_validation == "accepted") == aliases_physically, "volume and metadata disagree")
                require(old.plan(fixture.root, [exact]) == [], "baseline omission differs")
                for operation in (lambda: live.validate(fixture.root, "research/fixture"),
                                  lambda: live.plan(fixture.root, [exact])):
                    try:
                        operation()
                    except ValueError as error:
                        require("exact Git-tracked input" in str(error), "wrong rejection boundary")
                    else:
                        raise ValueError("alias was accepted by repaired boundary")
                records.append({"requested_form": form, "core.precomposeunicode": setting,
                                "tracked": exact, "alias": alias, "aliases_physically": aliases_physically,
                                "old_full_metadata": old_validation, "old_plan": [],
                                "repaired_validation": "exact-Git rejection", "repaired_plan": "exact-Git rejection"})
            manifest["inputs"] = ["input.txt", exact]
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            for module in (old, live):
                module.validate(fixture.root, "research/fixture")
                require(module.plan(fixture.root, [exact]) == ["research/fixture"], "canonical control differs")
        finally:
            fixture.doCleanups()
    require(len(records) == 7, "probe coverage drift")
    return {"aliases": records, "canonical_full_metadata_and_plan_pairs": 10}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    require(sys.platform == "win32", "this audit requires native Windows")
    require(sys.version_info[:2] == (3, 12), "registered replay requires Python 3.12")
    manifest = json.loads((ROOT / PACKAGE / "VERIFY.json").read_bytes())
    inventory = sorted(set(manifest["inputs"]) | {
        str(p.relative_to(ROOT)).replace("\\", "/") for p in (ROOT / PACKAGE).iterdir() if p.is_file()})
    source_rows = []
    for name in inventory:
        original = git(ROOT, "show", AUDITED_HEAD + ":" + name)
        working = (ROOT / name).read_bytes()
        require(name == TEST or original == working, "unexpected audited source change: " + name)
        source_rows.append({"path": name, "audited_sha256": hashlib.sha256(original).hexdigest(),
                            "working_sha256": hashlib.sha256(working).hexdigest()})
    require(len(source_rows) == 13, "published source inventory drift")
    baseline_raw = git(ROOT, "show", BASELINE + ":scripts/research_package.py")
    require(hashlib.sha256(baseline_raw).hexdigest() ==
            "51e8ee72b1c99de7060c4cc83aabcc54ff1a572bad31f31a6d0102dcc0aae0aa", "baseline hash drift")
    old_environment = dict(os.environ)
    # Deliberately cover the legacy pipe encoding regardless of the parent shell.
    env = {**old_environment, "PYTHONIOENCODING": "cp1252", "PYTHONUTF8": "0"}
    with tempfile.TemporaryDirectory(prefix="windows-spelling-audit-") as directory:
        temporary = Path(directory)
        # Source hashes do not authenticate an older sibling .pyc file.
        # Keep subsequent proof-relevant imports in a fresh cache namespace.
        sys.dont_write_bytecode = True
        sys.pycache_prefix = str(temporary / "fresh-pycache")
        original_test = temporary / "original_test.py"
        original_test.write_bytes(git(ROOT, "show", AUDITED_HEAD + ":" + TEST))
        launcher = temporary / "launch_original.py"
        launcher.write_text(
            "import importlib.util, pathlib, unittest, sys\n"
            f"s=importlib.util.spec_from_file_location('original_test', {str(original_test)!r})\n"
            "m=importlib.util.module_from_spec(s); s.loader.exec_module(m)\n"
            f"m.ROOT=pathlib.Path({str(ROOT)!r})\n"
            "suite=unittest.defaultTestLoader.loadTestsFromName('GitInputSpellingTests.test_unicode_spelling_is_not_normalized',m)\n"
            "sys.exit(not unittest.TextTestRunner(verbosity=2).run(suite).wasSuccessful())\n", encoding="utf-8")
        before = capture([sys.executable, "-I", "-B", str(launcher)], env, temporary)
        require(before["returncode"] == 1 and "AssertionError" in before["stderr"] and
                "src/cafe" in before["stderr"] and "exact Git-tracked input" in before["stderr"],
                "original Unicode assertion failure did not reproduce")
        repaired = capture([sys.executable, "-B", "scripts/research_package.py", "--package", PACKAGE], env, temporary)
        require(repaired["returncode"] == 0 and "PASS_REGISTERED_RESEARCH_PACKAGE" in repaired["stdout"],
                "repaired registered replay failed: " + json.dumps(repaired))
        require(re.findall(r"Ran (\d+) tests? in", repaired["stderr"]) == ["10", "5"],
                "registered test-count coverage drift")
        require(repaired["stderr"].count("skipped 'Windows forbids control characters in filenames'") == 1,
                "unexpected platform-skip coverage")
        baseline_path = temporary / "baseline.py"
        baseline_path.write_bytes(baseline_raw)
        old, live = load("audit_old", baseline_path), load("audit_live", ROOT / "scripts/research_package.py")
        probe = boundary_probe(old, live)
    receipt = {"schema_version": 1, "orientation_main": ORIENTATION_MAIN, "audited_head": AUDITED_HEAD,
               "baseline_runner": BASELINE, "priority_revision": 6,
               "environment": {"platform": platform.platform(), "machine": platform.machine(),
                               "python": platform.python_version(), "git": git(ROOT, "--version").decode().strip(),
                               "replay_pipe_encoding": "cp1252", "PYTHONUTF8": "0",
                               "temporary_directory": "caller-provided writable Windows workspace"},
               "source_inventory": source_rows, "original_unicode_test": before,
               "repaired_registered_replay": repaired, "native_full_metadata_probe": probe,
               "scope": "Native fixture and test-harness verification; no supplier or theorem replay"}
    args.output.write_text(json.dumps(receipt, indent=2, ensure_ascii=True) + "\n", encoding="utf-8", newline="\n")
    print("PASS_NATIVE_WINDOWS_SPELLING original_failure=1 repaired_tests_run=15 intentional_skips=1 alias_probes=7 canonical_pairs=10")


if __name__ == "__main__":
    main()
