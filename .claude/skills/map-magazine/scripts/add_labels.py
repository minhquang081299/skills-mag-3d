"""Thêm lớp nhãn (tên phố dọc tuyến, phường/xã quanh hành lang, điểm mốc, đô thị) vào file dữ liệu bài tuyến đường.

    python -I add_labels.py extract.json places.json labels.json data.json

labels.json:
{
  "landmarks": [{"name": "Nút Hoàng Cầu", "r": "1", "lat": 21.021, "lon": 105.8253}, ...],
  "towns": ["Thường Tín", "Văn Giang", ...],        # đô thị hiện ở các góc nhìn toàn cảnh
  "street_min_m": 700,                              # khoảng cách tối thiểu giữa hai nhãn phố cùng vòng
  "area_radius_m": 1300,                            # phường/xã trong bán kính này quanh hành lang
  "skip_streets": ["Đường cao tốc vành đai 4 vùng thủ đô Hà Nội"]
}
Ghi thêm vào data.json: labels = FeatureCollection điểm, properties {t: street|area|lm|town, n, r, corr}.
"""
import json, math, sys

ex_p, pl_p, lb_p, data_p = sys.argv[1:5]
cfg = json.load(open(lb_p, encoding='utf-8'))
D = json.load(open(data_p, encoding='utf-8'))
places = json.load(open(pl_p, encoding='utf-8'))['places']
KX, KY = 104000, 111000


def dist(a, b):
    return math.hypot((a[0] - b[0]) * KX, (a[1] - b[1]) * KY)


def seglen(c):
    return sum(dist(c[i], c[i + 1]) for i in range(len(c) - 1))


def midpoint(c):
    L = seglen(c) / 2
    for i in range(len(c) - 1):
        d = dist(c[i], c[i + 1])
        if L <= d and d:
            t = L / d
            return [c[i][0] + (c[i + 1][0] - c[i][0]) * t, c[i][1] + (c[i + 1][1] - c[i][1]) * t]
        L -= d
    return c[len(c) // 2]


out = []
# 1) tên phố: đoạn dài nhất của mỗi tên trong mỗi vòng, rồi bỏ nhãn quá gần nhau
skip = set(cfg.get('skip_streets', []))
best = {}
for f in D['ringlines']['features']:
    p = f['properties']
    nm = p.get('nm', '')
    if not nm or nm in skip or any(nm.lower().replace('đường ', '').startswith(x.lower()) for x in cfg.get('skip_street_prefix', []))             or any(x.lower() in nm.lower() for x in cfg.get('skip_street_contains', [])):
        continue
    L = seglen(f['geometry']['coordinates'])
    key = (p['r'], nm)
    if key not in best or L > best[key][0]:
        best[key] = (L, midpoint(f['geometry']['coordinates']))
minm = cfg.get('street_min_m', 700)
placed = {}
for (r, nm), (L, pt) in sorted(best.items(), key=lambda x: -x[1][0]):
    if L < 120:
        continue
    if any(dist(pt, q) < minm for q in placed.get(r, [])):
        continue
    placed.setdefault(r, []).append(pt)
    short = nm.replace('Đường ', '').replace('Phố ', '')
    out.append({'type': 'Feature', 'properties': {'t': 'street', 'n': short, 'r': r}, 'geometry': {'type': 'Point', 'coordinates': [round(pt[0], 6), round(pt[1], 6)]}})

# 2) phường/xã quanh từng hành lang
rad = cfg.get('area_radius_m', 1300)
cl = {}
for f in D['corrlines']['features']:
    cl.setdefault(f['properties']['id'], []).extend(f['geometry']['coordinates'])
for cid, pts in cl.items():
    pts = pts[::max(1, len(pts) // 300)]
    seen = set()
    for pl in places:
        if pl['kind'] not in ('suburb', 'quarter', 'town', 'village') or pl['name'] in seen:
            continue
        if pl['name'][:1].isdigit() or '(' in pl['name'] or any(pl['name'].startswith(x) for x in cfg.get('skip_area_prefix', [])):
            continue
        p = [pl['lon'], pl['lat']]
        if min(dist(p, q) for q in pts) <= rad:
            seen.add(pl['name'])
            out.append({'type': 'Feature', 'properties': {'t': 'area', 'n': pl['name'], 'corr': cid}, 'geometry': {'type': 'Point', 'coordinates': p}})

# 3) điểm mốc
for lm in cfg.get('landmarks', []):
    out.append({'type': 'Feature', 'properties': {'t': 'lm', 'n': lm['name'], 'r': lm['r']}, 'geometry': {'type': 'Point', 'coordinates': [lm['lon'], lm['lat']]}})

# 4) đô thị cho góc nhìn toàn cảnh
want = cfg.get('towns', [])
got = set()
for pl in places:
    if pl['name'] in want and pl['name'] not in got and pl['kind'] in ('city', 'town', 'suburb'):
        got.add(pl['name'])
        out.append({'type': 'Feature', 'properties': {'t': 'town', 'n': pl['name']}, 'geometry': {'type': 'Point', 'coordinates': [pl['lon'], pl['lat']]}})

D['labels'] = {'type': 'FeatureCollection', 'features': out}
json.dump(D, open(data_p, 'w', encoding='utf-8'), separators=(',', ':'), ensure_ascii=False)
from collections import Counter
print('labels', Counter(f['properties']['t'] for f in out), 'missing towns:', sorted(set(want) - got))
