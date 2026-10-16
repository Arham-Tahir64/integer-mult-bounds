"""Native Windows evidence for PR3007; authenticated predecessor fixtures.

Arham Tahir, with substantial OpenAI Codex assistance. Apache-2.0.
Adapted from ToikY's native macOS probe at f35825d5cdc8c918fcb466d66476ae35b534eb05.
Credit Nick Petalas/PR3007, Arham Tahir/PR2994 and the retained runner lineage.
Usage: python -I -B native_probe.py EXACT_PR3007_CHECKOUT [--registered-log FILE]
"""
import argparse
import hashlib
import importlib.util
import json
import os
import platform
import subprocess
import sys
import tempfile
from pathlib import Path

HEAD = "3cb500b743f36e13d21b6a46f126846bf36bad32"
BASE = "836b19bfa309ceafbc8ee32a15e8c4b10dde7e11"
PACKAGE = "research/replay-input-head-spelling"
CASE_ALIASES = ("SRC/dep.json", "src/DEP.json", "SRC/DEP.json")
WIN32_ALIASES = ("src./dep.json", "src/dep.json.", "src/dep.json ")
NFC, NFD = "src/caf\u00e9.json", "src/cafe\u0301.json"


def need(condition, message):
    if not condition:
        raise ValueError(message)


def git(root, *args):
    return subprocess.check_output(["git", *args], cwd=root, stderr=subprocess.PIPE, timeout=30)


def authenticate(root):
    need(git(root, "rev-parse", "HEAD").decode().strip() == HEAD, "wrong audited HEAD")
    manifest = json.loads((root / PACKAGE / "VERIFY.json").read_bytes())
    local = git(root, "ls-tree", "-r", "--name-only", "-z", HEAD, "--", PACKAGE)
    names = sorted(set(manifest["inputs"]) | {n.decode() for n in local.split(b"\0") if n})
    need(len(names) == 13, "unexpected package/input closure")
    rows = {}
    for name in names:
        raw = (root / name).read_bytes()
        need(raw == git(root, "show", HEAD + ":" + name), "working bytes drift: " + name)
        rows[name] = {"git_blob": git(root, "rev-parse", HEAD + ":" + name).decode().strip(),
                      "sha256": hashlib.sha256(raw).hexdigest()}
    return rows


