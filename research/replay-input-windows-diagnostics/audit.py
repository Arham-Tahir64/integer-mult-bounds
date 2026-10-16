#!/usr/bin/env python3
"""Native Windows execution of PR3007 and a narrow test-protocol repair.

Arham Tahir, with substantial OpenAI Codex assistance. Apache-2.0.
Uses Nick Petalas's original fixtures; this is not an independent verifier.
"""
import argparse
from datetime import datetime, timezone
import difflib
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import tempfile

HEAD = "3cb500b743f36e13d21b6a46f126846bf36bad32"
PACKAGE = "research/replay-input-head-spelling"
TEST = "tests/test_research_git_spelling.py"
BASE = "836b19bfa309ceafbc8ee32a15e8c4b10dde7e11"


def require(condition, message):
    if not condition:
        raise ValueError(message)


def git(root, *args):
    result = subprocess.run(["git", *args], cwd=root, capture_output=True, timeout=60, check=False)
    require(result.returncode == 0, "Git failed: " + result.stderr.decode("utf-8", "replace"))
    return result.stdout


def authenticated_files(source):
    require(git(source, "rev-parse", "HEAD").decode().strip() == HEAD, "wrong audited HEAD")
    manifest = json.loads(git(source, "show", HEAD + ":" + PACKAGE + "/VERIFY.json"))
    names = set(manifest["inputs"])
    names.update(git(source, "ls-tree", "-r", "--name-only", "-z", HEAD, "--", PACKAGE)
                 .decode("utf-8").strip("\0").split("\0"))
    pins = []
    for name in sorted(names):
        raw = git(source, "show", HEAD + ":" + name)
        require((source / name).read_bytes() == raw, "working bytes differ: " + name)
        pins.append({"path": name, "sha256": hashlib.sha256(raw).hexdigest(),
                     "git_blob": git(source, "rev-parse", HEAD + ":" + name).decode().strip()})
    return pins


def repaired_test(raw):
    require(raw.count(b"import json\n") == 1, "import patch context drift")
    old = b'cwd=self.root, capture_output=True, text=True, encoding="utf-8", timeout=15, check=False)'
    new = (b'cwd=self.root, capture_output=True, text=True, encoding="utf-8",\n'
           b'            env={**os.environ, "PYTHONIOENCODING": "utf-8"}, timeout=15, check=False)')
    require(raw.count(old) == 1, "subprocess patch context drift")
    return raw.replace(b"import json\n", b"import json\nimport os\n").replace(old, new)


