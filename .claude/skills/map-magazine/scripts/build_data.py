"""Gộp dữ liệu OSM thành một file GeoJSON cho trang map magazine.

    python -I build_data.py city.json targets.json groups.json out/city-v1.json [overrides.json]

city.json     : kết quả `osm_fetch.sh city …` (đường, nước, công viên, nhà).
targets.json  : kết quả `osm_fetch.sh ids …` (các tòa sẽ tô sáng). Có thể trùng với city.json.
groups.json   : {"hh": [way id, ...], "vp": [...], ...}  mã nhóm = data-focus trong trang.
                Way nào nằm trong groups nhưng không có trong targets.json sẽ lấy từ city.json
                (tiện cho nhà liền kề, khối đế nhỏ không có tên).
overrides.json: {"<way id>": chiều cao mét}  cho tòa thiếu building:levels trên OSM (tùy chọn).

Đầu ra: {roads, water, parks, buildings, targets}; targets có properties g (nhóm), n (tên OSM), h (m).
"""
import json, re, sys

city_p, targets_p, groups_p, out_p = sys.argv[1:5]
over_p = sys.argv[5] if len(sys.argv) > 5 else None
city = json.load(open(city_p, encoding='utf-8'))
tg = json.load(open(targets_p, encoding='utf-8'))
groups = json.load(open(groups_p, encoding='utf-8'))
override = {int(k): float(v) for k, v in json.load(open(over_p, encoding='utf-8')).items()} if over_p else {}
id2g = {int(i): g for g, ids in groups.items() for i in ids}

ROADCLASS = {'motorway': 'major', 'trunk': 'major', 'primary': 'major', 'secondary': 'major', 'tertiary': 'mid',
             'residential': 'minor', 'unclassified': 'minor', 'living_street': 'minor', 'service': 'service'}


def ring(geom):
    return [[round(p['lon'], 6), round(p['lat'], 6)] for p in geom]


def height(t):
    try:
        if t.get('height'):
            v = float(re.sub('[^0-9.]', '', t['height']) or 0)
            if v: return v
        if t.get('building:levels'):
            return float(t['building:levels']) * 3.3
    except ValueError:
        pass
    return 9.0


roads, water, parks, blds = [], [], [], []
for e in city['elements']:
    t = e.get('tags', {})
    if e['type'] == 'way' and 'geometry' in e:
        if e['id'] in id2g:
            continue
        r = ring(e['geometry'])
        if 'highway' in t:
            roads.append({'type': 'Feature', 'properties': {'c': ROADCLASS.get(t['highway'].replace('_link', ''), 'minor')},
                          'geometry': {'type': 'LineString', 'coordinates': r}})
        elif t.get('natural') == 'water' and len(r) > 3:
            water.append({'type': 'Feature', 'properties': {}, 'geometry': {'type': 'Polygon', 'coordinates': [r]}})
        elif 'waterway' in t:
            roads.append({'type': 'Feature', 'properties': {'c': 'river'}, 'geometry': {'type': 'LineString', 'coordinates': r}})
        elif t.get('leisure') == 'park' and len(r) > 3:
            parks.append({'type': 'Feature', 'properties': {}, 'geometry': {'type': 'Polygon', 'coordinates': [r]}})
        elif 'building' in t and len(r) > 3:
            blds.append({'type': 'Feature', 'properties': {'h': round(height(t), 1)}, 'geometry': {'type': 'Polygon', 'coordinates': [r]}})
    elif e['type'] == 'relation' and t.get('natural') == 'water':
        for m in e.get('members', []):
            if m.get('role') == 'outer' and 'geometry' in m:
                r = ring(m['geometry'])
                if len(r) > 3 and r[0] == r[-1]:
                    water.append({'type': 'Feature', 'properties': {}, 'geometry': {'type': 'Polygon', 'coordinates': [r]}})

seen = {e['id'] for e in tg['elements']}
extra = [e for e in city['elements'] if e['type'] == 'way' and e['id'] in id2g and e['id'] not in seen and 'geometry' in e]
targets = []
for e in tg['elements'] + extra:
    if e['id'] not in id2g:
        continue
    t = e.get('tags', {})
    targets.append({'type': 'Feature',
                    'properties': {'g': id2g[e['id']], 'n': t.get('name', ''), 'h': round(override.get(e['id'], height(t)), 1)},
                    'geometry': {'type': 'Polygon', 'coordinates': [ring(e['geometry'])]}})

missing = sorted(set(id2g) - {f for f in seen} - {e['id'] for e in extra})
fc = lambda f: {'type': 'FeatureCollection', 'features': f}
json.dump({'roads': fc(roads), 'water': fc(water), 'parks': fc(parks), 'buildings': fc(blds), 'targets': fc(targets)},
          open(out_p, 'w', encoding='utf-8'), separators=(',', ':'), ensure_ascii=False)
print(f'roads {len(roads)}  water {len(water)}  parks {len(parks)}  buildings {len(blds)}  targets {len(targets)}')
if missing:
    print('KHÔNG TÌM THẤY way id:', missing)
flat = [f['properties']['n'] or '(không tên)' for f in targets if f['properties']['h'] <= 9.0 and f['properties']['n']]
if flat:
    print('Tòa có tên nhưng thiếu số tầng (đang 9 m, nên thêm vào overrides.json):', flat)
