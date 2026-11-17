# MagGen

Tạo bài magazine cuộn (scrollytelling) trên bản đồ 3D từ một bài báo về các công trình có địa điểm cụ thể.

## Nội dung

- `muong-thanh/`: bài mẫu "Hà Nội ấn định lộ trình xử lý 12 công trình vi phạm liên quan đến Mường Thanh".
  Mở `index.html` qua một server tĩnh (ví dụ `python -m http.server 8765 -d muong-thanh`), vì trang tải `city-v2.json` bằng fetch.
- `.claude/skills/map-magazine/`: skill Claude Code mô tả toàn bộ quy trình, kèm script tải dữ liệu OpenStreetMap,
  dựng file bản đồ, kiểm tra cuộn và tâm xoay, và bản mẫu tham chiếu.

## Nguồn

Nội dung tóm lược từ Báo Xây dựng, VnExpress, Znews, CafeF, Tiền Phong, Cafebiz, Dân trí, Afamily, Market Times
(liên kết trong trang). Ảnh HH Linh Đàm: TA / Báo Xây dựng. Bản đồ và vị trí tòa nhà: © OpenStreetMap contributors (ODbL).
