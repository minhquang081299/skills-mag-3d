// Dán vào javascript_tool khi trang đang mở (viewport 1440x900).
// Cuộn từng nấc 150px từ đầu xuống cuối rồi ngược lên; mỗi nấc so thẻ chữ đang ở giữa màn hình
// với nhãn công trình đang được tô nổi (.tag.focus). Kết quả đúng: mismatches = 0.
// Sửa LABELS cho khớp nhãn của trang (text của marker → mã nhóm).
const LABELS = { 'HH1–HH4 LINH ĐÀM': 'hh', 'VP3 · VP5 · VP6': 'vp', 'CT11 · CT12 KIM VĂN': 'kv', 'CT6 KIẾN HƯNG': 'kh', 'ĐẠI THANH': 'dt' };
const sleep = ms => new Promise(r => setTimeout(r, ms));
const steps = [...document.querySelectorAll('.step')];
const check = () => {
  const a = innerHeight / 2;
  const cur = steps.find(s => { const r = s.querySelector('.card').getBoundingClientRect(); return r.top <= a && r.bottom >= a; });
  if (!cur) return null;
  const t = document.querySelector('.tag.focus');
  return { exp: cur.dataset.focus, act: t ? LABELS[t.textContent.trim()] : 'all', y: scrollY };
};
const H = document.documentElement.scrollHeight - innerHeight;
const bad = []; let n = 0;
for (let y = 0; y <= H; y += 150) { scrollTo(0, y); await sleep(70); const c = check(); if (c) { n++; if (c.exp !== c.act) bad.push(['down', c]); } }
for (let y = H; y >= 0; y -= 150) { scrollTo(0, y); await sleep(70); const c = check(); if (c) { n++; if (c.exp !== c.act) bad.push(['up', c]); } }
JSON.stringify({ checked: n, mismatches: bad.length, sample: bad.slice(0, 6) });
