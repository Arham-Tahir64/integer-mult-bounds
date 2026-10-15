"""Exact intrinsic wrappers for PR2586; no compiler import or network required."""
from collections import Counter
import argparse
import copy
import gzip
import hashlib
import io
import json
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile
import types

P = Path(__file__).resolve().parent
ROOT = P.parents[1]
BASE = 'research/p104-native-channel/'
OLD = 'research/p104-physical-corrected-dual'


def need(ok, message):
    if not ok:
        raise ValueError(message)


def read_json(path):
    def pairs(items):
        out = {}
        for key, value in items:
            need(key not in out, 'duplicate JSON key: ' + key)
            out[key] = value
        return out
    return json.loads(path.read_text(encoding='utf-8'), object_pairs_hook=pairs)


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def authenticate():
    """Check every external input before executing any retained source."""
    sources = read_json(P / 'SOURCES.json')
    live = {}
    for item in sources['files']:
        if item['usage'] == 'input':
            raw = (ROOT / item['path']).read_bytes()
            need(digest(raw) == item['sha256'], 'source SHA256: ' + item['path'])
            blob = hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest()
            need(blob == item['git_blob'], 'source Git blob: ' + item['path'])
            live[item['path']] = raw
    pin = read_json(P / 'PREDECESSOR.json')
    need(pin['head'] == '7953c9a8f788a8de5cf2ced63d9a61b67c22c6f1', 'PR2586 head')
    raw = (P / pin['archive']).read_bytes()
    need(digest(raw) == pin['archive_sha256'], 'predecessor archive SHA256')
    expected = {item['path']: item for item in pin['files']}
    retained = {}
    with tarfile.open(fileobj=io.BytesIO(gzip.decompress(raw)), mode='r:') as archive:
        for member in archive.getmembers():
            if member.isdir():
                continue
            need(member.isfile() and member.name in expected and member.name not in retained,
                 'unexpected or duplicate archive member')
            content = archive.extractfile(member).read()
            item = expected[member.name]
            need(digest(content) == item['sha256'], 'retained source SHA256: ' + member.name)
            blob = hashlib.sha1(b'blob ' + str(len(content)).encode() + b'\0' + content).hexdigest()
            need(blob == item['git_blob'], 'retained source Git blob')
            retained[member.name] = content
    need(set(retained) == set(expected), 'complete predecessor archive')
    return live, retained


def interpreter(raw):
    module = types.ModuleType('p104_intrinsic_gaussian')
    exec(compile(raw, BASE + 'vendor/native_verify.py', 'exec'), module.__dict__)
    return module


def conjugate(gates):
    out = []
    for gate in gates:
        tag = gate[0]
        if tag == 'C':
            out.append(('C', gate[1], -gate[2]))
        elif tag == 'D':
            out.append(('D', tuple(gate[1]), tuple(-v % 4 for v in gate[2])))
        elif tag == 'phase':
            out.append(('phase', -gate[1] % 4))
        else:
            need(tag in ('P', 'X'), 'conjugation gate')
            out.append(gate)
    return tuple(out)


def dual_record(record):
    """A unitary monomial's inverse transpose is its entrywise conjugate."""
    need(record['rank'] == 0 and record['right'] is None, 'rank-zero adapter')
    out = copy.deepcopy(record)
    out['left']['phase'] = -out['left']['phase'] % 4
    out['left']['linear_Z4'] = [-v % 4 for v in out['left']['linear_Z4']]
    # Off-diagonal quadratic contributions are 2 mod 4, fixed by negation.
    return out


