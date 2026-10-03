/* 0-Note 在线阅读站 · 浏览器实测的探针与小工具(measure_site.mjs 用;拆出是为守住 ≤200 行)。
 * 三个探针是在页面里执行的源码字符串;reporter 只管计数与末行口径。 */
export const GENERIC = `(() => {
  const de = document.documentElement, b = document.body, sb = document.querySelector('.statusbar');
  const rgb = (s) => (String(s).match(/[0-9.]+/g) || ['0','0','0']).slice(0,3).map(Number);
  const f = (v) => { v /= 255; return v <= 0.04045 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4); };
  const lum = (c) => { const [r,g,bl] = rgb(c); return 0.2126*f(r) + 0.7152*f(g) + 0.0722*f(bl); };
  const ratio = (a, b2) => { const l1 = lum(a), l2 = lum(b2); return Math.round(((Math.max(l1,l2)+0.05)/(Math.min(l1,l2)+0.05))*100)/100; };
  const cb = getComputedStyle(b), csb = getComputedStyle(sb);
  return { scrollW: de.scrollWidth, innerW: window.innerWidth, theme: de.getAttribute('data-theme'),
    bg: cb.backgroundColor, fg: cb.color, contrast: ratio(cb.color, cb.backgroundColor),
    statusContrast: ratio(csb.color, csb.backgroundColor),
    external: document.querySelectorAll('script[src],link[rel=stylesheet]').length };
})()`;

export const TOUCH = `(() => {
  const small = [];
  document.querySelectorAll('button,input,.chip,.tree-item,.act,.tab,.t-close,a.skip').forEach((el) => {
    const r = el.getBoundingClientRect(); if (!r.width && !r.height) return;
    const cs = getComputedStyle(el); if (cs.visibility === 'hidden' || cs.display === 'none') return;
    if (r.height < 44 && r.width < 44) small.push((el.id || el.className || el.tagName) + ':' + Math.round(r.width) + 'x' + Math.round(r.height));
  });
  return small.slice(0, 8);
})()`;

export const FOCUS = `(() => {
  const a = document.activeElement, cs = getComputedStyle(a);
  const ring = (cs.outlineStyle !== 'none' && parseFloat(cs.outlineWidth) > 0) || cs.boxShadow !== 'none';
  return { cls: a.className || '', id: a.id || '', tag: a.tagName, ring: ring };
})()`;

/* 侧栏抽屉状态:data-open 与遮罩的实际显示(工作台固定用 .side-mask) */
export const SIDE = `(() => ({ open: document.querySelector('.sidebar').getAttribute('data-open'),
  mask: getComputedStyle(document.querySelector('.side-mask')).display }))()`;

export const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

/* 新开一页到干净状态:载入 -> 清 localStorage -> 重载 -> 等 JS 初始化(≥600ms,快会读中间态) */
export async function fresh(page, url) {
  await page.goto(url, { waitUntil: 'load', timeout: 120000 });
  await page.evaluate(() => { try { localStorage.clear(); } catch (e) {} });
  await page.reload({ waitUntil: 'load', timeout: 120000 });
  await sleep(650);
}

export const shot = async (page, dir, name) => { if (dir) await page.screenshot({ path: `${dir}/${name}` }); };
export const lum = (c) => { const m = (String(c).match(/[0-9.]+/g) || [0, 0, 0]).map(Number); return 0.2126 * m[0] + 0.7152 * m[1] + 0.0722 * m[2]; };
export const ctrl = async (page, key, shift) => {
  await page.keyboard.down('Control'); if (shift) await page.keyboard.down('Shift');
  await page.keyboard.press(key);
  if (shift) await page.keyboard.up('Shift'); await page.keyboard.up('Control');
};

export function reporter() {
  let pass = 0, fail = 0;
  const ok = (name, cond, detail = '') => {
    cond ? pass++ : fail++;
    console.log((cond ? 'PASS ' : 'FAIL ') + name + (detail ? '  ' + detail : ''));
  };
  return { ok, count: () => ({ pass, fail }) };
}
