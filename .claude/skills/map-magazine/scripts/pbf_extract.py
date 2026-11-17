"""Trích đường, sông, hồ (và tùy chọn nhà) trong một bbox từ file .osm.pbf của Geofabrik.
Dùng khi máy chủ Overpass quá tải. Cần: pip install --user osmium

    python -I pbf_extract.py vietnam.osm.pbf out.json S,W,N,E [--highways motorway,trunk,primary,secondary,construction] [--buildings]

Đầu ra có cùng dạng với Overpass `out geom tags` ({"elements":[{type,id,tags,geometry:[{lat,lon}]}]}),
nên dùng thẳng được với build_data.py và các script khác của skill.
"""
import json, sys
import osmium

pbf, out, bbox = sys.argv[1], sys.argv[2], [float(x) for x in sys.argv[3].split(',')]
S, W, N, E = bbox
hw = None
want_bld = '--buildings' in sys.argv
if '--highways' in sys.argv:
    hw = set(sys.argv[sys.argv.index('--highways') + 1].split(','))

els = []
fp = osmium.FileProcessor(pbf).with_locations().with_filter(osmium.filter.EntityFilter(osmium.osm.WAY))
for w in fp:
    t = dict(w.tags)
    keep = False
    if 'highway' in t:
        h = t['highway']
        base = h.replace('_link', '')
        keep = hw is None or base in hw or h in hw
    elif t.get('waterway') in ('river', 'canal') or t.get('natural') == 'water':
        keep = True
    elif want_bld and 'building' in t:
        keep = True
    if not keep:
        continue
    try:
        g = [{'lat': round(n.lat, 6), 'lon': round(n.lon, 6)} for n in w.nodes]
    except osmium.InvalidLocationError:
        continue
    if not g or not any(S <= p['lat'] <= N and W <= p['lon'] <= E for p in g):
        continue
    els.append({'type': 'way', 'id': w.id, 'tags': t, 'geometry': g})

json.dump({'elements': els}, open(out, 'w', encoding='utf-8'), ensure_ascii=False)
print(len(els), 'ways ->', out)
