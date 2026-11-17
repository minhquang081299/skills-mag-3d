"""Trích địa danh (điểm place=*, và các nút/đường có tên trong danh sách) trong bbox từ file .osm.pbf.

    python -P pbf_places.py vietnam.osm.pbf places.json S,W,N,E ["Ngã Tư Sở|Hoàng Cầu|Voi Phục"]

Đầu ra: {"places": [{"name", "kind", "lon", "lat"}]}
kind = city | town | suburb | quarter | village | neighbourhood | landmark (khớp danh sách tên).
Với đường có tên khớp danh sách, lấy điểm giữa của đường.
"""
import json, sys
import osmium

pbf, out, bbox = sys.argv[1], sys.argv[2], [float(x) for x in sys.argv[3].split(',')]
S, W, N, E = bbox
wanted = [x.strip().lower() for x in sys.argv[4].split('|')] if len(sys.argv) > 4 else []
PLACES = {'city', 'town', 'suburb', 'quarter', 'village', 'neighbourhood'}
res = []
inb = lambda lat, lon: S <= lat <= N and W <= lon <= E

fp = osmium.FileProcessor(pbf).with_locations()
for o in fp:
    t = o.tags
    name = t.get('name')
    if not name:
        continue
    if o.is_node():
        if not o.location.valid() or not inb(o.location.lat, o.location.lon):
            continue
        kind = t.get('place') if t.get('place') in PLACES else None
        if not kind and wanted and any(w == name.lower() or w in name.lower() for w in wanted):
            kind = 'landmark'
        if kind:
            res.append({'name': name, 'kind': kind, 'lon': round(o.location.lon, 6), 'lat': round(o.location.lat, 6)})
    elif o.is_way() and wanted and any(w == name.lower() for w in wanted):
        try:
            pts = [(n.lat, n.lon) for n in o.nodes]
        except osmium.InvalidLocationError:
            continue
        if not pts:
            continue
        lat, lon = pts[len(pts) // 2]
        if inb(lat, lon):
            res.append({'name': name, 'kind': 'landmark', 'lon': round(lon, 6), 'lat': round(lat, 6)})

json.dump({'places': res}, open(out, 'w', encoding='utf-8'), ensure_ascii=False)
from collections import Counter
print(len(res), 'places', Counter(p['kind'] for p in res))
