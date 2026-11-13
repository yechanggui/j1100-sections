#!/usr/bin/env python3
"""Generate ILLUSTRATIVE demo sections (NOT real vehicle data) + semantics.json.
run: python3 tools/gen_demo.py   (from repo root)"""
import json, math, os, sys, numpy as np
sys.path.insert(0, os.path.dirname(__file__))
from dxfout import Dxf
from section import ray_hit

OUT = os.path.join(os.path.dirname(__file__), '..', 'data')
COL = {'ANNOT': 7, 'BIW': 5, 'DOOR': 4, 'GLASS': 3, 'TRIM': 30, 'SEAL': 1, 'SEAT': 8, 'REF': 6, 'DIM': 2, 'ANNOT': 7, 'GROUND': 8}
def col(layer): return COL.get(layer.split('-')[0], 7)

class Sec:
    def __init__(s, sid, title, fname, plane, desc, h=12):
        s.h = h; s.d = Dxf(); s.items = []; s.meta = dict(id=sid, title=title, file=fname, plane=plane, desc=desc)
    def pl(s, layer, pts, closed=False):
        s.d.layer(layer, col(layer)); s.d.polyline(pts, layer, closed)
    def ref(s, name, p, note=''):
        s.d.layer('REF-POINTS', 6); s.d.leader(p, (p[0] + 35, p[1] + 35), name + (' ' + note if note else ''), 'REF-POINTS', s.h)
    def dim(s, p, q, **k):
        """k: id, code, std, name_cn, name_en, label, offset, drives, envelope, dts_key, status, definition, value(optional)"""
        v = k.get('value', math.dist(p, q)); s.d.layer('DIM-J1100' if k['std'].startswith('SAE') else 'DIM-OEM', 2)
        lay = 'DIM-J1100' if k['std'].startswith('SAE') else 'DIM-OEM'
        off = k.get('offset', 60) * s.h / 12 if s.h != 12 else k.get('offset', 60)
        s.d.dim(p, q, lay, off, s.h, label=k['code'] + ' = ' + (k.get('label') or '%.0f' % v))
        dx, dy = q[0] - p[0], q[1] - p[1]; L = math.hypot(dx, dy) or 1; nx, ny = -dy / L, dx / L
        mid = ((p[0] + q[0]) / 2, (p[1] + q[1]) / 2); e = off + math.copysign(s.h * 2.4, off)
        s.d.layer('ANNOT-DTS', 7); s.d.text((mid[0] + nx * e, mid[1] + ny * e), '[DTS] ' + k['dts_key'], s.h * 0.7, 'ANNOT-DTS')
        s.items.append(dict(id=k['id'], code=k['code'], std=k['std'], name_cn=k['name_cn'], name_en=k['name_en'], value=round(v, 1), unit='mm',
            definition=k.get('definition', ''), anchors=[list(p), list(q)], drives=k.get('drives', []), envelope=k.get('envelope', ''),
            dts_key=k['dts_key'], dts_target=None, status=k.get('status', 'verify-definition')))
    def save(s):
        s.d.save(os.path.join(OUT, s.meta['file'])); r = dict(s.meta); r['items'] = s.items; return r

secs = []
# ---------------- A: longitudinal centre section (Y=0) ----------------
A = Sec('A', 'A-A 纵向中心截面 (Y=0) · 乘员舱布置', 'sec_A_longitudinal.dxf', 'Y=0, 视图 X向后为正 / Z向上 (SAE J182)',
        '乘员舱纵向包络：地板、前围、顶盖、风挡、顶棚与座椅参考点(SgRP)/踵点(AHP)。', h=38)
