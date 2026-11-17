---
name: map-magazine
description: Tạo bài magazine cuộn (scrollytelling) trên bản đồ 3D từ một bài báo về các công trình, tòa nhà, dự án có địa điểm cụ thể. Mỗi đoạn văn bay camera tới đúng tòa nhà, mổ xẻ khối nhà theo tầng và từng căn hộ (trong / vượt quy hoạch), cho người đọc kéo, zoom, xoay 360°, bấm vào căn xem chi tiết, rồi xuất bản thành Artifact. Dùng khi người dùng đưa link bài báo và muốn "magazine", "bài long-form", "scrollytelling", "bản đồ 3D", "focus từng tòa nhà", hoặc dựng lại sai phạm xây dựng, dự án bất động sản, quy hoạch trên bản đồ.
---

# Map magazine 3D từ bài báo

Quy trình đã chạy thực tế cho bài "12 công trình vi phạm liên quan đến Mường Thanh" (Hà Nội, 11/2026).
Bản hoàn chỉnh nằm ở `references/example-muong-thanh.html`. Đọc nó trước khi viết trang mới:
đa số trang mới chỉ cần thay dữ liệu và nội dung, không phải viết lại engine.

Kết quả cuối: một Artifact gồm `index.html` + `city-vN.json` (dữ liệu bản đồ) + ảnh gốc của bài.

## Nguyên tắc nội dung (đọc trước tiên)

- **Viết lại bằng lời mình**, không chép nguyên văn bài báo. Chỉ dùng ảnh của bài gốc người dùng đưa, có ghi tác giả ảnh. Không lấy ảnh của các báo tham khảo thêm, chỉ lấy số liệu.
- **Mỗi con số có nguồn**: link báo ở cuối từng thẻ (`<p class="meta">Nguồn: …</p>`) và tổng hợp ở đoạn kết.
- **Công trình không có số liệu riêng thì bỏ đoạn riêng**, chỉ để trên bản đồ tổng quan, tô màu xám ("chưa có số liệu"), và nói một câu ở đoạn chương.
- **Có số liệu thì đi sâu tới tầng và căn**: tầng được phép và tầng thực tế, số căn duyệt và số căn thực tế, tầng nào sai công năng, bao nhiêu căn di dời.
- **Ước tính phải ghi là ước tính**: số căn mỗi tầng chia đều từ tổng, vị trí căn là sơ đồ minh họa, chiều cao tính từ số tầng.
- **Mâu thuẫn giữa các báo**: chọn một nguồn, ghi rõ nguồn khác nói gì.

## Quy trình

### 1. Đọc bài gốc
- Tải HTML bằng `curl -sL -A "Mozilla/5.0" <url>` vào scratchpad. WebFetch thường từ chối trả nguyên văn.
- Trích đoạn văn bằng Python. Trên Windows luôn mở file và in với `encoding='utf-8'`, nếu không sẽ lỗi `cp1252`. Ghi ra file `body.txt` rồi đọc.
- Lấy: tiêu đề, sapo, ngày, danh sách công trình và địa chỉ (phường, xã), mốc thời gian, ảnh (`data-original` của `<img>`; ảnh CDN thường là WebP dù đuôi `.jpg`, tải kèm header `-e <referer>`).

### 2. Tìm thêm nguồn cho từng công trình
- Chạy song song WebSearch `mode: "extended"` cho từng nhóm công trình: số tầng duyệt/thực tế, số căn duyệt/thực tế, kết luận thanh tra, số căn di dời.
- Một lượt tìm "còn dự án nào khác không" (cùng chủ đầu tư, cùng nghị quyết).
- WebFetch các bài tổng hợp (Znews, CafeF, Dân trí, Tiền Phong, VnExpress…) với prompt yêu cầu "giữ nguyên con số" và đặt dưới dạng bảng.
- Lập bảng số liệu theo từng tòa trước khi viết trang. Chỉ đưa vào trang những gì đọc được trực tiếp; không dựa vào phần tóm tắt của kết quả search mà chưa mở bài.

