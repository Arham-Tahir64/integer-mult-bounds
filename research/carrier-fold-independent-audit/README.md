# Independent audit of the two coupled carrier folds

Both PR3133 carrier folds pass a separate exact dirty-state interpreter and
the retained independent finite-set frame checker. No defect was found in
this scope. This is a partial audit, with no supplier admission or new kappa.

Source: dcharb78's [PR3133](https://github.com/CrocSwap/integer-mult-bounds/pull/3133),
head `51eb9c4ee9e4722010d308aa3309e039d3940cc2`. The audit starts from canonical
main `997e6a9ca7b4f95d50e366f61412fd640d72a88a`, priority revision 6, card
`independent-moment` (chooser seed `1f7506f7bdccb4c2805c8006b0729380`). The
selected conditional kappa remains `0.001672660197076918`.

## Checked implication

The new code reconstructs the complete candidate from PR2979's two frozen
words and PR3133's fourteen source-addressed hunks, including the two endpoint
lowerings, shifted B-warp positions and inverse cleanup. The first two restore
edits reconstruct the PR3042 baseline. No supplier producer, frame solver,
primary auditor, stored PASS receipt or numerical root evaluator is executed.

For **each provider**, the baseline and candidate pass forward and
inverse-transpose replay on all **632 independent arbitrary dirty inputs**.
The forward boundary before cleanup has all 91 restored helper rows equal to
their own inputs, with no remaining reads of those inputs by other rows.
All **91 private buffers** start at zero, remain zero until cleanup, and return
to zero after cleanup in both orientations. Each isolated carrier fold also
passes forward replay. These are operator identities, not random samples.

The interpreter stores rational coefficients of `(input, chronological
operator word)` terms. A warp appends a formal invertible generator; only an
adjacent inverse pair cancels. ADD and SCALE act linearly. Thus equality in
this free group algebra remains equality after assigning any invertible linear
operator to each generator. This checks the scalar/warp composition without
asserting that a specific native circuit realizes those operators. Four small
hand-derived fixtures check noncommuting correction order, its dual, and
inverse cancellation.

Frame accounting reuses the pinned finite-set tracer from
`research/rank7-restore-substitution-audit/frames.py` (PR3065). It enumerates
subspaces of F2^9, checks chronological containment and literal warp boundaries,
and counts rank jumps. It is independent of PR3133's frame implementation;
this audit does not claim a new implementation of that retained checker.

| Change, relative to PR3042 | Exact local profile delta | Width inventory delta |
|---|---|---|
| Fold on helper 586 | `6 H2 - 2 H3 - 3 H4 + H5` | `+1 width-6, -1 width-7` |
| Fold on helper 588 | Same | Same |
| Both | `12 H2 - 4 H3 - 6 H4 + 2 H5` | `+2 width-6, -2 width-7` |

Here `Hr` denotes one rank-r recursive child. Both providers give the final
profile `{1:2433, 2:724, 3:228, 4:102, 5:20, 8:8}` and inventory
`{4:26, 5:2, 6:18, 7:50, 8:99, 9:213}`. The local paid rank mass falls
from 5,139 to 5,137.

## Valid losing controls and failure controls

For each fold separately, keep its literal scalar gates and frame paths but
restore its old rank-eight endpoint. This is a valid **fixed-path fold-only
control**, with unchanged width inventory and delta
`H1 + 6 H2 - 2 H3 - 3 H4 + H5`. Its endpoint semantics still pass.
Under the source's integer surrogate tariff, this control costs **+24,706**
units; the coupled fold costs **-2,091,965**, with a **+665** margin after the
source's rounded 2,091,300-unit width guide. These surrogate numbers are
comparison evidence, not certified physical idle prices or kappa acceptance.
The source's separately optimized fold-only `-973` margin and lowering-only
`-3345` margin are **not independently established here**. Our valid losing
control proves a statement only about the named fixed paths, not every fold-only
or lowering-only implementation.

Eight actual-word mutants per provider are rejected: either fold sign flipped,
either deleted B gate restored, unshifted warp chronology, a polluted private
buffer, a wrong rank-seven endpoint, and endpoint lowering without gate refits.
The four scalar mutants regenerate their cleanup before replay, so rejection
does not merely detect stale inverse lists. Failure reasons are retained in
[RESULT.json](RESULT.json).