roof = [(250, 1210), (900, 1235), (1500, 1215), (1900, 1130)]
A.pl('BIW-ROOF-OUTER', roof); A.pl('BIW-ROOF-INNER', [(x, z - 25) for x, z in roof])
head = [(260, 1130), (900, 1160), (1500, 1145), (1860, 1075)]; A.pl('TRIM-HEADLINER', head)
A.pl('BIW-FLOOR', [(-100, 320), (1100, 300), (1500, 330), (1900, 420)]); A.pl('TRIM-CARPET', [(-60, 335), (1100, 316), (1480, 346)])
A.pl('BIW-DASH', [(-100, 320), (-150, 880), (-120, 940)]); A.pl('GLASS-WINDSHIELD', [(-120, 940), (250, 1195)])
A.pl('SEAT-SCHEMATIC', [(700, 360), (700, 520), (1000, 560), (1100, 880), (1060, 900)])
SgRP, AHP = (950, 600), (150, 330)
A.ref('SgRP', SgRP); A.ref('AHP', AHP)
A.dim(SgRP, (SgRP[0], AHP[1]), id='A-H30', code='H30', std='SAE J1100', name_cn='座椅参考点到踵点垂直距离', name_en='SgRP to AHP, vertical',
      offset=-90, definition='SgRP 与 AHP 的垂直距离（沿 Z）。', drives=['BIW-FLOOR', 'TRIM-CARPET', 'SEAT-SCHEMATIC'],
      envelope='决定前地板/脚部区地板高度与座椅安装点高度，约束地板截面包络。', dts_key='pkg.seat.h30_sgrp_to_ahp_z')
A.dim(SgRP, (AHP[0], SgRP[1]), id='A-L53', code='L53', std='SAE J1100', name_cn='座椅参考点到踵点水平距离', name_en='SgRP to AHP, horizontal',
      offset=-130, definition='SgRP 与 AHP 的水平距离（沿 X）。', drives=['BIW-DASH', 'BIW-FLOOR', 'SEAT-SCHEMATIC'],
      envelope='决定前围板位置与脚部空间，约束前围/地板过渡截面。', dts_key='pkg.seat.l53_sgrp_to_ahp_x')
a = math.radians(8); dirv = (math.sin(a), math.cos(a)); hit = ray_hit([np.array(head)], SgRP, dirv)
q = tuple(float(v) for v in hit[1]); A.d.line(SgRP, q, 'DIM-J1100')
A.dim(SgRP, q, id='A-H61', code='H61', std='SAE J1100', name_cn='有效头部空间（前排）', name_en='Effective head room, front',
      offset=-100, value=hit[0] - 102, label='%.0f (沿8°线 %.0f − 102)' % (hit[0] - 102, hit[0]), definition='自 SgRP 沿后倾 8° 直线量至顶棚内饰，再按 J1100 规则扣减（此处 102 mm 为待核对参数）。',
      drives=['BIW-ROOF-OUTER', 'BIW-ROOF-INNER', 'TRIM-HEADLINER'], envelope='顶盖外板→内板→顶棚的垂向包络上边界；决定顶盖高度、顶盖下沉量与顶棚厚度。', dts_key='pkg.head.h61_effective_front')
A.dim(AHP, SgRP, id='A-L34', code='L34*', std='SAE J1100', name_cn='最大有效腿部空间（简化）', name_en='Max effective leg room (simplified)',
      offset=-60, definition='简化为 AHP–SgRP 直线距离；真实 L34 定义需对照 J1100 原文。', drives=['BIW-DASH', 'BIW-FLOOR', 'TRIM-CARPET'],
      envelope='前围与踏板区包络。', dts_key='pkg.leg.l34_max_effective_accel', status='simplified')
secs.append(A.save())

# ---------------- B: roof-side cross-section (X plane) ----------------
B = Sec('B', 'B-B 顶盖-侧围-车门横截面 (X=B柱附近)', 'sec_B_roofside.dxf', 'X=常数, 左半车; 横轴 Y向外 / Z向上',
        '顶盖边梁、顶棚、侧窗玻璃、门内饰板与门框密封条的横向包络。', h=18)
