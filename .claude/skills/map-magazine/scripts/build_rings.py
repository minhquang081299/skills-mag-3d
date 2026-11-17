"""Dựng rings-v1.json cho trang vành đai từ dữ liệu OSM đã trích (định dạng Overpass).

    python -I build_rings.py extract.json rules.json out.json

rules.json:
{
  "rings": [ {"r": "2", "st": "done", "w": 34, "names": ["Trường Chinh", ...], "bbox": [S,W,N,E], "ids": [..], "construction": false}, ... ],
  "corridors": [ {"id": "c1", "names": [...], "bbox": [...], "ids": [...], "w": 50}, ... ]
}
Mỗi way khớp tên (hoặc id) và nằm trong bbox được gán cho vòng tương ứng.
"""
import json, math, sys

src, rules_p, out_p = sys.argv[1:4]
d = json.load(open(src, encoding='utf-8'))
rules = json.load(open(rules_p, encoding='utf-8'))


def inside(g, bb):
    S, W, N, E = bb
    return sum(S <= p['lat'] <= N and W <= p['lon'] <= E for p in g) >= max(1, len(g) // 2)


def match(e, rule):
    t = e.get('tags', {})
    if e['id'] in set(rule.get('ids', [])):
        return True
    if e['id'] in set(rule.get('exclude', [])):
        return False
    hw = t.get('highway', '')
    if not hw or hw in ('footway', 'cycleway', 'path', 'steps', 'service', 'track', 'pedestrian'):
        return False
    if rule.get('hw') and hw.replace('_link', '') not in rule['hw'] and not (hw == 'construction' and t.get('construction', '') in rule['hw']):
        return False
    nm = t.get('name', '') + '|' + t.get('ref', '') + '|' + t.get('alt_name', '') + '|' + t.get('official_name', '')
    if rule.get('names') and not any(n.lower() in nm.lower() for n in rule['names']):
        return False
    if any(x.lower() in nm.lower() for x in rule.get('exclude_names', [])):
        return False
    if rule.get('bbox') and not inside(e['geometry'], rule['bbox']):
        return False
    return bool(rule.get('names') or rule.get('ids'))


def offset_poly(coords, w):
    """Dải rộng w (m) quanh polyline [[lon,lat],...]."""
    lat0 = coords[0][1]
    kx, ky = math.cos(math.radians(lat0)) * 111320, 110540
    P = [(c[0] * kx, c[1] * ky) for c in coords]
    left, right = [], []
    for i, (x, y) in enumerate(P):
        nx = ny = 0.0
        for a, b in ((i - 1, i), (i, i + 1)):
            if 0 <= a and b < len(P):
                dx, dy = P[b][0] - P[a][0], P[b][1] - P[a][1]
                L = math.hypot(dx, dy) or 1
                nx += -dy / L; ny += dx / L
        L = math.hypot(nx, ny) or 1
        nx, ny = nx / L * w / 2, ny / L * w / 2
        left.append((x + nx, y + ny)); right.append((x - nx, y - ny))
    ring = left + right[::-1] + [left[0]]
    return [[round(x / kx, 6), round(y / ky, 6)] for x, y in ring]


def line(g):
    return [[round(p['lon'], 6), round(p['lat'], 6)] for p in g]


def elevated(t):
    try:
        layer = int(t.get('layer', '0'))
    except ValueError:
        layer = 0
    return t.get('bridge') in ('yes', 'viaduct') and layer >= 1 or t.get('bridge') == 'viaduct' or layer >= 2


ribbons, ringlines, corridors, corrlines, roads, rivers, water = [], [], [], [], [], [], []
used = set()
for rule in rules['rings']:
    n = 0
    for e in d['elements']:
        if e['id'] in used or 'geometry' not in e or len(e['geometry']) < 2:
            continue
        if not match(e, rule):
            continue
        used.add(e['id']); n += 1
        t = e['tags']
        el = 1 if elevated(t) else 0
        st = 'build' if t.get('highway') == 'construction' or rule.get('st') == 'build' and not rule.get('mixed') else rule.get('st', 'done')
        if rule.get('mixed'):
            st = 'build' if t.get('highway') == 'construction' else 'plan' if t.get('highway') == 'proposed' else 'done'
        co = line(e['geometry'])
        ringlines.append({'type': 'Feature', 'properties': {'r': rule['r'], 'st': st, 'nm': t.get('name', '')}, 'geometry': {'type': 'LineString', 'coordinates': co}})
        ribbons.append({'type': 'Feature', 'properties': {'r': rule['r'], 'st': st, 'el': el, 'nm': t.get('name', ''),
                                                          'b': 11 if el else 0, 't': 13.5 if el else 1.4},
                        'geometry': {'type': 'Polygon', 'coordinates': [offset_poly(co, rule.get('w', 30) if not el else rule.get('we', 20))]}})
    print('ring', rule['r'], n, 'ways')

for rule in rules['corridors']:
    n = 0
    for e in d['elements']:
        if 'geometry' not in e or len(e['geometry']) < 2 or not match(e, rule):
            continue
        t = e['tags']
        if rule.get('ground_only') and elevated(t):
            continue
        n += 1
        co = line(e['geometry'])
        corrlines.append({'type': 'Feature', 'properties': {'id': rule['id']}, 'geometry': {'type': 'LineString', 'coordinates': co}})
        corridors.append({'type': 'Feature', 'properties': {'id': rule['id']}, 'geometry': {'type': 'Polygon', 'coordinates': [offset_poly(co, rule['w'])]}})
    print('corridor', rule['id'], n, 'ways')

for e in d['elements']:
    if e['id'] in used or 'geometry' not in e:
        continue
    t = e.get('tags', {})
    co = line(e['geometry'])
    if 'highway' in t:
        h = t['highway'].replace('_link', '')
        if h in ('motorway', 'trunk', 'primary'):
            roads.append({'type': 'Feature', 'properties': {'c': 'major'}, 'geometry': {'type': 'LineString', 'coordinates': co}})
        elif h in ('secondary', 'tertiary'):
            roads.append({'type': 'Feature', 'properties': {'c': 'minor'}, 'geometry': {'type': 'LineString', 'coordinates': co}})
    elif t.get('waterway') in ('river', 'canal'):
        rivers.append({'type': 'Feature', 'properties': {}, 'geometry': {'type': 'LineString', 'coordinates': co}})
    elif t.get('natural') == 'water' and len(co) > 3 and co[0] == co[-1]:
        water.append({'type': 'Feature', 'properties': {}, 'geometry': {'type': 'Polygon', 'coordinates': [co]}})

fc = lambda f: {'type': 'FeatureCollection', 'features': f}
json.dump({'ribbons': fc(ribbons), 'ringlines': fc(ringlines), 'corridors': fc(corridors), 'corrlines': fc(corrlines),
           'roads': fc(roads), 'rivers': fc(rivers), 'water': fc(water)},
          open(out_p, 'w', encoding='utf-8'), separators=(',', ':'), ensure_ascii=False)
print('roads', len(roads), 'rivers', len(rivers), 'water', len(water))

# ---- gọn nhẹ phần nền ----
import math as _m
D = json.load(open(out_p, encoding='utf-8'))
CORE = (20.93, 105.74, 21.10, 105.93)
def inb(c, b): return b[0] <= c[1] <= b[2] and b[1] <= c[0] <= b[3]
def r5(cs): return [[round(x, 5), round(y, 5)] for x, y in cs]
D['roads']['features'] = [dict(f, geometry={'type': 'LineString', 'coordinates': r5(f['geometry']['coordinates'])}) for f in D['roads']['features']
                          if f['properties']['c'] == 'major' or inb(f['geometry']['coordinates'][0], CORE)]
def span(cs):
    xs = [c[0] for c in cs]; ys = [c[1] for c in cs]
    return max((max(xs) - min(xs)) * 104000, (max(ys) - min(ys)) * 111000)
D['water']['features'] = [dict(f, geometry={'type': 'Polygon', 'coordinates': [r5(f['geometry']['coordinates'][0])]}) for f in D['water']['features'] if span(f['geometry']['coordinates'][0]) > 350]
D['rivers']['features'] = [dict(f, geometry={'type': 'LineString', 'coordinates': r5(f['geometry']['coordinates'])}) for f in D['rivers']['features'] if span(f['geometry']['coordinates']) > 400]
json.dump(D, open(out_p, 'w', encoding='utf-8'), separators=(',', ':'), ensure_ascii=False)
print('slim: roads', len(D['roads']['features']), 'water', len(D['water']['features']), 'rivers', len(D['rivers']['features']))
