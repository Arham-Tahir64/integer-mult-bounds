# Native Windows audit and Unicode capture correction

**Result:** PR3007's exact-Git boundary works in the checked native Windows
fixtures, but its original registered replay fails a Unicode test under CP1252.
The test explicitly decodes its child as UTF-8 without requesting UTF-8 output.
The child correctly rejects `src/cafe\u0301.json`, escaping the combining accent
as the literal six-character sequence `\u0301`; the assertion expects the literal
combining character. This is a test-harness mismatch, not an accepted alias.

The small correction is independently cherry-pickable as commit
[`369e38c0952b2228dec03fd51ce1e1e84b6a32cd`](https://github.com/Arham-Tahir64/integer-mult-bounds/commit/369e38c0952b2228dec03fd51ce1e1e84b6a32cd).
It requests `PYTHONIOENCODING=utf-8` in the helper that already decodes UTF-8,
and adds an explicit CP1252 rejection/no-partial-output control. Production
runner bytes, original fixtures and scientific inputs are unchanged. The
existing canonical PR remains [PR3007](https://github.com/CrocSwap/integer-mult-bounds/pull/3007);
this attachment does not open another copy of that PR.

## Exact sources and task

Orientation and submission main: `d8e0f83f00191df62174b641e9fff055c357f641`,
priority revision 6. Canonical main was fetched again before publication and
was unchanged. Audited PR3007 source: `3cb500b743f36e13d21b6a46f126846bf36bad32`,
Nick Petalas. Original-runner provenance:
`836b19bfa309ceafbc8ee32a15e8c4b10dde7e11`, SHA256
`51e8ee72b1c99de7060c4cc83aabcc54ff1a572bad31f31a6d0102dcc0aae0aa`.

Task `portable-replay`, refined to the explicit native Windows handoff in
[the canonical investigation](https://github.com/CrocSwap/integer-mult-bounds/discussions/2983#discussioncomment-18978628)
and [ToikY's macOS follow-up](https://github.com/CrocSwap/integer-mult-bounds/discussions/2983#discussioncomment-18980039).
No card was drawn because this was an open handoff. Success/stop test: a
source-bound native replay verdict, explicit skips, and one bounded fix if a
concrete native failure emerged. Session budget: about 60 minutes; no supplier
work or mechanism expansion. The original claim is
[comment 18981673](https://github.com/CrocSwap/integer-mult-bounds/discussions/2983#discussioncomment-18981673).

Entry overlap: 277 open PRs, 1,760 Discussion records and 399 sparse local
records. Submission refresh at 19:48 UTC on 2026-10-16: 279 open PRs and 1,767
Discussion records, complete pagination, plus three local records in the
dependency checkout. Cached/offline search warnings identify use of that fresh
API snapshot. Closed PRs, arbitrary diffs, unpublished work and excluded sparse
directories were not exhaustively searched. No novelty certificate is claimed.

The final scan exposed concurrent Windows claims
[18981656](https://github.com/CrocSwap/integer-mult-bounds/discussions/2983#discussioncomment-18981656),
[18981663](https://github.com/CrocSwap/integer-mult-bounds/discussions/2983#discussioncomment-18981663)
and [18981668](https://github.com/CrocSwap/integer-mult-bounds/discussions/2983#discussioncomment-18981668).
This is independent concurrent execution using credited predecessor fixtures;
discovery priority and independent human review are not claimed. The added
value is the concrete CP1252 assertion failure, small patch, retained legacy
encoding control and inspectable native receipt.

During final publication, the concurrent claim 18981663 published a passing
[Windows 3.12.10 report](https://github.com/Arham-Tahir64/integer-mult-bounds/tree/e16c73710d350afe93ea0f174724dc89881defb1/research/replay-input-windows-audit),
including additional Win32 trailing-dot/trailing-space coverage. That evidence
is credited. The failure here is scoped to the explicitly reproduced CP1252
pipe contract; it does not claim every native Windows configuration fails.

## Reproduction and evidence

Use native Windows, Git, a Python 3.12 executable, and a checkout containing the
two exact Git source objects above. In PowerShell, `python` below must refer to
Python 3.12. Set temporary files to a writable local directory; the sandbox's
default application temporary directory produced an ACL failure before the
first test and was excluded from the scientific verdict.

```powershell
$replayTmp = Join-Path (Get-Location) 'windows-spelling-tmp'
New-Item -ItemType Directory -Path $replayTmp -Force | Out-Null
$env:TEMP = $replayTmp
$env:TMP = $replayTmp
python -B research/replay-input-head-spelling/native-windows-audit/audit.py --output windows-spelling-rerun.json
```

The script does not fetch or modify source files. It authenticates all 13
published package/input files, allowing only the declared test-file correction,
then runs the original Unicode test from authenticated source, the corrected
registered replay, and native full-metadata probes. Proof-relevant imports use
a fresh bytecode-cache namespace. It writes a receipt only after every check
passes. It deliberately forces CP1252 with UTF-8 mode disabled so the original
failure remains reproducible even from a UTF-8-configured parent shell.

[EVIDENCE.json](EVIDENCE.json) records Windows 11 build 26200, AMD64, CPython
3.12.14 and Git 2.45.1.windows.1. It contains original and working SHA256 hashes,
the original assertion failure, complete corrected registered output, and the
seven native probe rows. Repository and audit-temp paths in captured output are
replaced with `<ROOT>`/`<TEMP>`; timings and ephemeral fixture paths can differ
on replay, so whole-receipt byte equality is not an acceptance test.

| Check | Native result |
|---|---|
| Original Unicode test under CP1252 | Expected failure: literal combining character versus escaped diagnostic |
| Corrected registered replay | 10 spelling tests and 5 retained lexical tests run; 14 pass, 1 intentional skip |
| Explicit CP1252 diagnostic control | Rejection, empty stdout and existing workflow-output bytes retained |
| Authenticated before/after CLI | 3 original empty matrices; 3 repaired rejections; 2 canonical controls |
| Three ASCII aliases, full metadata | Physically alias on this volume; original accepts and omits replay; repaired validator and planner reject |
| NFC/NFD with precomposeunicode false/true | Four cases; forms remain distinct on this volume; repaired identity follows exact Git spelling |
| Canonical full-metadata/plan pairs | 10 pass, five fixtures against both original and repaired runners |

The intentional skipped group is
`test_nul_framing_preserves_spaces_tabs_and_newlines`: Windows forbids tab/CR/LF
in these fixture filenames. Case-only rename, missing repository/HEAD,
deleted-parent, unrelated-input, staged/untracked-input and full-metadata
controls execute successfully. The 10 spelling tests also pass with the same
one skip under native CPython 3.14.6 using `-I -O -Werror -B`; that direct
supplement is not the version-gated registered replay.

No full 167-test tooling suite, hosted CI, independent human/formal review,
selected cold replay, native mathematical supplier replay or new kappa is
claimed. Distinct tracked names that physically alias and concurrent writers
retain the predecessor's exclusions. The Unicode normalization observations
are about this Windows volume, not every Windows filesystem configuration.

## Credit

Nick Petalas supplied PR3007's repair, fixtures and handoff, and PR2986's
separate symlink repair; Arham Tahir supplied PR2994's native macOS finding and
Git-spelling handoff; ToikY supplied the native macOS audit. Retain EdDiboi's
earlier symlink finding, woklerx/PR1891, Charles Bethin, Douglas Colkitt and all
source runner/scaffold attribution. Concurrent Windows investigations are
linked above. New attachment and test correction: Arham Tahir, with substantial
OpenAI Codex assistance in investigation, implementation, testing and writing.
Apache-2.0. No subagents or independent human review were used.

## Open next questions

1. Apply the small test-only correction to PR3007 or an equivalent successor,
   then run its existing cross-platform CI. First step: cherry-pick the linked
   fix commit and run the registered command. The blocker is upstream adoption;
   native Windows no longer lacks a concrete execution result.
2. Compare the concurrent native reports before requesting another replay.
   First step: inspect their exact heads and encoding contracts in the canonical
   thread. Only a changed failure mode or uncovered platform contract justifies
   more work; no further alias census is proposed here.
