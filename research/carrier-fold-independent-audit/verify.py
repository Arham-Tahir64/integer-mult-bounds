# SPDX-License-Identifier: Apache-2.0
"""Separate exact dirty-state interpreter for the two PR3133 carrier folds.

No supplier producer, auditor or frame solver is executed. The independent
PR3065 finite-set frame tracer is reused with its exact source pin and credit.
"""
import copy
import gzip
import hashlib
import importlib.util
import json
from collections import Counter
from fractions import Fraction as Q
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = P.parents[1]
HEAD = '51eb9c4ee9e4722010d308aa3309e039d3940cc2'


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def read(path):
    data = path.read_bytes()
    if data[:2] == b'\x1f\x8b':
        data = gzip.decompress(data)
    return json.loads(data)


def pins():
    source_rows = [entry for entry in read(P / 'SOURCES.json')['files'] if entry['usage'] == 'input']
    vendor = read(P / 'VENDOR.json')
    require(vendor['head'] == HEAD, 'vendor head declaration')
    for entry in source_rows + vendor['files']:
        raw = (ROOT / entry['path']).read_bytes()
        require(hashlib.sha256(raw).hexdigest() == entry['sha256'], 'input SHA256: ' + entry['path'])
        require(hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest()
                == entry['git_blob'], 'input Git blob: ' + entry['path'])


def frame_module():
    path = ROOT / 'research/rank7-restore-substitution-audit/frames.py'
    spec = importlib.util.spec_from_file_location('independent_frames', path)
    mod = importlib.util.module_from_spec(spec)
    # Compile the pinned source directly: do not consume an ambient .pyc.
    exec(compile(path.read_bytes(), str(path), 'exec'), mod.__dict__)
    return mod


def delta(before, after):
    return {r: after.get(r, 0) - before.get(r, 0)
            for r in sorted(before.keys() | after.keys())
            if before.get(r, 0) != after.get(r, 0)}


def b_program(word):
    scheduled = {}
    for op, record in enumerate(word['warps'], 1):
        scheduled.setdefault(record[0], []).append(['warp', record[1], op])
    result = []
    for i in range(len(word['B']) + 1):
        result.extend(scheduled.get(i, []))
        if i < len(word['B']):
            result.append(word['B'][i])
    return result


def cleanup(word):
    full = [256, 128, 64, 32, 16, 8, 4, 2, 1]
    restored = set(map(int, word['helper_final']))
    rename = lambda r: r + 704 if r in restored else r
    stream = word['A'][word['prelude_events']:] + b_program(word) + word['restore']
    result = []
    for gate in stream[::-1]:
        kind, target = gate[:2]
        if kind != 'warp' and 112 <= target < 224:
            continue
        if kind == 'warp':
            result.append(['warp', rename(target), -gate[2], full])
        elif kind == 'add':
            result.append(['add', rename(target), rename(gate[2]), -gate[3], gate[4], full])
        else:
            require(kind == 'scale' and gate[2] != 0, 'invertible cleanup scale')
            result.append(['scale', rename(target), gate[3], gate[2], full])
    return result


def rebuild(parent, edits):
    """Source-addressed splice, independent of declared_edits.py."""
    word = copy.deepcopy(parent)
    hunks = [h for edit in edits for h in edit.get('edits', [edit])]
    for section in ('A', 'B', 'restore'):
        selected = sorted([h for h in hunks if h['section'] == section], key=lambda h: h['start'])
        gates, cursor = [], 0
        for hunk in selected:
            start, stop = hunk['start'], hunk['stop']
            require(cursor <= start < stop <= len(parent[section]), 'disjoint source interval')
            require(parent[section][start:stop] == hunk['old'], 'exact edit preimage')
            gates.extend(parent[section][cursor:start])
            gates.extend(copy.deepcopy(hunk['new']))
            cursor = stop
        gates.extend(parent[section][cursor:])
        word[section] = gates
    for warp in word['warps']:
        position = warp[0]
        for h in hunks:
            if h['section'] == 'B':
                require(not h['start'] < position < h['stop'], 'warp inside edited interval')
        warp[0] += sum(len(h['new']) - len(h['old']) for h in hunks
                       if h['section'] == 'B' and h['stop'] <= position)
    for edit in edits:
        for r, change in edit.get('helper_final', {}).items():
            require(word['helper_final'][r] == change['old'], 'endpoint preimage')
            word['helper_final'][r] = change['new']
    word['cleanup'] = cleanup(word)
    return word


