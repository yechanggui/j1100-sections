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
    m = model or {'nodes': {}, 'shells': [], 'parts': {}}
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
            elif kw == '*PART':
                part_line += 1
                if part_line == 1: title = line.strip()
                elif part_line == 2:
                    m['parts'][int(line[:10])] = title
    return m

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
    return xyz, np.vstack(tri), np.concatenate([pid, pid[quad]])