def baseline_module(root, temporary):
    raw = git(root, "show", BASE + ":scripts/research_package.py")
    need(hashlib.sha256(raw).hexdigest() ==
         "51e8ee72b1c99de7060c4cc83aabcc54ff1a572bad31f31a6d0102dcc0aae0aa", "baseline SHA drift")
    path = temporary / "baseline.py"
    path.write_bytes(raw)
    spec = importlib.util.spec_from_file_location("authenticated_baseline", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module, raw


def rejection(validator, root):
    try:
        validator(root, "research/fixture")
    except ValueError as error:
        need("exact Git-tracked input" in str(error), "wrong metadata rejection: " + str(error))
    else:
        raise ValueError("repaired metadata accepted a non-HEAD spelling")


def observations(root, old, old_raw):
    # Source authentication precedes imports. A private cache namespace also
    # prevents pre-existing pyc files from replacing those exact sources.
    sys.path.insert(0, str(root / "tests"))
    from test_research_git_spelling import GitInputSpellingTests
    from test_research_onboarding import PackageTests, package

    unicode_rows, metadata_rows, planner_rows = [], [], []
    canonical_calls = 0
    for mode in ("false", "true"):
        for created_form, created in (("NFC", NFC), ("NFD", NFD)):
            fixture = GitInputSpellingTests("runTest")
            fixture.setUp()
            try:
                fixture.git("config", "core.precomposeunicode", mode)
                for alias in CASE_ALIASES + WIN32_ALIASES:
                    need((fixture.root / alias).samefile(fixture.root / "src/dep.json"),
                         "fixture does not physically alias: " + alias)
                fixture.write(created, b"original unicode\n")
                alternate = NFD if created == NFC else NFC
                need(not (fixture.root / alternate).exists(), "unexpected Unicode normalization on this volume")
                fixture.commit()
                tree = fixture.git("ls-tree", "-r", "--name-only", "-z", "HEAD")
                need(created.encode() + b"\0" in tree and alternate.encode() + b"\0" not in tree,
                     "Git changed the created Unicode spelling")
                fixture.manifest("alpha", [alternate])
                before = fixture.commit()
                fixture.write(created, b"changed unicode\n")
                fixture.commit()
                diff = fixture.git("diff", "--no-renames", "--name-only", "-z", before, "HEAD")
                need(diff == created.encode() + b"\0", "Unicode change was not target-only")
                fixture.rejected(before, alternate)
                fixture.manifest("alpha", [created])
                need(fixture.selected(before) == ["research/alpha"], "exact Unicode consumer missing")
                unicode_rows.append({"mode": mode, "created_form": created_form,
                                     "unicode_alias_exists": False, "case_same_file": True,
                                     "win32_aliases_same_file": list(WIN32_ALIASES),
                                     "head_spelling": created, "diff_nul_hex": diff.hex(),
                                     "alternate_rejected": alternate, "canonical_selected": ["research/alpha"]})
            finally:
                fixture.doCleanups()

            rename = GitInputSpellingTests("runTest")
            rename.setUp()
            try:
                rename.git("config", "core.precomposeunicode", mode)
                rename.test_case_only_rename_selects_both_exact_consumers()
                unicode_rows[-1]["case_rename_selected"] = ["research/alpha", "research/beta"]
                unicode_rows[-1]["case_rename_diff_nul_hex"] = rename.git(
                    "diff", "--no-renames", "--name-only", "-z", "HEAD^", "HEAD").hex()
            finally:
                rename.doCleanups()

            fixture = PackageTests("runTest")
            fixture.setUp()
            try:
                git(fixture.root, "config", "core.precomposeunicode", mode)
                fixture.ready()
                (fixture.root / "src").mkdir()
                (fixture.root / "src/dep.json").write_bytes(b"dependency\n")
                (fixture.root / created).write_bytes(b"unicode\n")
                git(fixture.root, "add", "--all")
                git(fixture.root, "-c", "gc.auto=0", "commit", "-qm", "native dependencies")
                path = fixture.target / "VERIFY.json"
                manifest = json.loads(path.read_bytes())
                for alias in CASE_ALIASES + WIN32_ALIASES + (alternate,):
                    manifest["inputs"] = ["input.txt", alias]
                    path.write_text(json.dumps(manifest), encoding="utf-8")
                    exists = (fixture.root / alias).is_file()
                    if exists:
                        old.validate(fixture.root, "research/fixture")
                    else:
                        try:
                            old.validate(fixture.root, "research/fixture")
                        except ValueError as error:
                            need("missing or external file" in str(error), "unexpected baseline Unicode rejection")
                        else:
                            raise ValueError("baseline accepted an absent Unicode input")
                    rejection(package.validate, fixture.root)
                    metadata_rows.append({"mode": mode, "created_form": created_form, "alias": alias,
                                          "physical_file_exists": exists, "baseline_accepts": exists,
                                          "repair_rejects_at_head_boundary": True})
                manifest["inputs"] = ["input.txt", "src/dep.json", created]
                path.write_text(json.dumps(manifest), encoding="utf-8")
                old.validate(fixture.root, "research/fixture")
                package.validate(fixture.root, "research/fixture")
                canonical_calls += 2
            finally:
                fixture.doCleanups()

    # Extra Windows-specific planner controls: trailing dots and spaces are
    # physically the same file but are distinct strings in Git invalidation.
    fixture = GitInputSpellingTests("runTest")
    fixture.setUp()
    try:
        before = fixture.git("rev-parse", "HEAD").decode().strip()
        fixture.write("src/dep.json", b"changed\n")
        fixture.commit()
        need(fixture.git("diff", "--name-only", "-z", before, "HEAD") == b"src/dep.json\0",
             "Windows alias fixture diff drift")
        live = (root / "scripts/research_package.py").read_bytes()
        for alias in CASE_ALIASES + WIN32_ALIASES:
            fixture.manifest("alpha", [alias])
            fixture.write("scripts/research_package.py", old_raw)
            result = fixture.cli(before)
            need(result.returncode == 0 and json.loads(result.stdout) == {"include": []},
                 "baseline did not reproduce empty-matrix omission")
            fixture.write("scripts/research_package.py", live)
            fixture.rejected(before, alias)
            fixture.manifest("alpha", ["src/dep.json"])
            need(fixture.selected(before) == ["research/alpha"], "canonical Windows consumer missing")
            planner_rows.append({"alias": alias, "same_file": True, "baseline_empty_matrix": True,
                                 "repair_rejects_without_output": True,
                                 "canonical_selected": ["research/alpha"]})
    finally:
        fixture.doCleanups()
    need(len(unicode_rows) == 4 and len(metadata_rows) == 28 and canonical_calls == 8,
         "observation coverage drift")
    return unicode_rows, metadata_rows, planner_rows, canonical_calls


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("checkout", type=Path)
    parser.add_argument("--registered-log", type=Path)
    args = parser.parse_args()
    need(sys.platform == "win32", "native Windows required")
    root = args.checkout.resolve()
    before = authenticate(root)
    if args.registered_log:
        result = subprocess.run([sys.executable, "-X", "utf8", "-B", str(root / "scripts/research_package.py"),
                                 "--package", PACKAGE], cwd=root,
                                env={**os.environ, "PYTHONUTF8": "1", "PYTHONIOENCODING": "utf-8"},
                                capture_output=True, timeout=400)
        args.registered_log.write_bytes(result.stdout + result.stderr)
        need(result.returncode == 0 and b"PASS_REGISTERED_RESEARCH_PACKAGE" in result.stdout,
             "registered replay failed; see requested log")
    with tempfile.TemporaryDirectory(prefix="native-windows-spelling-") as temporary:
        saved_cache = sys.pycache_prefix
        sys.pycache_prefix = str(Path(temporary) / "pycache")
        try:
            old, raw = baseline_module(root, Path(temporary))
            unicode_rows, metadata_rows, planner_rows, canonical_calls = observations(root, old, raw)
        finally:
            sys.pycache_prefix = saved_cache
    need(authenticate(root) == before, "audited source changed during execution")
    report = {"status": "PASS_NATIVE_WINDOWS_HEAD_SPELLING", "head": HEAD, "baseline": BASE,
              "platform": platform.platform(), "machine": platform.machine(),
              "python": platform.python_version(), "git": git(root, "--version").decode().strip(),
              "unicode_and_rename": unicode_rows, "full_metadata_comparisons": metadata_rows,
              "canonical_validator_calls": canonical_calls, "planner_alias_controls": planner_rows,
              "source_bytes_unchanged": True, "fresh_import_cache": True, "source_inventory": before,
              "scope": "Native Windows on this case-insensitive, Unicode-preserving volume. Authenticated author fixtures and an adapted ToikY probe; not a separate verifier or human review. No tracked-name collisions, concurrent-writer, hosted-CI or supplier claim."}
    print(json.dumps(report, indent=2, ensure_ascii=True))


if __name__ == "__main__":
    main()