### 3. Xác định tòa nhà trên OpenStreetMap
- Không dùng Nominatim cho tên tòa nhà ở Việt Nam (thường không ra). Dùng Overpass tìm `way["building"]["name"]` trong bbox khu vực; script `scripts/osm_fetch.sh` có sẵn truy vấn và tự thử nhiều máy chủ (overpass-api.de hay quá tải, có lúc lỗi 429/502).
- Ghi lại OSM way id của từng khối tháp (ví dụ HH1A, HH1B…). Tên OSM có thể khác tên trong báo (CT6 Kiến Hưng nằm trên OSM với tên "CT6A Xa La"): đối chiếu số khối, số tầng, và chi tiết đặc trưng trong bài (dãy nhà liền kề, sông bên cạnh…).
- Nhà liền kề, khối đế thuộc dự án: lấy theo vị trí (các way building sát cụm tháp).
- Nhiều tòa thiếu `building:levels`: tự đặt chiều cao theo số liệu báo hoặc theo tòa cùng cụm, rồi ghi chú trên trang.

### 4. Dựng dữ liệu bản đồ
- Artifact chặn mọi tile server (CSP), nên **không dùng nền bản đồ online**. Tải đường, hồ, công viên, nhà quanh khu vực bằng Overpass (`scripts/osm_fetch.sh city …`) rồi chạy `scripts/build_data.py` để ra một file GeoJSON gộp (~1,5 MB cho 4×5 km).
- `build_data.py` nhận file nhóm `groups.json` (`{"mã nhóm": [osm way id…]}`) và `overrides.json` (chiều cao bổ sung, tùy chọn).
- **Đặt tên file dữ liệu có số phiên bản** (`city-v2.json`) và đổi số mỗi khi dữ liệu đổi. Trình duyệt người xem giữ cache file cũ rất lâu; đổi tên là cách chắc chắn nhất. Fetch với `{ cache: 'no-cache' }`.

### 5. Viết trang (sửa từ bản mẫu)
Engine trong bản mẫu gồm các khối; khi làm bài mới chỉ sửa phần dữ liệu và nội dung:

| Phần | Sửa gì |
|---|---|
| `LABELS`, `ORDER`, `CAM` | Mã nhóm, tên nhãn, thứ tự đoạn (chỉ nhóm có đoạn riêng), zoom và hướng mặc định |
| `segments()` | Cách cắt từng tòa thành tầng: số tầng thực tế, tầng được phép (`o=1` là vượt), tầng sai công năng (`k:'pod'`), tầng áp mái (`k:'pent'`), tòa ngoài quy hoạch (`gr:'whole'` để ẩn/mọc lên ở bước "quy hoạch vs thực tế") |
| `unitCount()` | Số căn mỗi tầng cho những tòa có tổng số căn công bố (chia đều bằng `spread`) |
| `unitStatus()`, `UNIT_COL`, `describe()` | Trạng thái từng căn và nội dung bảng thông tin khi bấm |
| `<section class="step" data-…>` | Nội dung từng đoạn và cảnh camera |

Thuộc tính của một đoạn:
- `data-focus="hh"` hoặc `"all"`; với `all` dùng `data-view` (`overview`, `overview2`, `linhdam`, `west`, `orbit`, `orbit2`, `all`; thêm view mới trong `cam()`).
- `data-style="permit"` (xanh trong phép / cam vượt / đỏ thẫm sai công năng), `"plan"` (chỉ dựng phần có trong bản vẽ), `"hl"` + `data-hl="Tên OSM"` hoặc `data-kinds="pod,pent"` (tô riêng một tòa hoặc loại tầng).
- `data-grow="0|1"` (ẩn/mọc phần xây thêm, có animation), `data-legend="1"`, `data-zoom`, `data-bear`, `data-pitch`.
- Zoom ≥ 17.1 (điện thoại ≥ 16.6) thì tự hiện từng căn hộ và ô cửa sổ; đặt `data-zoom` của đoạn "từng căn" khoảng 17.3–17.8.