def extend(term, operators):
    """Postfix operator words; only adjacent inverse cancellation is used."""
    variable, old = term
    stack = list(old)
    for op in operators:
        if stack and stack[-1] == -op:
            stack.pop()
        else:
            stack.append(op)
    return variable, tuple(stack)


def execute(word, dual=False, check=True):
    """All 632 dirty inputs; independent symbolic invertible warp operators."""
    live = sorted(set(range(704)) - set(word['removed']))
    require(len(live) == 632, 'live input count')
    restored = set(map(int, word['helper_final']))
    rows = {r: {(r, ()): Q(1)} for r in live}
    rows.update({r + 704: {} for r in restored})
    stream = []
    for record in word['initial_corrections']:
        stream.append(['operator_add', record['target'], record['source'],
                       record['operator_word'], record['coefficient']])
    stream += word['precondition'] + word['compensation'] + word['A'] + word['cut']
    stream += b_program(word) + word['restore']
    boundary = len(stream)
    stream += word['cleanup']
    for index, gate in enumerate(stream):
        if index == boundary and check and not dual:
            for r in restored:
                require(rows[r] == {(r, ()): Q(1)}, f'restored boundary row {r}')
                require(all(not any(var == r for var, _ in row) for s, row in rows.items() if s != r),
                        f'restored boundary column {r}')
            require(all(not rows[r + 704] for r in restored), 'buffers zero before cleanup')
        kind, target = gate[:2]
        require(target in rows, 'live target')
        if kind == 'warp':
            operators = [gate[2]]
            require(operators[0] != 0 and abs(operators[0]) <= 72, 'warp id')
            rows[target] = {extend(k, operators): v for k, v in rows[target].items()}
        elif kind == 'scale':
            factor = Q(gate[2], gate[3])
            require(factor, 'nonzero scalar')
            if dual:
                factor = 1 / factor
            rows[target] = {k: factor * v for k, v in rows[target].items()}
        else:
            require(kind in ('add', 'operator_add'), 'known primitive')
            source = gate[2]
            require(source in rows and source != target, 'distinct live source')
            if kind == 'add':
                factor, operators = Q(gate[3], gate[4]), []
            else:
                factor = Q(gate[4])
                operators = list(reversed(gate[3]))
            if dual:
                target, source, factor = source, target, -factor
                if kind == 'operator_add':
                    operators = [-o for o in gate[3]]
            output = rows[target].copy()
            for term, coefficient in rows[source].items():
                key = extend(term, operators)
                value = output.get(key, Q(0)) + factor * coefficient
                if value:
                    output[key] = value
                else:
                    output.pop(key, None)
            rows[target] = output
    if check:
        for r in live:
            expected = {(r, ()): Q(1)}
            if dual and r < 112:
                expected[(r + 112, ())] = Q(-1)
            elif not dual and 112 <= r < 224:
                expected[(r - 112, ())] = Q(1)
            require(rows[r] == expected, f'endpoint {"dual" if dual else "forward"} row {r}')
        require(all(not rows[r + 704] for r in restored), 'zero private-buffer return')
    return rows


def recount(word, frames):
    traced = frames.trace(word)
    return traced, dict(sorted(Counter(traced['widths']).items()))


def algebra_fixtures():
    """Hand-derived noncommuting correction and inverse-transpose examples."""
    toy = {k: [] for k in ('precondition', 'compensation', 'A', 'B', 'cut', 'restore', 'cleanup', 'warps')}
    toy.update(removed=list(range(224, 296)), helper_final={}, initial_corrections=[
        {'target': 0, 'source': 1, 'operator_word': [1, 2], 'coefficient': '3/2'}])
    forward, dual = execute(toy, check=False), execute(toy, dual=True, check=False)
    require(forward[0] == {(0, ()): Q(1), (1, (2, 1)): Q(3, 2)}, 'ordered correction fixture')
    require(dual[1] == {(1, ()): Q(1), (0, (-1, -2)): Q(-3, 2)}, 'dual correction fixture')
    require(extend((0, (1, 2)), [-2, -1]) == (0, ()), 'inverse cancellation fixture')
    require(extend((0, (1, 2)), [-1, -2]) != (0, ()), 'noncommutativity fixture')
    return 4


