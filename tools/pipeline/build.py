#!/usr/bin/env python3
"""key -> plane section -> layered DXF with SAE J1100-style dimensions/labels.
usage: build.py parts MAIN.key
       build.py dxf MAIN.key config.json out.dxf"""
import sys, json, math, numpy as np
from keyparse import read_key, to_arrays
from section import slice_mesh, chain, ray_hit
from dxfout import Dxf

PALETTE = [1,2,3,4,5,6,30,40,50,80,110,140,170,200]
GROUPS_DEFAULT = {  # layer name -> keywords in *PART title (edit to taste)
    '白车身_BIW': ['roof','pillar','floor','rocker','sill','dash','firewall','door','hood','trunk','rail','cross','member','panel','a-pillar','b-pillar'],
    '内饰_INTERIOR': ['seat','instrument','ip','console','headliner','trim','carpet','steering'],
    '密封条_SEAL': ['seal','weather','strip','gasket'],
    '玻璃_GLASS': ['glass','windshield','window','backlite'],
}

def classify(title, groups):
    t = title.lower()
    for g, kws in groups.items():
        if any(k in t for k in kws): return g
    return '其他_OTHER'

def cmd_parts(key):
    m = read_key(key); xyz, tri, pid = to_arrays(m)
    cnt = {p: int((pid == p).sum()) for p in np.unique(pid)}
    for p, c in sorted(cnt.items()): print(p, c, m['parts'].get(p, '?'))

def cmd_dxf(key, cfgp, out):
    cfg = json.load(open(cfgp)); sc = cfg.get('unit_scale', 1.0)
    m = read_key(key, search=cfg.get('include_path', [])); xyz, tri, pid = to_arrays(m); xyz = xyz * sc
    ax, val = cfg['plane']['axis'], cfg['plane']['value'] * sc
    segs, spid = slice_mesh(xyz, tri, pid, ax, val)
    xs = cfg.get('x_sign', 1.0)                           # -1 flips so vehicle front faces left/right as desired
    tf = lambda p: (p[0] * xs, p[1])
    groups = cfg.get('groups', GROUPS_DEFAULT); d = Dxf(); gcol = {}; polys_by_pid = {}
    for p in np.unique(spid):
        s = segs[spid == p] * np.array([xs, 1.0])
        pls = chain(s, cfg.get('chain_tol', 0.05)); polys_by_pid[int(p)] = pls
        title = m['parts'].get(int(p), f'PID{p}'); g = classify(title, groups)
        lay = f'{g}__{int(p)}_{title[:20]}'
        gcol.setdefault(g, PALETTE[len(gcol) % len(PALETTE)])
        d.layer(lay, gcol[g])
        for pl in pls: d.polyline(pl, lay, closed=bool(np.allclose(pl[0], pl[-1], atol=0.1)))
    P = {k: tf(v) for k, v in cfg['points'].items()}      # named reference points given as model (x,z)
    h = cfg.get('text_height', 14.0)
    for k, p in P.items():
        d.leader(p, (p[0] + 40, p[1] + 40), f'{k}', 'REF_POINTS', h)
    rear = cfg.get('rear_dir', 1.0) * xs                  # drawing-space +/-1 pointing to vehicle rear
    roof = [pl for q in cfg.get('roof_inner_pids', []) for pl in polys_by_pid.get(q, [])]
    notes = []
    for dm in cfg['dims']:
        t = dm['type']; lay = 'DIM_J1100'
        if t == 'H30':   # vertical SgRP -> AHP
            a, b = P['SgRP'], P['AHP']; c = (a[0], b[1])
            d.dim(a, c, lay, dm.get('offset', 80), h, label=f'H30 = {abs(a[1]-b[1]):.0f}')
            d.text((a[0] + 20, (a[1] + b[1]) / 2), 'H30 座椅参考点到踵点垂直高度', h * 0.8, 'ANNOTATION')
        elif t == 'L53': # horizontal SgRP -> AHP
            a, b = P['SgRP'], P['AHP']; c = (b[0], a[1])
            d.dim(a, c, lay, dm.get('offset', -80), h, label=f'L53 = {abs(a[0]-b[0]):.0f}')
            d.text((min(a[0], c[0]), a[1] - 130), 'L53 SgRP到AHP水平距离', h * 0.8, 'ANNOTATION')
        elif t == 'H61': # head room along line tilted `angle` deg from vertical toward the rear, minus offset
            ang = math.radians(dm.get('angle', 8.0)); dirv = (rear * math.sin(ang), math.cos(ang))
            hit = ray_hit(roof, P['SgRP'], dirv)
            if hit is None: notes.append('H61: ray missed roof_inner_pids'); continue
            q = tuple(hit[1]); L = hit[0] - dm.get('minus', 102.0)
            d.line(P['SgRP'], q, 'DIM_J1100')
            d.dim(P['SgRP'], q, lay, dm.get('offset', 90), h, label=f'H61 = {L:.0f} (raw {hit[0]:.0f}-{dm.get("minus",102.0):.0f})')
            d.text((q[0] + 15, q[1] + 15), 'H61 有效头部空间(8°线,至顶棚内饰)', h * 0.8, 'ANNOTATION')
        elif t == 'L34': # simplified: straight distance AHP -> SgRP in section plane (see README caveat)
            a, b = P['AHP'], P['SgRP']
            d.dim(a, b, lay, dm.get('offset', 70), h, label=f'L34* = {math.dist(a, b):.0f}')
            d.text((a[0], a[1] - 60), 'L34* 腿部空间(简化: AHP-SgRP直线距离,待核对J1100定义)', h * 0.8, 'ANNOTATION')
        elif t == 'P2P':  # generic named-point dimension
            d.dim(P[dm['a']], P[dm['b']], lay, dm.get('offset', 60), h, label=dm.get('label'))
            if 'note' in dm: 
                a, b = P[dm['a']], P[dm['b']]; d.text(((a[0]+b[0])/2, (a[1]+b[1])/2 - 40), dm['note'], h * 0.8, 'ANNOTATION')
    d.save(out); print('wrote', out, 'layers:', len(d.layers), 'entities:', len(d.ents)); [print('NOTE', n) for n in notes]

if __name__ == '__main__':
    a = sys.argv[1:]
    if a[:1] == ['parts']: cmd_parts(a[1])
    elif a[:1] == ['dxf']: cmd_dxf(a[1], a[2], a[3])
    else: print(__doc__)