B.pl('BIW-ROOF-OUTER', [(0, 1250), (300, 1243), (520, 1215), (640, 1180), (700, 1150)])
B.pl('BIW-ROOF-INNER', [(0, 1228), (300, 1221), (520, 1195), (600, 1168)])
B.pl('BIW-RAIL', [(560, 1110), (690, 1110), (700, 1150), (600, 1170), (560, 1170)], True)
B.pl('TRIM-HEADLINER', [(0, 1180), (300, 1175), (500, 1155), (580, 1125), (610, 1100)])
B.pl('GLASS-SIDE', [(690, 1105), (735, 720)]); B.pl('DOOR-INNER', [(710, 1000), (745, 700), (745, 480)])
B.pl('TRIM-DOOR', [(680, 1010), (700, 800), (690, 760), (680, 720), (712, 700), (716, 520)])
B.pl('BIW-SIDE-OUTER', [(830, 1100), (850, 900), (868, 500)]); B.pl('DOOR-OUTER', [(790, 1085), (840, 900), (868, 520)])
B.pl('SEAL-DOOR-PRIMARY', [(695, 1085), (735, 1085), (740, 1115), (700, 1118)], True); B.pl('SEAL-GLASSRUN', [(690, 1105), (700, 1112), (712, 1105)])
B.pl('GROUND-CL', [(0, 0), (0, 1300)])
Sh, El = (700, 800), (680, 720); B.ref('肩部点', Sh); B.ref('肘部点', El)
B.dim((0, Sh[1]), Sh, id='B-W3', code='W3/2', std='SAE J1100', name_cn='肩部空间（半宽，×2=W3）', name_en='Shoulder room (half; W3 = 2×)', value=700, label='700 → W3 = 1400',
      offset=-70, definition='左右侧内饰板在肩部高度处的横向间距；半车截面标注半宽。', drives=['TRIM-DOOR', 'DOOR-INNER', 'BIW-SIDE-OUTER'], envelope='决定侧围/车门内外板与门内饰的横向包络。', dts_key='pkg.width.w3_shoulder_front')
B.dim((0, El[1]), El, id='B-W31', code='W31/2', std='SAE J1100', name_cn='肘部空间（半宽，×2=W31）', name_en='Elbow room (half; W31 = 2×)', value=680, label='680 → W31 = 1360',
      offset=70, definition='肘部高度处左右门内饰（含扶手）横向间距；该项为你提供的术语，编号待核对。', drives=['TRIM-DOOR', 'DOOR-INNER'], envelope='扶手/门内饰型面包络。', dts_key='pkg.width.w31_elbow_front')
B.dim((300, 1175), (300, 1221), id='B-HIC', code='HIC-GAP', std='OEM通用', name_cn='头部撞击缓冲间隙（顶棚-顶盖内板）', name_en='Headliner to roof-inner clearance', offset=-60, status='target-needed',
      definition='顶棚下表面到顶盖内板上表面的垂向间隙，用于头部碰撞(FMVSS 201/ECE-R21类)缓冲。', drives=['TRIM-HEADLINER', 'BIW-ROOF-INNER'], envelope='决定顶棚结构与顶盖内板的间距。', dts_key='safety.head_impact.headliner_clearance')
B.dim((690, 1105), (735, 720), id='B-GLASS', code='GLASS-H', std='OEM通用', name_cn='侧窗玻璃可视高度（本截面）', name_en='Side glass visible height (this section)', offset=60, status='target-needed',
      definition='本截面上玻璃上缘到腰线下缘的长度；J1100 的 DLO（采光口）需在侧视图而非本截面中度量。', drives=['GLASS-SIDE', 'SEAL-GLASSRUN'], envelope='侧窗采光口上缘由门框/密封条上边界约束。', dts_key='pkg.dlo.side_glass_height_section')
secs.append(B.save())

# ---------------- C: sill + lower door seal ----------------
C = Sec('C', 'C-C 门槛-车门下部密封截面', 'sec_C_sill_seal.dxf', 'X=常数, 左侧门槛; 横轴 Y向外 / Z向上',
        '门槛内/外板、车门下缘、密封条（自由态与压缩态）、门槛饰板，及间隙/面差。', h=10)