def check_adapter(N, item, word, dual):
    where, name = item['position'], item['register']
    q, frame = item['normal'], tuple(item['frame'])
    need(type(q) is int and 0 < q < 512 and q.bit_count() % 2 == 1, 'odd root normal')
    g = N.frame(frame, 9)
    if where == 'entry':
        need(name.startswith('X') and frame == (q,), 'source entry binding')
        need(word['initial_frames'][name] == list(frame), 'canonical input frame')
        intrinsic = (('C', q, 1),)
        forward = N.adjoint(intrinsic) + g
        left = conjugate(intrinsic) + N.recipe(dual)
        right = conjugate(g)
    else:
        need(where == 'exit' and name.startswith('Y'), 'target exit binding')
        need(len(frame) == 8 and all((q & v).bit_count() % 2 == 0 for v in frame),
             'target hyperplane binding')
        need(word['final_frames'][name] == list(frame), 'canonical output frame')
        intrinsic = (('C', q, -1),) + N.fourier(9)
        forward = N.adjoint(g) + intrinsic
        left = conjugate(g) + N.recipe(dual)
        right = conjugate(intrinsic)
    N.equal(N.recipe(item['recipe']), forward, 'forward intrinsic adapter phase')
    N.equal(N.recipe(dual), conjugate(forward), 'dual intrinsic adapter phase')
    N.equal(left, right, 'literal intrinsic boundary composition')


def complete_columns(N, forward, dual):
    """Independent sparse monomial inverse-transpose, on all 512 columns."""
    action = {}
    images = set()
    for x in range(512):
        column, den = N.state(forward, x)
        need(den == 0 and len(column) == 1, 'unit monomial column')
        y, (a, b) = next(iter(column.items()))
        need(a*a + b*b == 1 and y not in images, 'unitary monomial bijection')
        images.add(y)
        action[x] = (y, a, b)
    # If M[y,x]=z, then (M^-T)[y,x]=z^-1. Derive this from
    # the explicit bijection, without using the recipe conjugation switch.
    for x, (y, a, b) in action.items():
        column, den = N.state(dual, x)
        need(den == 0 and column == {y: (a, -b)}, 'all inverse-transpose monomial columns')
    return 512


def replay_predecessor(live, retained):
    with tempfile.TemporaryDirectory(prefix='p104-intrinsic-source-') as directory:
        root = Path(directory)
        for name, raw in (live | retained).items():
            need(name.startswith('research/') and '..' not in Path(name).parts, 'bounded replay path')
            path = root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(raw)
        result = subprocess.run([sys.executable, '-I', '-O', '-B', str(root / OLD / 'verify.py')],
                                capture_output=True, text=True, timeout=300, check=True)
        need('PASS_P104_PHYSICAL_CORRECTED_DUAL' in result.stdout, 'predecessor full replay')
    return json.loads(retained[OLD + '/RESULT.json'])


