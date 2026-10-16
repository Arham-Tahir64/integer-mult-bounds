# PR3007: CP1252 diagnostic test failure and repair

The native Windows handoff from [PR3007](https://github.com/CrocSwap/integer-mult-bounds/pull/3007)
and [ToikY's macOS audit](https://github.com/CrocSwap/integer-mult-bounds/discussions/2983#discussioncomment-18980039)
finds one **test portability defect** at exact head
`3cb500b743f36e13d21b6a46f126846bf36bad32`. The production Git-spelling guard
rejects the Unicode alias correctly. Its test subprocess decodes stderr as
UTF-8 without requiring the writer to use UTF-8. Under CP1252, Python's stderr
escapes the combining accent, and the literal-filename assertion fails:

```text
AssertionError: 'src/cafe\u0301.json' not found in
'use an exact Git-tracked input path from HEAD: src/cafe\\u0301.json\n'
```

This was first observed using the host's ordinary CPython 3.12 command and then
reproduced with explicit output encodings. [EVIDENCE.patch](EVIDENCE.patch)
sets `PYTHONIOENCODING=utf-8` in that test helper's subprocess environment,
matching its existing UTF-8 reader. Every assertion remains intact. This patch
is an attachment for the pending PR's author; no shared runner or predecessor
source is modified by this contribution.

**Concurrent evidence and the distinct delta.** The native Windows/Win32-alias
[attachment at `e16c73710d350afe93ea0f174724dc89881defb1`](https://github.com/Arham-Tahir64/integer-mult-bounds/tree/e16c73710d350afe93ea0f174724dc89881defb1/research/replay-input-windows-audit)
was published during this session. Its `native_probe.py` explicitly runs the
registered command with `-X utf8`, `PYTHONUTF8=1` and
`PYTHONIOENCODING=utf-8`. Its passing result is consistent with the UTF-8 control
here. This contribution's added result is the CP1252 failure and minimal test
repair, with a controlled before/after comparison. The common registered platform
coverage is corroboration, not a claim of exclusive Windows coverage. The
concurrent claims and prior observation design retain credit.

## Measured result

Native Windows 11 build 26200, x86-64, CPython 3.12.10, Git for Windows 2.45.1.
The fixture volume resolves ASCII case aliases to the same file. NFC and NFD
filenames are distinct on this volume.

| Registered replay | Result |
| --- | --- |
| Original source, CP1252 child output | Fails only the literal Unicode diagnostic assertion; one intentional skip |
| Original source, UTF-8 child output | 13 tests pass, one intentional skip |
| Patched test helper, CP1252 inherited output | 13 tests pass, one intentional skip |

All three runs first pass the source-bound differential: three historical
planner omissions, three repaired rejections, and two canonical controls.
The first run stops before the five retained lexical-input tests. Each passing
run executes all nine new groups (eight pass, one skips) and all five retained
groups. The skipped group creates tab, CR and LF filenames that Windows forbids;
permitted-space behavior and the larger observation matrix are covered by the
concurrent attachment rather than rerun here.

The original registration retains its Unicode, full source-pinned metadata,
case-only rename, deleted-parent, staged/untracked and Git-failure controls.
No assertion, fixture or production predicate is removed or relaxed. The prior
native Windows attachment supplies the larger filesystem observation matrix;
this package does not rebuild it.

[EVIDENCE.json](EVIDENCE.json) records the 13 authenticated source files,
exact Git blobs and SHA256s, per-run output hashes, platform information
and native stream encodings. [EVIDENCE.txt](EVIDENCE.txt)
retains raw registered stdout followed by stderr for each labelled run,
including native CRLF. Its hash is recorded in the JSON. Timings, temporary
paths and environment fields are observations and need not reproduce byte-for-byte.

## Reproduce on native Windows

Use Python 3.12 and Git. From a repository containing this contribution, fetch
the exact public dependency and its historical baseline, then create a fresh
sparse worktree. Replace `python` with the intended Python 3.12 executable.
Use fresh output paths to retain the published evidence.

```powershell
git fetch --no-tags https://github.com/CrocSwap/integer-mult-bounds.git refs/pull/3007/head
git fetch --no-tags https://github.com/CrocSwap/integer-mult-bounds.git 836b19bfa309ceafbc8ee32a15e8c4b10dde7e11
git worktree add --no-checkout --detach ../pr3007-native-source 3cb500b743f36e13d21b6a46f126846bf36bad32
git -C ../pr3007-native-source sparse-checkout set scripts tests research/replay-input-head-spelling
git -C ../pr3007-native-source checkout
python -I -B research/replay-input-windows-diagnostics/audit.py --source-root ../pr3007-native-source --output ../windows-audit-rerun/EVIDENCE.json
```

Expected marker:

```text
PASS_NATIVE_WINDOWS_AUDIT_WITH_TEST_PROTOCOL_REPAIR source_files=13
```

The audit checks all 13 working files against the exact commit before execution
and again afterward. It creates a disposable sparse repository borrowing only
the local immutable object database, copying shallow boundaries when necessary;
it performs no network access or writes to the supplied source checkout. It
tests the original source under both encodings, applies the exact generated
patch only in that temporary repository, and runs the same registration again.
A changed-source rejection control confirms that the deliberately patched test
no longer authenticates as the original source. All scratch state is cleaned
on ordinary exit. On the observed host the complete audit takes roughly a minute;
each of the three registered subprocesses has a 120-second timeout. Set
`TEMP` and `TMP` to an existing writable scratch directory when required by a
sandbox. A local Git clone transport could not start its MSYS helper inside
this sandbox, so the audit uses direct local object borrowing instead.

There is no generic Linux registration for this native-only check of an unmerged
dependency. The explicit command above is its replay entry point. Python 3.12
standard library and Git suffice; no dependencies are installed.

## Scope and credit

Started from canonical main `d8e0f83f00191df62174b641e9fff055c357f641`, priority
revision 6. [TASK.json](TASK.json) records handoff-first selection, overlap,
the declared scope and stopping rule. The historical runner used by PR3007 is
`836b19bfa309ceafbc8ee32a15e8c4b10dde7e11`; its original blob/SHA256 checks remain
active. The supplied source checkout remains byte-identical. Source immutability,
the production routing guard and the assertion coverage are preserved.

This is independently executed platform evidence using Nick Petalas's fixtures,
with controlled stream encodings and a narrow test patch. It is not a separately
implemented verifier or independent human review. Distinct tracked names that
physically alias, concurrent source mutation, hosted CI and supplier mathematics
remain outside scope. No new supplier, kappa or selected-frontier claim is made.

Credit Nick Petalas/PR3007 for the repair, fixtures and handoff; Arham Tahir/PR2994
for the original native macOS counterexamples and repair contract; ToikY for the
macOS execution, four-cell observation design and remaining Windows handoff;
Nick Petalas/PR2986, EdDiboi, woklerx/PR1891, Charles Bethin, Douglas Colkitt and
the retained runner/scaffold authors. Windows execution, diagnostic audit driver and
test-protocol patch by Arham Tahir with substantial OpenAI Codex assistance.
Apache-2.0; predecessor notices and source licenses remain intact.

## Open next questions

Adopt the attached test-helper patch in PR3007 and run its registered command
under an ordinary Windows code-page environment. The first step is applying
`EVIDENCE.patch` to that exact head; the patched CP1252 run here supplies the
acceptance evidence. The dependency's author/maintainer has not adopted it in
this contribution. No further alias census is justified by this diagnostic
defect, and no production guard change is proposed.