C.pl('BIW-SILL-INNER', [(700, 160), (800, 160), (800, 300), (700, 300)], True)
C.pl('BIW-SILL-OUTER', [(800, 150), (850, 150), (868, 320), (800, 320)])
C.pl('DOOR-OUTER', [(870, 326), (870, 480)]); C.pl('DOOR-INNER', [(800, 350), (800, 480)]); C.pl('DOOR-HEM', [(800, 326), (870, 326)])
C.pl('SEAL-DOOR-FREE', [(772, 300), (800, 300), (800, 345), (772, 345)], True)
C.pl('SEAL-DOOR-PRIMARY', [(778, 305), (800, 305), (800, 340), (778, 340)], True)
C.pl('TRIM-SILL-SCUFF', [(690, 305), (770, 305), (770, 325), (690, 325)], True); C.pl('GROUND-LINE', [(600, 0), (950, 0)])
C.dim((868, 320), (870, 326), id='C-GAP', code='GAP', std='OEM通用', name_cn='门下缘-门槛外板间隙', name_en='Door-to-sill gap', value=6, label='6 (目标待定)', offset=-60, status='target-needed',
      definition='车门下缘与门槛外板之间的间隙，通常由 DTS 的 Gap & Flush 目标给出。', drives=['DOOR-OUTER', 'BIW-SILL-OUTER'], envelope='决定门下缘与门槛外板的相对位置。', dts_key='gapflush.door_sill.gap')
C.dim((868, 320), (870, 320), id='C-FLUSH', code='FLUSH', std='OEM通用', name_cn='门-门槛面差', name_en='Door-to-sill flush', value=2, label='2 (目标待定)', offset=70, status='target-needed',
      definition='门外板与门槛外板在 Y 向的面差。', drives=['DOOR-OUTER', 'BIW-SILL-OUTER'], envelope='外观面包络。', dts_key='gapflush.door_sill.flush')
C.dim((790, 300), (790, 345), id='C-SEAL-FREE', code='SEAL-H0', std='OEM通用', name_cn='密封条自由态高度', name_en='Seal free height', offset=-45, status='target-needed',
      definition='密封条未压缩的截面高度。', drives=['SEAL-DOOR-FREE'], envelope='密封条型面。', dts_key='seal.door_primary.free_height')
C.dim((790, 305), (790, 340), id='C-SEAL-CMP', code='SEAL-H1', std='OEM通用', name_cn='密封条压缩态高度', name_en='Seal compressed height', offset=-90, status='target-needed',
      definition='关门状态下的截面高度；压缩量 = H0 − H1，压缩率需落在 DTS 给定区间。', drives=['SEAL-DOOR-PRIMARY'], envelope='密封条与门/门槛接触包络。', dts_key='seal.door_primary.compressed_height')
C.dim((868, 0), (868, 320), id='C-SILL-H', code='H-SILL', std='OEM通用', name_cn='门槛外板上缘离地高度', name_en='Sill top height above ground', offset=65, status='target-needed',
      definition='地面相关尺寸，沿地面法向（J1100 约定）。', drives=['BIW-SILL-OUTER'], envelope='门槛高度/上下车便利性。', dts_key='pkg.entry.sill_height')
secs.append(C.save())

# side-view / table-only items (not drawable in these sections)
pending = [
 dict(id='P-DLO', code='DLO', std='SAE J1100', name_cn='采光口（Daylight Opening）', name_en='Daylight Opening', dts_key='pkg.dlo.side', status='side-view-only',
      definition='J1100 2009 版使用 DLO 术语（你的描述里写作 DGO）；需在侧视图/风挡视图中度量，不能由单个截面得到。', drives=['GLASS-SIDE', 'GLASS-WINDSHIELD', 'SEAL-GLASSRUN'], envelope='玻璃采光口决定门框、A/B 柱与密封条的外轮廓。'),
 dict(id='P-W27', code='W27/W35/H35', std='SAE J1100', name_cn='头部间隙(X平面截面)', name_en='Head clearances (X-plane section)', dts_key='pkg.head.clearance_xplane', status='needs-hpm',
      definition='J1100 2009 版修订了定义头部间隙的 X 平面截面（侧视顶部轮廓）；需 HPM/头部轮廓数据。', drives=['BIW-ROOF-INNER', 'TRIM-HEADLINER', 'BIW-RAIL'], envelope='顶盖边梁与顶棚的横向头部包络。')]
json.dump(dict(disclaimer='示意数据：几何与数值为演示用途，不是任何真实车型。J1100 条目定义均需对照标准原文核对。DTS 目标值留空，请填入贵司 DTS。',
               sections=secs, pending=pending), open(os.path.join(OUT, 'semantics.json'), 'w'), ensure_ascii=False, indent=1)
print('ok', [s['file'] for s in secs])