Cấu trúc bài nên theo: hero → quy mô sai phạm (con số tổng) → các phần theo khu vực (đoạn chương + từng công trình) → giải phẫu sâu công trình nhiều số liệu nhất (quy hoạch → thực tế → từng hạng mục → từng căn → pháp lý) → cơ chế xử lý → quyền lợi người dân → lộ trình → trách nhiệm tài chính → kết + nguồn.

### 6. Những lỗi đã gặp và cách tránh (đều đã có trong bản mẫu)
- **Cuộn ngược lệch nội dung**: đừng dùng IntersectionObserver trên cả khối section. Chọn đoạn theo thẻ chữ đang cắt đường mốc giữa màn hình (`pickStep()` chạy trên `scroll` + rAF).
- **Xoay bị lệch tâm**: đừng dùng `offset` để né thẻ chữ. Đặt `center` đúng vào công trình và dùng `padding` (lề trái trên desktop, lề dưới trên điện thoại). Khi bấm vào một tòa, đặt `pivot` = tâm tòa đó rồi `easeTo({center: pivot, padding})`. Nút xoay, xoay 360° đều quay quanh `pivot`.
- **Một mặt tòa nhà tối đen**: dùng `light.anchor: 'viewport'` để ánh sáng đi theo camera.
- **Tòa nhà phẳng**: OSM thiếu số tầng; xem bước 3.
- **Bị cache dữ liệu cũ trên link Claude**: xem bước 4.
- **`[hidden]` không ẩn khi chạy localhost**: skeleton của Artifact có `[hidden]{display:none!important}` nhưng file local thì không; thêm `.info[hidden]{display:none}`.
- **Tiếng Việt lỗi font khi xem local**: thêm `<meta charset="utf-8">` đầu file.
- **Không có chữ trên bản đồ**: không có glyph server, nên nhãn dùng HTML marker (`maplibregl.Marker`), không dùng symbol layer.
- `maxBounds` làm camera tự kéo sát vào tòa nhà khi pitch cao: không dùng.

### 7. Kiểm tra trước khi xuất bản
Chạy server tĩnh (`.claude/launch.json` với `python -m http.server 8765 -d <thư mục>`), mở bằng `preview_start`, đặt viewport 1440×900 rồi:
1. **Cuộn hai chiều**: dán `scripts/check_scroll.js` vào `javascript_tool`. Kết quả phải là `mismatches: 0`.
2. **Tâm xoay**: dán `scripts/check_pivot.js` (đứng ở một đoạn có focus). Vị trí `--sx/--sy` của đèn rọi phải đứng yên qua 8 lần xoay 45° và chế độ 360°.
3. **Chụp màn hình** các đoạn chính (zoom vào vùng tòa nhà để xem từng căn, cửa sổ), bấm thử một căn xem bảng thông tin.
4. `read_console_messages` với `onlyErrors: true` phải rỗng.

### 8. Xuất bản
- `Artifact` publish `index.html` với `files: {"city-vN.json": …, "<ảnh>.webp": …}`, `icon: "map"`, description một câu. Lần sau chỉ publish lại cùng `file_path`; khi đổi file dữ liệu thì truyền tên mới và `null` cho tên cũ.
- Mở link Claude một lần để chắc chắn trang và dữ liệu tải được (trang nằm trong iframe, cuộn bằng con lăn trên vùng trang).

