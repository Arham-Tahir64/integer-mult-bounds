# Batch source-pin reads without caching validation

**Verifier engineering; no new kappa or construction.** Registered package
validation previously launched two Git processes per source pin, then another
to reread the historical task catalogue. The change uses one literal tree
lookup and one streaming `git cat-file --batch` process. A 34-source fixture
therefore falls from 69 Git processes to two.

On this Windows host, seven alternating-order pairs measured median metadata
validation times of **1.928127 seconds before and 0.073139 seconds after**
(**26.36x**). [BENCHMARK.json](BENCHMARK.json) contains every pair, environment,
source hashes and process counts. These are local metadata timings, not a
complete circuit-replay speedup or a cross-platform guarantee. There is no
timing threshold in acceptance.

The receipt distinguishes the candidate's clean Git blob from its local checkout
SHA256, which includes this host's line endings. Baseline source pins bind the
exact historical Git bytes; no input pin is relaxed for newline conversion.

## Exact coverage and scope

The implementation changes `scripts/research_package.py` at its source
transport and pin-check loop. Every row still checks its base-tree object ID,
SHA256 of the full historical bytes, and, for live inputs, exact equality of
the working bytes. The original card is compared to the same historical
catalogue. Its already checked blob replaces the redundant read. Command,
timeout, dependency and package-selection checks remain in place.

`ls-tree -rz --full-tree` emits NUL-delimited records with literal pathspecs;
only exact object IDs are sent to `cat-file`. The reader checks each returned
ID, object type, length and trailing separator. It reads one payload at a time,
and terminates and reaps its child when a caller rejects a pin. Each invocation
repeats tree resolution, all pin checks and every live file read. Duplicate
requests are checked separately; no proof or validation result is cached.

The equivalence claim concerns regular-file inventories emitted by the package
generator. The reader explicitly rejects missing paths and non-blob entries;
directory provenance was not an inventory supported by that generator. No
text filters, compression normalization or field projection is applied.

## Evidence and reproduction

Base: `c5108f0f68d482e5712a8e26a5978d47762dfc16`. The exact previous implementation
is read from that commit and authenticated against [SOURCES.json](SOURCES.json).
Both implementations use the same fixture: two historical provenance pins and
32 live binary inputs of 4097 bytes. `verify.py` compares returned task/manifest
values and nine rejection controls, including changed working bytes after a
successful validation. A changed working catalogue remains valid historical
provenance. Both implementations make the same decisions.

Seven focused tests also cover binary/empty blobs, literal brackets, spaces,
an option-like filename, UTF-8 filenames, duplicate requests, changed bases,
missing/wildcard/directory paths, eight malformed responses, a nonzero Git exit
after valid output, and child cleanup after rejection.

From the repository root:

```sh
python3 -I -O -B research/batched-source-pin-validation/verify.py
python3 -B -m unittest discover -s tests -p test_research_source_blobs.py -v
python3 -B scripts/research_package.py --package research/batched-source-pin-validation --check-only
python3.12 -B scripts/research_package.py --package research/batched-source-pin-validation
# Optional measurement; preserve the committed receipt.
python3 -I -O -B research/batched-source-pin-validation/verify.py --benchmark /tmp/source-pin-benchmark.json
```

Expected: `PASS_BATCHED_SOURCE_PIN_VALIDATION sources=34 processes=69->2 controls=9`,
seven passing tests, and a metadata/pin pass. Direct optimized replay and
focused tests pass on CPython 3.14.6 / Git 2.45.1.windows.1. Python 3.12 is
unavailable locally, so the registered Python 3.12 replay and Linux timings
are unrun obligations.

The wider tooling suite was run with `PYTHONUTF8=1` and fixture Git
`core.autocrlf=false`: 25 tests pass, one Python-3.12-only test skips, and one
existing timeout test errors because Windows lacks `os.killpg` (also causing
its temporary-directory cleanup error). The exact original implementation
reproduces the same timeout/cleanup failure. Without those settings, existing
fixtures also hit locale decoding and Git newline conversion. These separate
portability defects are not repaired here. The selected source-binding
baseline passes; the selected cold replay was not run.

## Task and overlap

OS-random nonce `8b38097fe434074e63862edfb3f66d26` selected verifier engineering
and `replay-runtime`. The scope is refined to registered replay metadata.
[TASK.json](TASK.json) records the bounded domain, stop rule, next question,
final overlap refresh and exact nearest heads.

The entry check read paginated open-PR titles/bodies through the connected
GitHub API, local README/TASK/ledger notes through `find_overlap.py`, and the
public coordination threads and active Discussion list. Discussion comments
were not exhaustively paginated; code diffs were not searched. No match proves
novelty. PR797 improves a different compiler sorting bottleneck; PR1559 repairs
selected-bit gzip comparisons. Neither supplies this source-read optimization.

A local task card was used because the connector exposes no Discussion posting
tool. A credential-based access attempt was rejected by automatic approval
review and was not retried. The public contribution branch supplies the handoff.

Submission status: the validated branch is public at
`Arham-Tahir64/integer-mult-bounds:codex/independent-result-20261013`. The GitHub
connector rejected upstream PR creation with HTTP 403 (integration access),
and the available browser was signed out. No upstream PR was created; the
public branch comparison supplies an independently reviewable handoff.

## Open next questions

How much does batching save on large real contributed manifests on Linux CI?
Process startup, Git pack layout and other replay costs vary. The first step
is the identical-fixture benchmark on Linux, then metadata validation of one
accepted large manifest. Representative accepted manifests and hosted
measurements remain required; no complete selected-replay speedup follows
from the local receipt.

## Credit

Douglas Colkitt, with OpenAI Codex assistance, wrote the registered-package
validator and onboarding workflow. Maxime Fleury's reproducibility audit,
following Antoine Olivier's replay findings, distinguishes immutable source
hashes from regenerated containers. PR797's compiler optimization and PR1559's
gzip comparison are distinct work and retain their authors' credit.

Prepared by Arham Tahir with substantial OpenAI Codex assistance in design,
implementation, tests, measurement and writing. No independent human or
subagent review is claimed. New work is Apache-2.0; inherited attribution and
source licenses are unchanged.
