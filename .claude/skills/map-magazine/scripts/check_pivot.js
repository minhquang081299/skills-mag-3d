// Dán vào javascript_tool khi đang đứng ở một đoạn có data-focus (không phải "all").
// Đèn rọi (#spot) bám theo vị trí màn hình của tâm xoay (pivot). Nếu xoay đúng quanh công trình,
// --sx/--sy phải giữ nguyên qua 8 lần xoay 45° (đủ 360°) và khi bật chế độ xoay 360° tự động.
const sleep = ms => new Promise(r => setTimeout(r, ms));
const sp = document.getElementById('spot');
const rd = () => Math.round(parseFloat(sp.style.getPropertyValue('--sx'))) + ',' + Math.round(parseFloat(sp.style.getPropertyValue('--sy')));
const out = [rd()];
for (let i = 0; i < 8; i++) { document.getElementById('rr').click(); await sleep(700); out.push(rd()); }
document.getElementById('orbit').click(); await sleep(2500); out.push('orbit ' + rd()); await sleep(2000); out.push('orbit ' + rd());
document.getElementById('orbit').click();
JSON.stringify({ positions: out, stable: new Set(out.map(s => s.replace('orbit ', ''))).size === 1 });
