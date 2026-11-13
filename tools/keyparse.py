"""Minimal LS-DYNA .key reader: *NODE, *ELEMENT_SHELL, *PART, *INCLUDE (fixed 8/16-col or comma format)."""
import os, numpy as np

def _ints(line, w=8, n=8):
    if ',' in line:
        return [int(float(t)) for t in line.split(',') if t.strip()]
    return [int(line[i*w:(i+1)*w]) for i in range(n) if line[i*w:(i+1)*w].strip()]

def _floats(line):
    if ',' in line:
        t = line.split(',')
        return int(t[0]), [float(x) for x in t[1:4]]
    try:
        return int(line[:8]), [float(line[8+16*i:24+16*i]) for i in range(3)]
    except ValueError:
        t = line.split()
        return int(t[0]), [float(x) for x in t[1:4]]

def read_key(path, model=None, search=()):
    m = model or {'nodes': {}, 'shells': [], 'solids': [], 'parts': {}}
    base = os.path.dirname(os.path.abspath(path))
    kw, part_line, inc_next = None, 0, False
    with open(path, 'r', errors='replace') as f:
        for raw in f:
            line = raw.rstrip('\r\n')
            if not line.strip() or line.startswith('$'):
                continue
            if line.startswith('*'):
                kw = line.strip().upper().split()[0]; part_line = 0
                inc_next = kw == '*INCLUDE'
                continue
            if kw == '*INCLUDE' and inc_next:
                name = line.strip()
                for d in (base, *search):
                    p = os.path.join(d, name)
                    if os.path.exists(p):
                        read_key(p, m, search); break
                else:
                    print('WARN include not found:', name)
                inc_next = False
            elif kw == '*NODE':
                nid, xyz = _floats(line); m['nodes'][nid] = xyz
            elif kw == '*ELEMENT_SHELL':
                v = _ints(line)
                if len(v) >= 6: m['shells'].append(v[:6])
            elif kw == '*ELEMENT_SOLID':
                v = _ints(line, 8, 10)
                if len(v) >= 10: m['solids'].append(v[:10])
            elif kw == '*PART':
                part_line += 1
                if part_line == 1: title = line.strip()
                elif part_line == 2:
                    m['parts'][int(line[:10])] = title
    return m

HEX_FACES = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]

def solid_skin(sol, ids):
    """Exterior faces of solid elements (hex/wedge/tet in 8-node form) -> triangles (row indices), pids."""
    if len(sol) == 0: return np.zeros((0, 3), np.int64), np.zeros(0, np.int64)
    sol = np.asarray(sol, np.int64); pid = sol[:, 1]; n = sol[:, 2:10]
    nuniq = np.array([len(set(r)) for r in n.tolist()])
    quads, qpid = [], []
    tet = nuniq == 4
    if tet.any():
        t = n[tet][:, :4]
        for f in ((0, 1, 2), (0, 1, 3), (1, 2, 3), (2, 0, 3)):
            quads.append(np.column_stack([t[:, f], t[:, f[2]]])); qpid.append(pid[tet])
    o = ~tet
    for f in HEX_FACES:
        quads.append(n[o][:, list(f)]); qpid.append(pid[o])
    Q = np.vstack(quads); P = np.concatenate(qpid)
    # drop faces that collapse to < 3 distinct nodes
    srt = np.sort(Q, axis=1)
    distinct = 1 + (np.diff(srt, axis=1) != 0).sum(1)
    keep = distinct >= 3; Q, P, srt = Q[keep], P[keep], srt[keep]
    # canonical key on the distinct node set (handles quad-vs-collapsed-quad sharing)
    key = np.where(np.concatenate([np.ones((len(srt), 1), bool), np.diff(srt, axis=1) != 0], 1), srt, -1)
    key = np.sort(key, axis=1)
    _, inv, cnt = np.unique(key, axis=0, return_inverse=True, return_counts=True)
    ext = cnt[inv.ravel()] == 1; Q, P = Q[ext], P[ext]
    tri = np.vstack([Q[:, [0, 1, 2]], Q[:, [0, 2, 3]]]); tp = np.concatenate([P, P])
    good = (tri[:, 0] != tri[:, 1]) & (tri[:, 1] != tri[:, 2]) & (tri[:, 0] != tri[:, 2])
    tri, tp = tri[good], tp[good]
    return np.searchsorted(ids, tri), tp

def to_arrays(m):
    ids = np.fromiter(m['nodes'].keys(), dtype=np.int64)
    xyz = np.array(list(m['nodes'].values()), dtype=float)
    o = np.argsort(ids); ids, xyz = ids[o], xyz[o]
    sh = np.array(m['shells'], dtype=np.int64)
    pid = sh[:, 1]
    n = np.searchsorted(ids, sh[:, 2:6])           # node id -> row
    tri = [n[:, [0, 1, 2]]]
    quad = sh[:, 5] != sh[:, 4]
    tri.append(n[quad][:, [0, 2, 3]])
    st, sp = solid_skin(m.get('solids', []), ids)
    tri.append(st)
    return xyz, np.vstack(tri), np.concatenate([pid, pid[quad], sp])