def aggregate_bill(old_local, new_local):
    dispatch = read(ROOT / 'research/rank7-joint-endframes/allocation/DISPATCH.json')
    counts = Counter(row[2] for row in dispatch)
    require(counts == {'gauge44': 250, 'extra': 416}, 'published dispatch counts')
    calls = sum(counts.values())
    before = {int(k): v for k, v in read(ROOT / 'research/rank7-restore-carrier-skips/allocation/PROFILE.json').items()}
    after = {int(k): v for k, v in read(P / 'vendor/PROFILE.json').items()}
    def remainder(profile, local):
        result = {r: profile.get(r, 0) - calls * local.get(r, 0)
                  for r in profile.keys() | local.keys()}
        require(all(n >= 0 for n in result.values()), 'nonnegative conditional idle remainder')
        return {r: n for r, n in sorted(result.items()) if n}
    old_idle, new_idle = remainder(before, old_local), remainder(after, new_local)
    idle_change = delta(old_idle, new_idle)
    require(idle_change == {1: 4, 3: -63, 5: -338, 39: 1, 48: 66}, 'changed idle remainder')
    require(sum(r * n for r, n in before.items()) == sum(r * n for r, n in after.items()) == 4816512,
            'aggregate rank mass')
    require(sum(r * n for r, n in idle_change.items()) == 2 * calls, 'freed width rank-mass balance')
    return {'calls': dict(counts), 'baseline_profile': before, 'profile': after,
            'baseline_conditional_idle': old_idle, 'conditional_idle': new_idle,
            'idle_delta': idle_change, 'rank_mass': 4816512,
            'status': 'arithmetic decomposition only; owner packing and idle legality are not checked'}


def failure_controls(parent, baseline, candidate, edits, frames):
    results = {}

    def rejects(label, function):
        try:
            function()
        except ValueError as error:
            results[label] = str(error)
        else:
            raise ValueError('negative control accepted: ' + label)

    hunks = [h for edit in edits for h in edit.get('edits', [edit])]
    for carrier in (75, 84):
        bad = copy.deepcopy(candidate)
        gate = next(g for g in bad['B'] if g[0] == 'add' and g[1] == carrier and g[2] in (438, 440))
        gate[3] = -gate[3]
        bad['cleanup'] = cleanup(bad)
        rejects(f'flipped_fold_{carrier}_with_regenerated_cleanup', lambda: execute(bad))
    for index in (52, 57):
        bad = copy.deepcopy(candidate)
        new_index = index + sum(len(h['new']) - len(h['old']) for h in hunks
                                if h['section'] == 'B' and h['stop'] <= index)
        bad['B'].insert(new_index, copy.deepcopy(parent['B'][index]))
        for warp in bad['warps']:
            if warp[0] >= new_index:
                warp[0] += 1
        bad['cleanup'] = cleanup(bad)
        rejects(f'restored_old_B_{index}_with_regenerated_cleanup', lambda: execute(bad))
    bad = copy.deepcopy(candidate)
    bad['warps'] = copy.deepcopy(parent['warps'])
    bad['cleanup'] = cleanup(bad)
    rejects('unshifted_warp_chronology', lambda: execute(bad))
    bad = copy.deepcopy(candidate)
    bad['cleanup'].append(['add', 586 + 704, 0, 1, 1, [256, 128, 64, 32, 16, 8, 4, 2, 1]])
    rejects('private_buffer_pollution', lambda: execute(bad))
    bad = copy.deepcopy(candidate)
    bad['helper_final']['586'] = copy.deepcopy(candidate['helper_final']['588'])
    rejects('wrong_rank_seven_endpoint', lambda: frames.trace(bad))
    bad = copy.deepcopy(baseline)
    bad['helper_final']['586'] = copy.deepcopy(candidate['helper_final']['586'])
    rejects('endpoint_lowering_without_gate_refit', lambda: frames.trace(bad))
    return results