def compute():
    live, retained = authenticate()
    predecessor = replay_predecessor(live, retained)
    N = interpreter(live[BASE + 'vendor/native_verify.py'])
    native = json.loads(gzip.decompress(live[BASE + 'NATIVE-RECIPES.json.gz']))
    word = json.loads(retained[OLD + '/WORD.json'])
    adapters = native['endpoint_adapters']
    expected = {('entry', 'X' + str(i)) for i in range(104)} | {
        ('exit', 'Y' + str(i)) for i in range(104)}
    seen = set()
    columns = 0
    records = []
    for item in adapters:
        key = item['position'], item['register']
        need(key in expected and key not in seen, 'unique complete adapter binding')
        seen.add(key)
        record = dual_record(item['recipe'])
        check_adapter(N, item, word, record)
        columns += complete_columns(N, N.recipe(item['recipe']), N.recipe(record))
        records.append({'position': key[0], 'register': key[1], 'normal': item['normal'],
                        'frame': item['frame'], 'recipe': record})
    need(seen == expected, 'all 208 intrinsic endpoints')
    profiles = Counter(e[4] for e in word['program'] if e[0] == 'transport')
    need(dict(sorted(profiles.items())) == {int(k): v for k, v in predecessor['logical']['profile'].items()},
         'unchanged complete positive profile')
    controls = []

    def reject(name, fn):
        try:
            fn()
        except ValueError:
            controls.append(name)
        else:
            raise ValueError('fault falsely accepted: ' + name)

    probe = next(item for item in adapters if
                 N.state(N.recipe(item['recipe'])) != N.state(N.recipe(dual_record(item['recipe']))))
    good = dual_record(probe['recipe'])
    bad = copy.deepcopy(good)
    bad['left']['phase'] = (bad['left']['phase'] + 1) % 4
    reject('wrapper global phase', lambda: check_adapter(N, probe, word, bad))
    reject('unconjugated wrapper', lambda: check_adapter(N, probe, word, probe['recipe']))
    reject('adjoint instead of inverse transpose', lambda: N.equal(
        N.adjoint(N.recipe(probe['recipe'])), N.recipe(good), 'wrong adjoint'))
    reject('missing wrapper', lambda: N.equal((), N.recipe(good), 'omitted intrinsic wrapper'))
    other = next(item for item in adapters if item['position'] == probe['position'] and
                 item['register'] != probe['register'] and item['frame'] != probe['frame'])
    reject('wrong port wrapper', lambda: check_adapter(N, probe, word, dual_record(other['recipe'])))
    entry = next(item for item in adapters if item['position'] == 'entry')
    reject('unconjugated intrinsic input contract', lambda: N.equal(
        (('C', entry['normal'], 1),), (('C', entry['normal'], -1),), 'wrong external chart'))
    # A separate noncommuting fixture tests the general product law. The actual
    # source adapters can commute with their endpoint charts; that is allowed.
    A = (('P', (2, 1, 4, 8, 16, 32, 64, 128, 256)), ('X', 1))
    B = (('D', (1, 0, 0, 0, 0, 0, 0, 0, 0), (1, 0, 0, 0, 0, 0, 0, 0, 0)), ('phase', 1))
    F = N.fourier(9)

    def transpose(gates):
        return tuple(('P', N.inverse(tuple(g[1]))) if g[0] == 'P' else g
                     for g in reversed(gates))

    lhs = transpose(N.adjoint(A + F + B))
    rhs = transpose(N.adjoint(A)) + transpose(N.adjoint(F)) + transpose(N.adjoint(B))
    N.equal(lhs, rhs, 'inverse transpose product positive control')
    reject('reversed inverse-transpose product', lambda: N.equal(
        lhs, transpose(N.adjoint(B)) + transpose(N.adjoint(F)) + transpose(N.adjoint(A)),
        'reversed product order'))
    payload = json.dumps(records, sort_keys=True, separators=(',', ':')).encode()
    return {'schema_version': 1, 'status': 'PASS_P104_PHYSICAL_DUAL_INTRINSIC_ENDPOINTS',
            'predecessor_head': '7953c9a8f788a8de5cf2ced63d9a61b67c22c6f1',
            'predecessor_full_replay': True, 'public_roles': 358,
            'predecessor_boundary_coefficients': predecessor['logical']['boundary_coefficients'],
            'input_X_adapters': 104, 'output_Y_adapters': 104,
            'exact_monomial_columns': columns, 'adapter_records_sha256': digest(payload),
            'added_positive_children': 0, 'added_rank_mass': 0,
            'retained_positive_profile': dict(sorted(profiles.items())),
            'retained_rank_mass': sum(k*v for k, v in profiles.items()),
            'retained_events': len(word['program']), 'wrapped_event_count': len(word['program']) + len(records),
            'retained_private_zero_erases': len(predecessor['logical']['private_zero_erases']),
            'controls': controls, 'no_new_kappa': True}, records


def validate_receipt(result, expected):
    need(json.dumps(result, sort_keys=True) == json.dumps(expected, sort_keys=True), 'complete typed receipt')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path)
    parser.add_argument('--adapters-out', type=Path)
    args = parser.parse_args()
    outputs = [path.resolve() for path in (args.out, args.adapters_out) if path is not None]
    need(len(outputs) == len(set(outputs)), 'distinct output files')
    for path in outputs:
        need(not path.exists(), 'exclusive new output')
    result, adapters = compute()
    if args.out:
        with args.out.open('x', encoding='utf-8', newline='\n') as out:
            out.write(json.dumps(result, indent=2) + '\n')
    else:
        expected = read_json(P / 'RESULT.json')
        validate_receipt(result, expected)
    if args.adapters_out:
        with args.adapters_out.open('x', encoding='utf-8', newline='\n') as out:
            out.write(json.dumps(adapters, sort_keys=True, separators=(',', ':')))
    print(result['status'] + ' adapters=208 columns=106496 added_rank=0 retained_mass=3542')


if __name__ == '__main__':
    main()
