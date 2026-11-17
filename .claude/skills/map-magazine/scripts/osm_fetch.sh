#!/usr/bin/env bash
# Tải dữ liệu OpenStreetMap qua Overpass, tự thử nhiều máy chủ (máy chủ chính hay quá tải).
#
#   osm_fetch.sh names <south,west,north,east> <out.json>
#       Liệt kê mọi tòa nhà có tên trong bbox (dùng để tìm OSM way id của từng khối tháp).
#   osm_fetch.sh ids <id1,id2,...> <out.json>
#       Tải geometry + tags của các way theo id (các tòa nhà sẽ tô sáng).
#   osm_fetch.sh city <south,west,north,east> <out.json>
#       Tải nền khu vực: đường, hồ, sông, công viên, mọi tòa nhà (để dựng bản đồ).
#
# Sau khi tải "names", in danh sách: python -I list_names.py out.json   (xem cuối file)
set -u
mode="$1"; arg="$2"; out="$3"

case "$mode" in
  names) q="[out:json][timeout:90];way[\"building\"][\"name\"]($arg);out center tags;" ;;
  ids)   q="[out:json][timeout:60];way(id:$arg);out geom tags;" ;;
  city)  q="[out:json][timeout:180];(way[\"highway\"~\"^(motorway|trunk|primary|secondary|tertiary|residential|unclassified|living_street|service)(_link)?\$\"]($arg);way[\"natural\"=\"water\"]($arg);relation[\"natural\"=\"water\"]($arg);way[\"waterway\"]($arg);way[\"leisure\"=\"park\"]($arg);way[\"building\"]($arg););out geom tags;" ;;
  *) echo "mode phải là names | ids | city"; exit 1 ;;
esac

for ep in https://overpass-api.de/api/interpreter \
          https://overpass.kumi.systems/api/interpreter \
          https://overpass.private.coffee/api/interpreter \
          https://maps.mail.ru/osm/tools/overpass/api/interpreter; do
  curl -s -m 220 -A "map-magazine/1.0" --data-urlencode "data=$q" "$ep" -o "$out"
  if head -c 40 "$out" | grep -q '{'; then
    echo "OK  $ep  $(wc -c < "$out") bytes"; exit 0
  fi
  echo "FAIL $ep: $(head -c 120 "$out" | tr '\n' ' ')"
done
echo "Tất cả máy chủ đều lỗi. Chờ vài phút rồi chạy lại (chạy nền nếu bbox lớn)."; exit 2

# --- list_names.py (in tòa nhà có tên, kèm số tầng và id) ---
# import json,sys,io
# sys.stdout=io.TextIOWrapper(sys.stdout.buffer,encoding='utf-8')
# for e in json.load(open(sys.argv[1],encoding='utf-8'))['elements']:
#     c=e.get('center',{}); t=e['tags']
#     print(round(c.get('lat',0),5), round(c.get('lon',0),5), t.get('name'), '|', t.get('building:levels',''), e['id'])