def audit():
    pins()
    fixtures = algebra_fixtures()
    frames = frame_module()
    spec = read(P / 'vendor/EDITS.json')
    prices = read(ROOT / 'research/rank7-joint-endframes/construction/STAGE-PRICES.json')['weights']
    tariff = {int(r): c for r, c in prices['c'].items()}
    price = lambda change: sum(tariff[r] * n for r, n in change.items())
    report = {}
    for variant in ('base', 'extra'):
        parent = read(ROOT / f'research/rank7-joint-endframes/data/WORD-{variant}.json.gz')
        candidate = read(P / f'vendor/FINAL-WORD-{variant}.json.gz')
        edits = spec['edits'][variant]
        baseline = rebuild(parent, edits[:2])
        rebuilt = rebuild(parent, edits)
        old_trace, old_widths = recount(baseline, frames)
        new_trace, new_widths = recount(rebuilt, frames)
        rebuilt['report']['local_profile'] = {str(k): v for k, v in new_trace['profile'].items()}
        rebuilt['report']['width_inventory'] = {str(k): v for k, v in new_widths.items()}
        require(rebuilt == candidate, 'full literal candidate reconstruction')
        require(old_trace['profile'] == {1: 2433, 2: 712, 3: 232, 4: 108, 5: 18, 8: 8}, 'PR3042 baseline profile')
        require(new_trace['profile'] == {1: 2433, 2: 724, 3: 228, 4: 102, 5: 20, 8: 8}, 'candidate profile')
        require(old_widths == {4: 26, 5: 2, 6: 16, 7: 52, 8: 99, 9: 213}, 'old inventory')
        require(new_widths == {4: 26, 5: 2, 6: 18, 7: 50, 8: 99, 9: 213}, 'new inventory')
        for label, word in [('baseline', baseline), ('candidate', candidate)]:
            for dual in (False, True):
                execute(word, dual)
            print('PASS_ENDPOINT', variant, label, '632 inputs, forward and dual, 91 buffers', flush=True)
        isolated = []
        for edit in edits[2:]:
            one = rebuild(parent, edits[:2] + [edit])
            one_trace, widths = recount(one, frames)
            change = delta(old_trace['profile'], one_trace['profile'])
            require(change == {2: 6, 3: -2, 4: -3, 5: 1}, 'isolated fold profile')
            require(delta(old_widths, widths) == {6: 1, 7: -1}, 'one freed width')
            execute(one)
            # A real, valid fold-only control on this literal frame path. This
            # is an upper bound on fold-only cost, not its optimized minimum.
            widened = copy.deepcopy(one)
            h = str(edit['helper'])
            widened['helper_final'][h] = parent['helper_final'][h]
            wide_trace, wide_widths = recount(widened, frames)
            execute(widened)
            wide_change = delta(old_trace['profile'], wide_trace['profile'])
            require(wide_change == {1: 1, 2: 6, 3: -2, 4: -3, 5: 1}, 'fixed-path fold-only delta')
            require(wide_widths == old_widths, 'fixed-path control keeps inventory')
            require(price(change) == -2091965 and price(wide_change) == 24706, 'surrogate local prices')
            require(-price(change) - prices['break_even'] == 665, 'surrogate guide margin')
            isolated.append({'id': edit['id'], 'profile_delta': change,
                             'width_delta': delta(old_widths, widths),
                             'fold_only_fixed_path_delta': wide_change,
                             'surrogate_coupled_price': price(change), 'surrogate_guide_margin': 665,
                             'surrogate_fold_only_fixed_path_price': price(wide_change)})
        controls = failure_controls(parent, baseline, candidate, edits, frames)
        print('PASS_FAILURE_CONTROLS', variant, len(controls), flush=True)
        report[variant] = {'baseline_profile': old_trace['profile'], 'profile': new_trace['profile'],
                           'profile_delta': delta(old_trace['profile'], new_trace['profile']),
                           'inventory': new_widths, 'isolated_folds': isolated,
                           'independent_inputs': 632, 'zero_buffers': 91,
                           'orientations': ['forward', 'dual'], 'failure_controls': controls}
    bill = aggregate_bill(old_trace['profile'], new_trace['profile'])
    return {'status': 'PASS_CARRIER_FOLD_INDEPENDENT_AUDIT', 'source_head': HEAD,
            'algebra_fixture_checks': fixtures, 'providers': report, 'aggregate_bill': bill,
            'scope': 'Exact free-operator endpoints and finite-set frame recount; '
            'native phase, ownership, physical stock, optimized single-move claims and outer admission unverified.'}


if __name__ == '__main__':
    result = audit()
    text = json.dumps(result, indent=2, sort_keys=True) + '\n'
    import sys
    if '--write-result' in sys.argv:
        (P / 'RESULT.json').write_text(text, encoding='utf-8')
    else:
        require(read(P / 'RESULT.json') == json.loads(text), 'committed result equality')
    print(result['status'], flush=True)