## Aggregate bill: exact arithmetic, conditional idle remainder

The unchanged source-bound dispatch has 250 gauge44 and 416 extra calls.
Subtracting the independently recounted local bill from the published complete
profiles gives the following **conditional** idle change:

`4 H1 - 63 H3 - 338 H5 + H39 + 66 H48`.

Its rank mass is exactly 1,332, equal to the two freed width units in each of
666 calls. Both complete profiles have rank mass 4,816,512. This establishes
the arithmetic decomposition, not legality of the changed idle placement.
In particular, the old idle bill cannot simply be reused after lowering the
two endpoints. The raw aggregate profile is pinned to the exact PR head.

## Reproduce

From the repository root, using Python 3.12 or later and the standard library:

```sh
python3 -I -B research/carrier-fold-independent-audit/verify.py
python3 scripts/research_package.py --package research/carrier-fold-independent-audit --check-only
python3 scripts/research_package.py --package research/carrier-fold-independent-audit
```

The verifier checks every live source's SHA256 and Git blob identity, then
requires exact equality with the committed result. `--write-result` explicitly
regenerates that result for development. Successful direct execution was
checked on Windows with CPython 3.12.14; the registered replay and optimized
cross-version checks are recorded in the
[canonical finding](https://github.com/CrocSwap/integer-mult-bounds/discussions/2612#discussioncomment-18991086).

SOURCES.json uses the standard base-commit pins for retained main inputs.
VENDOR.json records original PR paths, commit, SHA256 and Git blob identities
for the imported bytes. Those source paths were cross-checked with `git show`
at the fetched exact PR head before publication. Replay verifies the retained
byte identities without needing that external PR commit in local history.

## Limits

This audit does not validate native Gaussian phases or residual adapters,
owner geometry and chronological idle packing, physical stock/backing storage,
all-size or precision/compiler assumptions, optimized single-move minima,
either supplier's cap, or the complete outer release. It does not certify
PR3133's claimed exponent or alter the selected result.

## Concurrent audit and disposition

The final complete overlap refresh found
[PR3136](https://github.com/CrocSwap/integer-mult-bounds/pull/3136), head
`3e73133a7b6a73d9433a2e33dc3404d8d049f20d`, published concurrently under the
same Arham Tahir account by a separate session. It covers the same local folds
and includes a separate implementation of the binary warp checks that this
package leaves inherited. Its artifact was inspected after this session's
interpreter and result had been completed. No exclusive novelty or independent
human review is claimed for either session.

This package is retained as independent implementation corroboration, plus the
explicit conditional aggregate-idle decomposition above. The result is handed
to the existing investigation with a public source commit; a second overlapping
audit PR is not requested. PR3136 deserves credit for the concurrent audit,
including its broader warp-validation and behavioral-control coverage.

## Open next questions

The next useful independent check is to bind the changed rank-six residual
adapters for helpers 586 and 588 to their exact native entrance/exit frames,
including global phase and dirty restoration. Start with PR3133's derived
adapter manifest and compare its literal operators to those frame pairs. This
matters because the free-operator identity here assumes correct realization;
its blocker is a separate native operator and phase replay.

A second bounded check is the changed idle placement that supplies the
conditional remainder above: bind FILL, ORDER, DISPATCH and provider widths,
then check ownership and chronology independently. Aggregate rank-mass balance
does not discharge that obligation. Structured questions are in TASK.json.

## Credit

dcharb78 owns the PR3133 coupled folds and PR3042 restore skips. Marius-Paul
Dumitrean / mdumitrean supplied PR2979's joint end frames and its retained
construction lineage; Jeremy Kothe supplied PR3015's declared-edit interface
and the earlier frame/cleanup and rewrite work; Mason Hale and Jeremy Diviney
supplied the paired-extension lineage. The retained independent PR3065 frame
tracer and restore-substitution audit are credited to Nick Petalas, with the
automated development assistance disclosed in that package. The supplier's
full predecessor notice is preserved verbatim
in `vendor/NOTICE`; all its attribution remains in force.

New interpreter and audit by Arham Tahir, with substantial OpenAI Codex
assistance. No independent human review is claimed. Apache-2.0.
