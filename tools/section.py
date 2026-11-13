import numpy as np
AX = {'x': 0, 'y': 1, 'z': 2}
UV = {'y': (0, 2), 'x': (1, 2), 'z': (0, 1)}   # drawing axes (u,v) per cut plane

def slice_mesh(xyz, tri, pid, axis='y', value=0.0):
    a = AX[axis]; d = xyz[:, a] - value; d[d == 0] = 1e-9
    dv = d[tri]; P = xyz[tri]                       # (M,3) , (M,3,3)
    pts, cr = [], []
    for i, j in ((0, 1), (1, 2), (2, 0)):
        c = (dv[:, i] > 0) != (dv[:, j] > 0)
        t = dv[:, i] / (dv[:, i] - dv[:, j] + 1e-30)
        pts.append(P[:, i] + (P[:, j] - P[:, i]) * t[:, None]); cr.append(c)
    cr = np.stack(cr, 1); pts = np.stack(pts, 1)
    sel = cr.sum(1) == 2
    order = np.argsort(~cr[sel], axis=1, kind='stable')[:, :2]
    ps = pts[sel]; r = np.arange(len(ps))[:, None]
    seg = ps[r, order]                               # (K,2,3)
    u, v = UV[axis]
    return seg[:, :, [u, v]], pid[sel]

def chain(segs, tol=0.05):
    key = lambda p: (int(round(p[0] / tol)), int(round(p[1] / tol)))
    adj = {}
    for i, s in enumerate(segs):
        for e in (0, 1): adj.setdefault(key(s[e]), []).append((i, e))
    used = np.zeros(len(segs), bool); out = []
    def walk(pt):
        res = []
        while True:
            nxt = [(i, e) for i, e in adj.get(key(pt), []) if not used[i]]
            if not nxt: return res
            i, e = nxt[0]; used[i] = True; pt = segs[i][1 - e]; res.append(pt)
    for i in range(len(segs)):
        if used[i]: continue
        used[i] = True
        fw = walk(segs[i][1]); bw = walk(segs[i][0])
        line = bw[::-1] + [segs[i][0], segs[i][1]] + fw
        out.append(np.array(line))
    return out

def ray_hit(polys, p, d):
    """nearest intersection of ray p + t d (t>0) with polylines; returns (t, point) or None"""
    best = None; p = np.asarray(p, float); d = np.asarray(d, float)
    for pl in polys:
        a, b = pl[:-1], pl[1:]; e = b - a
        den = d[0] * e[:, 1] - d[1] * e[:, 0]
        ok = np.abs(den) > 1e-12
        w = a - p
        t = np.where(ok, (w[:, 0] * e[:, 1] - w[:, 1] * e[:, 0]) / np.where(ok, den, 1), -1)
        s = np.where(ok, (w[:, 0] * d[1] - w[:, 1] * d[0]) / np.where(ok, den, 1), -1)
        hit = ok & (t > 1e-9) & (s >= 0) & (s <= 1)
        for ti in t[hit]:
            if best is None or ti < best[0]: best = (ti, p + ti * d)
    return best