## Biến thể: bài về tuyến đường, hạ tầng dạng tuyến
Đã làm cho bài "Bảy vòng vành đai Hà Nội" (`E:\Personal\MagGen\vanh-dai`). Khác bài tòa nhà ở chỗ:
- **Tìm tuyến trong OSM**: tuyến mới thường có tên riêng ("Đường Vành đai 1", "Đường cao tốc vành đai 4…", thẻ `wikipedia`), tuyến cũ mang tên phố (Trường Chinh, Phạm Văn Đồng…). Khớp bằng danh sách tên + bbox + loại đường trong `rules.json`; cẩn thận chuỗi con ("Vành đai 2" khớp nhầm "Vành đai 2.5": dùng `exclude_names`). Đoạn trống giữa tuyến thường là đường cũ được mở rộng (La Thành) hoặc đoạn đang thi công chưa tên: thêm theo `ids`.
- **`scripts/build_rings.py extract.json rules.json out.json`** dựng: dải 3D cho tuyến (đoạn `bridge`/`layer≥1` nâng lên 11–13,5 m), đường tâm để làm nhãn và camera, hành lang giải phóng mặt bằng (dải rộng bằng mặt cắt), nền đường/sông/hồ đã lọc gọn (~6 MB cho cả vùng Hà Nội).
- **Nhấn mạnh đền bù**: khối hộ dân dựng trong trang (hàm `houses()` của `vanh-dai/index.html`) xếp dọc hành lang, số khối = số hộ công bố (hoặc 1 khối = 10 hộ khi quá nhiều), bấm để xem; kèm biểu đồ HTML "tỷ trọng GPMB" và "tiền GPMB mỗi km" (đã chạy validator dataviz cho cặp màu #e8532f/#4f93c4 trên nền #171d21), có tooltip và bảng số liệu.
- **Nhãn tên phố, phường/xã, điểm mốc**: `scripts/pbf_places.py` trích địa danh (place=*, và tên nút giao/cầu cần tìm) từ file pbf; `scripts/add_labels.py extract.json places.json labels.json data.json` thêm lớp `labels` (tên phố dọc vòng đang xem, phường/xã trong bán kính quanh hành lang, điểm mốc khai báo tay theo bài, đô thị cho góc nhìn rộng). Lọc tên nhánh rẽ ("Đi …", "Hướng đi…"), tên làng cổ ("Kẻ …"). Trong trang, nhãn là HTML marker `pointer-events:none`, bật/tắt theo đoạn trong `labelsFor()`.
- **Tuyến chưa xây (không có trong OSM)**: không tự vẽ hướng tuyến; chỉ trình bày bằng số liệu.

## Khi Overpass quá tải
Overpass hay lỗi 502/429 nhiều giờ liền. Dự phòng chắc chắn: hỏi người dùng rồi tải bản trích Geofabrik (`https://download.geofabrik.de/asia/vietnam-latest.osm.pbf`, ~330 MB) vào thư mục riêng, `pip install --user osmium`, rồi chạy `python -P scripts/pbf_extract.py <pbf> extract.json S,W,N,E --highways motorway,trunk,primary,secondary,tertiary,construction [--buildings]` (dùng `-P`, không dùng `-I`, vì `-I` chặn thư viện cài ở thư mục người dùng). Mất khoảng 1 phút cho cả Việt Nam; đầu ra cùng định dạng Overpass.

## Tệp trong skill
- `references/example-muong-thanh.html`: bản hoàn chỉnh (engine + nội dung mẫu).
- `scripts/osm_fetch.sh`: tìm tòa nhà theo tên, tải geometry theo id, tải dữ liệu nền khu vực, có thử nhiều máy chủ Overpass.
- `scripts/build_data.py`: gộp dữ liệu OSM thành file GeoJSON cho trang (bài tòa nhà).
- `scripts/build_rings.py`: dựng dữ liệu cho bài tuyến đường (dải 3D, hành lang GPMB, nền gọn).
- `scripts/pbf_extract.py`: trích dữ liệu từ file .osm.pbf khi Overpass quá tải.
- `scripts/pbf_places.py`, `scripts/add_labels.py`: địa danh và lớp nhãn cho bản đồ.
- `scripts/check_scroll.js`, `scripts/check_pivot.js`: kiểm tra tự động trong trình duyệt.