def replay(root, label, encoding, expected_exit, log):
    environment = {**os.environ, "PYTHONIOENCODING": encoding, "PYTHONUTF8": "0"}
    argv = [sys.executable, "-B", "scripts/research_package.py", "--package", PACKAGE]
    result = subprocess.run(argv, cwd=root, env=environment, capture_output=True, timeout=120, check=False)
    log.extend([("\n=== " + label + " ===\n").encode(), result.stdout, result.stderr])
    out, err = result.stdout.decode("utf-8"), result.stderr.decode("utf-8")
    require(result.returncode == expected_exit, label + ": unexpected exit\n" + err)
    require("baseline_omissions=3 repaired_rejections=3 canonical_controls=2" in out,
            label + ": missing differential control")
    require("Windows forbids control characters in filenames" in err, label + ": missing named skip")
    if expected_exit:
        require("test_unicode_spelling_is_not_normalized" in err and
                "AssertionError:" in err and "not found in" in err and
                r"cafe\\u0301.json" in err and "FAILED (failures=1, skipped=1)" in err,
                label + ": unexpected original failure")
    else:
        require("PASS_REGISTERED_RESEARCH_PACKAGE" in out and "Ran 9 tests" in err and
                "OK (skipped=1)" in err and "Ran 5 tests" in err,
                label + ": incomplete registered coverage")
    print("CHECKED", label, "exit=" + str(result.returncode), flush=True)
    return {"label": label, "child_encoding": encoding, "exit": result.returncode,
            "stdout_bytes": len(result.stdout), "stderr_bytes": len(result.stderr),
            "stdout_sha256": hashlib.sha256(result.stdout).hexdigest(),
            "stderr_sha256": hashlib.sha256(result.stderr).hexdigest()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, required=True, help="unmodified sparse checkout of the exact PR3007 head")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    require(sys.platform == "win32", "this audit requires native Windows")
    source = args.source_root.resolve()
    pins = authenticated_files(source)
    log = []
    with tempfile.TemporaryDirectory(prefix="windows-spelling-audit-") as temp:
        temporary = Path(temp)
        checkout = temporary / "source"
        checkout.mkdir()
        git(checkout, "init", "-q")
        # Borrow immutable local objects without a transport process or source mutation.
        common = Path(git(source, "rev-parse", "--path-format=absolute", "--git-common-dir").decode().strip())
        (checkout / ".git/objects/info/alternates").write_bytes(((common / "objects").as_posix() + "\n").encode("utf-8"))
        if (common / "shallow").is_file():
            (checkout / ".git/shallow").write_bytes((common / "shallow").read_bytes())
        git(checkout, "config", "core.autocrlf", "false")
        git(checkout, "sparse-checkout", "set", "scripts", "tests", PACKAGE)
        git(checkout, "checkout", "--detach", HEAD)
        require(authenticated_files(checkout) == pins, "temporary checkout source binding differs")
        runs = [replay(checkout, "original-cp1252", "cp1252", 1, log),
                replay(checkout, "original-utf8", "utf-8", 0, log)]
        require(authenticated_files(checkout) == pins, "source changed during original replays")
        path = checkout / TEST
        original = path.read_bytes()
        fixed = repaired_test(original)
        path.write_bytes(fixed)
        try:
            authenticated_files(checkout)
        except ValueError as error:
            require(str(error) == "working bytes differ: " + TEST, "unexpected source-control rejection")
        else:
            raise ValueError("changed-source control was accepted")
        patch = "".join(difflib.unified_diff(original.decode().splitlines(True), fixed.decode().splitlines(True),
                                            fromfile="a/" + TEST, tofile="b/" + TEST))
        runs.append(replay(checkout, "patched-cp1252", "cp1252", 0, log))
        for pin in pins:
            raw = (checkout / pin["path"]).read_bytes()
            expected = hashlib.sha256(fixed).hexdigest() if pin["path"] == TEST else pin["sha256"]
            require(hashlib.sha256(raw).hexdigest() == expected, "source changed during patched replay: " + pin["path"])
    require(authenticated_files(source) == pins, "original source checkout changed")
    evidence = {"status": "PASS_NATIVE_WINDOWS_AUDIT_WITH_TEST_PROTOCOL_REPAIR",
                "checked_at_utc": datetime.now(timezone.utc).isoformat(), "audited_head": HEAD,
                "historical_baseline": BASE, "platform": platform.platform(), "python": sys.version,
                "native_stdout_encoding": sys.stdout.encoding, "native_stderr_encoding": sys.stderr.encoding,
                "git": git(source, "--version").decode().strip(), "source_files": pins,
                "registered_runs": runs,
                "changed_source_rejected": TEST,
                "raw_transcript_sha256": hashlib.sha256(b"".join(log)).hexdigest(),
                "limits": ["Original author's fixtures; no independent verifier or human review.",
                           "One intentional forbidden-control-character test skip per nine-group run.",
                           "Distinct tracked physical aliases, concurrent writes, hosted CI and supplier mathematics are outside scope."]}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes((json.dumps(evidence, indent=2, ensure_ascii=True) + "\n").encode("utf-8"))
    args.output.with_suffix(".txt").write_bytes(b"".join(log))
    args.output.with_suffix(".patch").write_bytes(patch.encode("utf-8"))
    print(evidence["status"], "source_files=" + str(len(pins)))


if __name__ == "__main__":
    main()
