# PR3007: native Windows evidence

**PASS on the recorded host.** This completes the native Windows request in
[the existing investigation](https://github.com/CrocSwap/integer-mult-bounds/discussions/2983#discussioncomment-18980039)
at PR3007 head `3cb500b743f36e13d21b6a46f126846bf36bad32`.
It is a native corroboration using authenticated author fixtures and an adapted
probe, not a separately implemented verifier or independent human review.

The evidence attachment starts from canonical main
`d8e0f83f00191df62174b641e9fff055c357f641`, priority revision 6. The task is a
handoff-first refinement of `portable-replay`, changing its generic artifact
comparison scope to native Windows replay-selection behavior. The bounded goal
was one exact-head platform check and filesystem observation matrix; no supplier
or selected-result change was attempted. The claim, source pins and released
result belong to the existing discussion, rather than a second canonical PR.

## Recorded result

- Windows 11 build 26200, AMD64; CPython 3.12.10;
  Git `2.45.1.windows.1`. Fresh disposable fixtures were placed on this host's
  case-insensitive, Unicode-preserving volume. No WSL or POSIX emulation was used
  for Python or filesystem behavior.
- The **actual registered command** passes: nine new test methods and five
  retained test methods, **13 passing and one intentional skip**. Windows forbids
  the control characters used by the skipped filename test. The differential
  replay reports three baseline omissions, three repaired rejections and two
  canonical controls. See [registered-replay.log](registered-replay.log).
- [native-observations.json](native-observations.json) records four cells crossing
  `core.precomposeunicode=false/true` with initially NFC/NFD filenames. In all
  four cells, Git preserves the created form; the alternate Unicode form is
  absent on this volume. Its declaration rejects at the repaired HEAD boundary;
  exact spelling selects the consumer. Four case-only directory renames select
  both exact consumers, with the raw NUL-framed Git deltas retained.
- **28 full-metadata comparisons:** 24 physical-alias declarations pass the old
  validator and fail the repaired HEAD check; the four nonexistent Unicode
  alternate spellings already fail the old file-existence check and fail the
  repaired HEAD check. Eight canonical validator calls pass. Added dependencies
  are unpinned, as permitted by the schema; source-provenance aliases are not
  claimed to pass.
- **Six actual Git/CLI alias comparisons** include the three ASCII case aliases
  and Windows-specific `src./dep.json`, `src/dep.json.` and `src/dep.json `
  (the last has a trailing space). Each names the same physical file as
  `src/dep.json`. On the same target-only Git diff the old planner publishes an
  empty matrix; the repair rejects before stdout or the existing output file is
  changed. Exact spelling selects `research/alpha` in every positive control.
- All **13 audited package/input files** match their exact Git blobs before and
  after the observations. The JSON retains each Git blob ID and SHA256.
  Imports use a fresh private bytecode namespace. Normal and optimized Python
  executions produce byte-identical JSON; the public receipt hash is recorded
  in the canonical discussion.

The old runner is independently authenticated to main
`836b19bfa309ceafbc8ee32a15e8c4b10dde7e11` and SHA256
`51e8ee72b1c99de7060c4cc83aabcc54ff1a572bad31f31a6d0102dcc0aae0aa`.
The published probe checks both source heads and rejects working-source drift.
The recorded log concatenates captured stdout followed by stderr; their original
interleaving is not claimed.
Local Git attributes preserve the observation and log bytes exactly, including
Windows line endings. The recorded JSON SHA256 is
`6a8a3392f0d3efd162cb70630f6dc94039105ec8108c94961ec179bf850850fe`.

Three concurrent native Windows claims appeared between the entry and final
overlap snapshots ([18981656](https://github.com/CrocSwap/integer-mult-bounds/discussions/2983#discussioncomment-18981656),
[18981668](https://github.com/CrocSwap/integer-mult-bounds/discussions/2983#discussioncomment-18981668),
[18981673](https://github.com/CrocSwap/integer-mult-bounds/discussions/2983#discussioncomment-18981673)).
The common registered replay overlaps their scope; the additional trailing-dot
and trailing-space planner/full-metadata comparisons are this attachment's
specific extra coverage. No priority or exclusive Windows-verification credit
is claimed. This attachment is a result in the same canonical investigation.

## Reproduce on native Windows

Use a fresh directory, Python 3.12 and Git. Fetch both commits so the predecessor
provenance is available. From the directory containing this evidence attachment:

```powershell
git clone --filter=blob:none --no-checkout --depth=1 https://github.com/CrocSwap/integer-mult-bounds.git pr3007-source
git -C pr3007-source config core.autocrlf false
git -C pr3007-source sparse-checkout set --no-cone scripts tests research/replay-input-head-spelling certificates/selected-result.json docs/research/agent-task-catalog.json
git -C pr3007-source fetch --no-tags --depth=1 origin refs/pull/3007/head 836b19bfa309ceafbc8ee32a15e8c4b10dde7e11
git -C pr3007-source checkout --detach 3cb500b743f36e13d21b6a46f126846bf36bad32

python -I -B native_probe.py pr3007-source --registered-log replay.log > observations.json
python -I -O -B native_probe.py pr3007-source > optimized.json
Get-FileHash observations.json, optimized.json -Algorithm SHA256
```

No dependencies are installed. The probe takes roughly a minute on the recorded
host, including the registered replay. The JSON deliberately records interpreter,
Git and OS versions; another environment can produce different bytes while the
same scoped checks pass. `TMP`/`TEMP` may point to a writable task directory when
the default sandbox temporary directory cannot support child fixture processes.
Those initial sandbox restrictions are environment failures, not PR3007 failures.
The recorded successful runs used native processes outside that restriction.

## Open next questions

This closes the requested platform check, not PR3007's substantive review or
merge decision. Its hosted CI remains separate. Distinct tracked paths that
physically alias and concurrently changing inputs remain outside the existing
contract; either needs a separately specified acceptance decision before a new
test campaign. The smallest next step is maintainer review of the exact PR head
with the Linux, macOS and Windows evidence together. No additional native replay
is proposed absent a source, environment or contract change.

No scientific admission, full cold supplier replay, new kappa or selected-frontier
change follows from these tooling checks.

## Credit and license

Nick Petalas supplied PR3007's repair, fixtures and handoff. Arham Tahir supplied
PR2994's native counterexamples and repair contract. This Windows probe adapts
ToikY's macOS probe and observation structure at
`f35825d5cdc8c918fcb466d66476ae35b534eb05`, file blob
`f39daa0598691bca795772a1bd0222f33585b215`; the new Windows-specific alias controls
and observations do not replace ToikY's macOS evidence.

Retain Nick Petalas/PR2986, EdDiboi, woklerx/PR1891, Charles Bethin, Douglas Colkitt
and the original runner/scaffold contributors' attribution. Native Windows
execution, adaptation, evidence and handoff by Arham Tahir with substantial
OpenAI Codex assistance. Apache-2.0. No independent human review is claimed.
