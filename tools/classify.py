"""Part title -> semantic layer group. Rules are ordered; first match wins.
Tuned for the CCSA/GMU 2012 Camry part names; edit for other models."""
import re
RULES = [
 ('GLASS-WINDSHIELD', r'windshield'),
 ('GLASS-BACKLITE',   r'windowrear'),
 ('GLASS-SIDE',       r'(door(front|rear|ear)window(r)?|windowsmall)$'),
 ('SEAT',             r'seat'),
 ('TRIM-DOOR',        r'door.*trim|doortrim'),
 ('TRIM-PILLAR',      r'pillar.*trim'),
 ('TRIM-IP',          r'^\d+_dash(?!tunnel)'),
 ('TRIM-HEADLINER',   r'headliner'),
 ('TRIM-CARPET',      r'carpet'),
 ('SEAL',             r'seal|weather|gasket'),
 ('DOOR-FRAME',       r'door.*(frame|window(track|rail|frame))'),
 ('DOOR-OUTER',       r'door.*outer'),
 ('DOOR-INNER',       r'door'),
 ('STRUCT-IPBEAM',    r'ipbeam|dashtunnel'),
 ('BIW-ROOF',         r'roof|header|bow'),
 ('BIW-PILLAR',       r'pillar'),
 ('BIW-SILL',         r'rocker|sill'),
 ('BIW-DASH',         r'firewall'),
 ('BIW-FLOOR',        r'floor|tunnel'),
 ('BIW-RAIL',         r'rail|xmember|member|wheelhous|wheelwell'),
 ('STEERING',         r'steering'),
 ('PEDAL',            r'brake|accel'),
]
_c = [(g, re.compile(p)) for g, p in RULES]
def classify(title):
    t = re.sub(r'(\.\d+)+$', '', title.strip().lower())
    for g, rx in _c:
        if rx.search(t): return g
    return 'OTHER'
