"""Dependency-free DXF (AC1009/R12) writer. Non-ASCII text is escaped as \\U+XXXX."""
import math

def _t(s):
    return ''.join(c if ord(c) < 128 else '\\U+%04X' % ord(c) for c in s)

class Dxf:
    def __init__(self):
        self.layers = {}; self.ents = []
    def layer(self, name, color=7):
        self.layers.setdefault(_t(name).upper().replace(' ', '_'), color)
        return _t(name).upper().replace(' ', '_')
    def _e(self, kind, layer, *pairs):
        s = f'0\n{kind}\n8\n{self.layer(layer)}\n'
        for c, v in pairs:
            s += f'{c}\n{v:.4f}\n' if isinstance(v, float) else f'{c}\n{v}\n'
        self.ents.append(s)
    def line(self, p, q, layer):
        self._e('LINE', layer, (10, float(p[0])), (20, float(p[1])), (30, 0.0), (11, float(q[0])), (21, float(q[1])), (31, 0.0))
    def polyline(self, pts, layer, closed=False):
        s = f'0\nPOLYLINE\n8\n{self.layer(layer)}\n66\n1\n70\n{1 if closed else 0}\n'
        for p in pts: s += f'0\nVERTEX\n8\n{self.layer(layer)}\n10\n{p[0]:.4f}\n20\n{p[1]:.4f}\n30\n0.0\n'
        self.ents.append(s + f'0\nSEQEND\n8\n{self.layer(layer)}\n')
    def text(self, p, s, h, layer, rot=0.0):
        self._e('TEXT', layer, (10, float(p[0])), (20, float(p[1])), (30, 0.0), (40, float(h)), (1, _t(s)), (50, float(rot)))
    def circle(self, c, r, layer):
        self._e('CIRCLE', layer, (10, float(c[0])), (20, float(c[1])), (30, 0.0), (40, float(r)))
    def arrow(self, tip, direction, size, layer):
        d = [direction[0], direction[1]]; n = math.hypot(*d); d = [d[0]/n, d[1]/n]
        b = (tip[0] + d[0]*size, tip[1] + d[1]*size); w = size / 6
        a = (b[0] - d[1]*w, b[1] + d[0]*w); c = (b[0] + d[1]*w, b[1] - d[0]*w)
        self.polyline([tip, a, c], layer, closed=True)
    def dim(self, p, q, layer='DIM', offset=60.0, h=12.0, label=None, fmt='%.0f'):
        """Aligned dimension (exploded: ext lines + dim line + arrows + text)."""
        dx, dy = q[0]-p[0], q[1]-p[1]; L = math.hypot(dx, dy)
        if L < 1e-6: return
        ux, uy = dx/L, dy/L; nx, ny = -uy, ux
        p2 = (p[0]+nx*offset, p[1]+ny*offset); q2 = (q[0]+nx*offset, q[1]+ny*offset)
        ex = math.copysign(h*0.4, offset)
        self.line(p, (p2[0]+nx*ex, p2[1]+ny*ex), layer); self.line(q, (q2[0]+nx*ex, q2[1]+ny*ex), layer)
        self.line(p2, q2, layer)
        self.arrow(p2, (ux, uy), h*0.8, layer); self.arrow(q2, (-ux, -uy), h*0.8, layer)
        m = ((p2[0]+q2[0])/2, (p2[1]+q2[1])/2)
        ang = math.degrees(math.atan2(dy, dx)); ang = ang if -90 <= ang <= 90 else ang+180
        txt = label or (fmt % L)
        self.text((m[0]+nx*h*0.3 - ux*len(txt)*h*0.3, m[1]+ny*h*0.3 - uy*len(txt)*h*0.3), txt, h, layer, ang)
    def leader(self, tip, to, s, layer='ANNOTATION', h=12.0):
        self.line(tip, to, layer); self.circle(tip, h*0.2, layer); self.text((to[0]+h*0.3, to[1]+h*0.3), s, h, layer)
    def save(self, path):
        o = '0\nSECTION\n2\nHEADER\n9\n$ACADVER\n1\nAC1009\n9\n$INSUNITS\n70\n4\n0\nENDSEC\n'
        o += '0\nSECTION\n2\nTABLES\n0\nTABLE\n2\nLTYPE\n70\n1\n0\nLTYPE\n2\nCONTINUOUS\n70\n0\n3\nSolid line\n72\n65\n73\n0\n40\n0.0\n0\nENDTAB\n'
        o += f'0\nTABLE\n2\nLAYER\n70\n{len(self.layers)}\n'
        for n, c in self.layers.items(): o += f'0\nLAYER\n2\n{n}\n70\n0\n62\n{c}\n6\nCONTINUOUS\n'
        o += '0\nENDTAB\n0\nENDSEC\n0\nSECTION\n2\nENTITIES\n' + ''.join(self.ents) + '0\nENDSEC\n0\nEOF\n'
        with open(path, 'w', encoding='ascii') as f: f.write(o)
