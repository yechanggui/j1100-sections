#!/usr/bin/env python3
"""Cut sections from an LS-DYNA model and write site data.
usage: python3 tools/gen_sections.py MODEL.key tools/vehicle.json data/
Writes data/<id>.dxf per section and data/vehicle.json (sections, layer groups, reference-point estimates).
Drawing axes follow SAE J182: X rearward +, Y left +, Z up +."""
import sys, os, json, numpy as np
sys.path.insert(0, os.path.dirname(__file__))
from keyparse import read_key, to_arrays
from section import slice_mesh, chain, ray_hit
from classify import classify
from dxfout import Dxf

GROUP_COLOR = {'BIW': 5, 'DOOR': 4, 'GLASS': 3, 'TRIM': 30, 'SEAL': 1, 'SEAT': 8, 'STRUCT': 140, 'STEERING': 9, 'PEDAL': 6, 'OTHER': 9}

def to_j182(xyz, cfg):
    """model -> J182 axes: flip each axis per cfg['axis_sign'] (e.g. Camry: x front-positive -> flip)."""
    return xyz * np.array(cfg.get('axis_sign', [1, 1, 1]), float)

def main(key, cfgp, out):
    cfg = json.load(open(cfgp)); os.makedirs(out, exist_ok=True)
    m = read_key(key); xyz, tri, pid = to_arrays(m); xyz = to_j182(xyz, cfg)
    titles = m['parts']; group = {p: classify(t) for p, t in titles.items()}
    meta = dict(vehicle=cfg['vehicle'], source=cfg['source'], units='mm', axes='SAE J182: X rearward +, Y left +, Z up +',
                sections=[], refs=cfg['refs'])
    for sc in cfg['sections']:
        segs, spid = slice_mesh(xyz, tri, pid, sc['axis'], sc['value'])
        u = {'y': 'X', 'x': 'Y', 'z': 'X'}[sc['axis']]; v = {'y': 'Z', 'x': 'Z', 'z': 'Y'}[sc['axis']]
        d = Dxf(); layers = {}
        for p in np.unique(spid):
            p = int(p); g = group.get(p, 'OTHER'); t = titles.get(p, f'PID{p}')
            lay = f'{g}__{p}_{t}'[:60]
            d.layer(lay, GROUP_COLOR.get(g.split('-')[0], 7)); layers[d.layer(lay)] = dict(group=g, pid=p, title=t)
            for pl in chain(segs[spid == p], 0.05):
                if len(pl) < 2: continue
                d.polyline(pl, lay, closed=bool(len(pl) > 3 and np.allclose(pl[0], pl[-1], atol=0.1)))
        f = f"{sc['id']}.dxf"; d.save(os.path.join(out, f))
        meta['sections'].append(dict(id=sc['id'], title=sc['title'], file=f, plane=f"{sc['axis'].upper()} = {sc['value']}", axis=sc['axis'],
                                     value=sc['value'], u=u, v=v, desc=sc.get('desc', ''), layers=layers))
        print(sc['id'], len(layers), 'parts', os.path.getsize(os.path.join(out, f)) // 1024, 'KB')
    json.dump(meta, open(os.path.join(out, 'vehicle.json'), 'w'), ensure_ascii=False, indent=1)

if __name__ == '__main__':
    main(*sys.argv[1:4])
