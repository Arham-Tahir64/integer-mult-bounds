# Independent intrinsic-endpoint audit for the P104 physical dual

[PR2586](https://github.com/CrocSwap/integer-mult-bounds/pull/2586), pinned at
`7953c9a8f788a8de5cf2ced63d9a61b67c22c6f1`, realizes the ordinary physical
inverse-transpose in canonical endpoint charts and explicitly leaves intrinsic
conversion open. This package checks that finite boundary obligation: **104
X-input and 104 Y-output monomial adapters**, with exact phase, give the
inverse-transpose of the forward map in its original intrinsic convention.
They add **zero positive children and zero rank mass**. The 416 H1 transports
of PR2586 are all retained. This is not a transport-fusion improvement.

No complete supplier, new kappa, rounded-erasure contract, hosting or optimality
claim is made. The standard inverse-transpose identities are not new; the result
is their source-bound realization and exact interface check for this word.

The final overlap refresh found the simultaneous
[intrinsic-bridge investigation, Discussion2646](https://github.com/CrocSwap/integer-mult-bounds/discussions/2646),
posted after this session's entry snapshot. It claims the **same bridge**, using
separately written Gaussian-integer column formulas. This package is retained
as independent corroboration: it uses the retained native interpreter, checks
literal native monomial recipes, and freshly replays the complete PR2586 source
before composing the endpoints. It does not claim a distinct mathematical
mechanism or priority. The public artifact is handed to that canonical thread;
no competing bridge PR is required for this result.

## Exact statement and proof

Use ordinary bilinear transpose T. For each physical odd root label q, let
`C_q=((1+i)I+(1-i)X_q)/2`, let F be the product of the nine coordinate C gates,
and let Gamma_W be the retained canonical unitary chart. The original forward
intrinsic charts I_i and I_f on the public roles are:

| Role | I_i | I_f |
| --- | --- | --- |
| X_s, 104 roles | C_qs | F |
| Y_t, 104 roles | I | F C_qt^(-1) |
| Dirty helpers, 150 roles | I | F |

Let S be the real logical shear from the pinned predecessor: X and helpers
stay fixed; Y receives C X. Only C's first two rows are identity rows; the other
102 rows remain Gram/2. Set `F_can=Gamma_f S Gamma_i^(-1)` and
`F_int=I_f S I_i^(-1)`. Define public block-diagonal monomials A and B by

```
A_Xs = Gamma_<qs> C_qs^(-1)              (input adapter)
B_Yt = F C_qt^(-1) Gamma_(qt-perp)^(-1)  (output adapter)
```

All other blocks of A/B are identity. These are precisely PR1991's 208
forward endpoint adapters. The verifier checks their actual native recipes
against these formulas, including scalar phase and their binding to PR2586's
canonical input/output frames. Thus `F_int=B F_can A`.

For invertible matrices, inverse transpose preserves written product order:
`(B F_can A)^(-T)=B^(-T) F_can^(-T) A^(-T)`. The monomials are unitary, so
`A^(-T)=conjugate(A)` and `B^(-T)=conjugate(B)`. Consequently execute:

1. conjugate(A) on the 104 X inputs;
2. the complete unchanged PR2586 physical dual;
3. conjugate(B) on the 104 Y outputs.

The result is exactly `F_int^(-T)`. Equivalently it realizes the logical
`S^(-T)` between **conjugate(I_i)** and **conjugate(I_f)**. It does not claim
the backward-chart operator `I_i S^(-T) I_f^(-1)` or replace ordinary transpose
by adjoint. Correct product order is tested on a noncommuting complex fixture.

For each rank-zero recipe, retain its binary address matrix, XOR offset and
quadratic rows; negate its linear Z4 phases and global phase modulo four.
The off-diagonal quadratic coefficient is two modulo four and is unchanged
by negation. This gives the concrete dual adapter recipe. All **106,496**
adapter/address columns are compared with an independently formed sparse
monomial inverse-transpose. Signed Pauli action plus an exact nonzero state
column also checks each literal chart equality and its phase, fixing the entire
Clifford operator. Linear composition therefore covers arbitrary 512-address
arrays and arbitrary public dirty input, not just scalar samples.

## Evidence and cost boundary

The default verifier first authenticates and replays the complete unchanged
PR2586 package from its retained source archive. Its two logical engines check
all 128,164 coefficients over 358 public roles, native recipes cover all 2,070
transport occurrences, and all eight exact private zero erasures pass. This
is a fresh replay of the predecessor's declared finite checks, using its
credited implementation, not an independently written replacement for them.
Our wrappers touch only public X/Y roles, so they do not modify helper or
private-collector events or their zero checks.

The wrapped program has **5,606** literal events: the retained 5,398 plus 208
rank-zero monomial operations. Its positive profile remains

```
1632 H1 + 74 H2 + 86 H3 + 104 H4 + 48 H5 + 42 H6 + 76 H7 + 8 H8
rank mass = 3542
```

Rank-zero operations have no positive recursive child in the retained native
contract. Their permutations, XORs and phases are explicit; no free physical
tape, layout, routing or runtime implementation is inferred. Decreasing
endpoint transports and private returns, idle/residual charges, physical
precision and rounded strict-zero erasure, full moment, all-size lifting and
the selected cold replay remain unproved/unrun here. Wrappers do not repair
the other 102 correction rows or admit a monotone owner contract.

The receipt includes rejecting controls for global phase, omitted wrapper,
wrong port, missing conjugation, adjoint confusion, wrong external chart and
reversed product order. Some actual adapters commute with their endpoint
charts; the verifier accepts this and uses a separate noncommuting fixture
for the general ordering control.

## Reproduce

Standard-library Python 3.12 or later; no compiler, Git or network is needed
for the direct replay:

```sh
python3 -I -O -B research/p104-physical-dual-intrinsic-endpoints/verify.py
python3 -I -B research/p104-physical-dual-intrinsic-endpoints/test_verify.py
python3 scripts/research_package.py --package research/p104-physical-dual-intrinsic-endpoints
```

`--out NEW.json` writes the receipt exclusively. `--adapters-out NEW.json`
exports all 208 exact wrapper records, canonically ordered as in the pinned
forward certificate. Its compact JSON bytes match the receipt's adapter hash.
Existing outputs are refused. Replay uses temporary storage; on a host whose
default temp directory is restricted, set TEMP/TMP (or TMPDIR on POSIX) to a
writable directory. The default replay does not write into the checkout.

[PREDECESSOR.json](PREDECESSOR.json) identifies every unchanged archived file
by PR head, Git blob and SHA256. Original README credit and limitations are
retained inside the archive. [SOURCES.json](SOURCES.json) pins the live main
inputs. [TASK.json](TASK.json) records priority revision 5, the bounded task,
overlap and environment. The registered provenance check additionally needs
Git history. No source archives or selected records are changed.

## Open next questions

Can a complete caller afford the physical endpoints, private lifetimes and
restoration? Pin that caller and write its complete owner/routing, monomial,
idle/residual and rounded-erasure ledger first. These unknown costs block
supplier admission. Discussion2619 separately investigates fusion; no saving
from it is assumed here. This closes the scoped boundary task and stops before
another construction expansion. Structured follow-up is in TASK.json.

## Credit

ywz65/PR2586 supplies the canonical physical dual and PR2497 the clean logical
word. Nick Petalas/PR2550 supplies the complementary-frame idea; PR2551
distinguishes the physical contracts. Chafik Boukhalfa/PR1991 supplies the native
channel and forward intrinsic adapters. Retain Rohan Arun/PR1972, Ross
Richardson/PR2445, Adam Gall/PR1940, Josie Elliston/PR1071, Ali
Romman/PR1125/1862, icekylinx's compiler and all credited native/geometry
ancestry. PR2497/PR2550 already check intrinsic adapters for their different
backward/complementary contracts; no claim to invent those adapters is made.

New endpoint proof, recipe conversion and check prepared by Arham Tahir with
substantial OpenAI Codex assistance. Apache-2.0. No independent human review,
proof assistant or complete multiplication theorem verification is claimed.
The concurrent Discussion2646 effort also posts as Arham Tahir with OpenAI
Codex assistance; the methods were developed independently during overlapping
sessions, not by a delegated reviewer. This is computational corroboration,
not independent human review.
