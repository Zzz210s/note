/* 0-Note 在线阅读站 · 浏览器实测(本地 file:// 打开生成物)。
 *
 * 用法:node measure_site.mjs <页面路径> [--shots <目录>]
 * 判据来自 spec V4~V7 与 §6.5/6.6:无横向滚动、触达 ≥44px、Ctrl-K 搜索、
 * 断网可用、明暗对比度 ≥4.5、断锚点为 0、零外部资源。
 */
import { createRequire } from 'module';
import fs from 'fs';
import path from 'path';

const require = createRequire(import.meta.url);
const puppeteer = require('C:/Users/23652/AppData/Roaming/npm/node_modules/puppeteer-core');
const EXE = 'C:/Users/23652/AppData/Local/ms-playwright/chromium_headless_shell-1228/chrome-headless-shell-win64/chrome-headless-shell.exe';

const file = process.argv[2];
const shotsArg = process.argv.indexOf('--shots');
const shots = shotsArg > 0 ? process.argv[shotsArg + 1] : '';
if (!file || !fs.existsSync(file)) { console.error('用法:node measure_site.mjs <页面路径> [--shots 目录]'); process.exit(2); }
if (shots) fs.mkdirSync(shots, { recursive: true });

const url = 'file:///' + path.resolve(file).split(path.sep).join('/');
let pass = 0, fail = 0;
const ok = (name, cond, detail = '') => { cond ? pass++ : fail++; console.log((cond ? 'PASS ' : 'FAIL ') + name + (cond ? '' : '  ' + detail)); };
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

const PROBE = `(() => {
  const out = { scrollW: document.documentElement.scrollWidth, innerW: window.innerWidth };
  const small = [];
  document.querySelectorAll('button, input, .chip, .icon-btn, .to-top, .link-btn, a.brand').forEach((el) => {
    const r = el.getBoundingClientRect();
    if (r.width === 0 && r.height === 0) return;
    const vis = getComputedStyle(el).visibility !== 'hidden' && getComputedStyle(el).display !== 'none';
    if (vis && (r.height < 44 && r.width < 44)) small.push((el.id || el.className || el.tagName) + ':' + Math.round(r.width) + 'x' + Math.round(r.height));
  });
  out.small = small.slice(0, 8);
  const ids = new Set(Array.from(document.querySelectorAll('[id]')).map((e) => e.id));
  out.deadAnchors = Array.from(document.querySelectorAll('a[href^="#"]')).map((a) => a.getAttribute('href').slice(1)).filter((h) => h && !ids.has(h)).slice(0, 5);
  out.cards = document.querySelectorAll('.card').length;
  out.external = document.querySelectorAll('script[src], link[rel=stylesheet]').length;
  const toRGB = (s) => {
    s = (s || '').trim();
    if (s.startsWith('#')) { const h = s.slice(1); const n = h.length === 3 ? h.split('').map((x) => x + x).join('') : h; return [0, 2, 4].map((i) => parseInt(n.slice(i, i + 2), 16)); }
    const m = s.match(/[0-9.]+/g) || ['0', '0', '0'];
    return m.slice(0, 3).map(Number);
  };
  const lum = (c) => { const f = (v) => { v /= 255; return v <= 0.04045 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4); };
    const [r, g, b] = toRGB(c); return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b); };
  const cs = getComputedStyle(document.documentElement);
  const L1 = lum(cs.getPropertyValue('--t1')), L2 = lum(cs.getPropertyValue('--bg'));
  out.contrast = Math.round(((Math.max(L1, L2) + 0.05) / (Math.min(L1, L2) + 0.05)) * 100) / 100;
  out.theme = document.documentElement.getAttribute('data-theme');
  return out;
})()`;

const browser = await puppeteer.launch({ executablePath: EXE, args: ['--no-sandbox', '--allow-file-access-from-files'] });
try {
  for (const vp of [{ name: 'desktop', width: 1200, height: 930 }, { name: 'mobile', width: 375, height: 812 }]) {
    const page = await browser.newPage();
    await page.setViewport({ width: vp.width, height: vp.height });
    await page.goto(url, { waitUntil: 'load', timeout: 120000 });
    const r = await page.evaluate(PROBE);
    ok(`${vp.name} 无横向滚动`, r.scrollW <= r.innerW + 1, `scrollW=${r.scrollW} innerW=${r.innerW}`);
    ok(`${vp.name} 触达 ≥44px`, r.small.length === 0, r.small.join(' | '));
    ok(`${vp.name} 断锚点为 0`, r.deadAnchors.length === 0, r.deadAnchors.join(' | '));
    ok(`${vp.name} 对比度 ≥4.5`, r.contrast >= 4.5, `contrast=${r.contrast}`);
    ok(`${vp.name} 零外部资源`, r.external === 0, `external=${r.external}`);
    if (vp.name === 'desktop') {
      const total = r.cards;
      await page.keyboard.down('Control'); await page.keyboard.press('KeyK'); await page.keyboard.up('Control');
      const focused = await page.evaluate(() => document.activeElement && document.activeElement.id);
      ok('Ctrl-K 聚焦搜索框', focused === 'q', `activeElement=${focused}`);
      await page.type('#q', 'tmux', { delay: 12 });
      await sleep(400);
      const hit = await page.evaluate(() => ({ visible: Array.from(document.querySelectorAll('.card')).filter((c) => !c.hidden).length, marks: document.querySelectorAll('mark').length }));
      ok('搜索命中并高亮', hit.visible > 0 && hit.marks > 0, JSON.stringify(hit));
      await page.keyboard.press('Escape');
      await sleep(300);
      const after = await page.evaluate(() => ({ visible: Array.from(document.querySelectorAll('.card')).filter((c) => !c.hidden).length, q: document.querySelector('#q').value }));
      ok('Esc 清空并复位', after.q === '' && after.visible === total, JSON.stringify(after) + ' total=' + total);
      await page.click('#theme');
      await sleep(250);
      const t = await page.evaluate(() => ({ theme: document.documentElement.getAttribute('data-theme'), stored: localStorage.getItem('note-theme') }));
      ok('主题切换并记忆', (t.theme === 'dark' || t.theme === 'light') && t.stored === t.theme, JSON.stringify(t));
      if (shots) { await page.screenshot({ path: path.join(shots, 'index-desktop.png') }); await page.screenshot({ path: path.join(shots, 'index-dark.png') }); }
      await page.click('#theme'); await sleep(200);
    } else if (shots) {
      await page.screenshot({ path: path.join(shots, 'index-mobile.png') });
    }
    await page.close();
  }

  /* 断网:只允许 file:// 请求,搜索仍要工作 */
  const off = await browser.newPage();
  await off.setRequestInterception(true);
  off.on('request', (req) => (req.url().startsWith('file:') ? req.continue() : req.abort()));
  await off.goto(url, { waitUntil: 'load', timeout: 120000 });
  await off.type('#q', 'tmux', { delay: 12 });
  await sleep(400);
  const offr = await off.evaluate(() => Array.from(document.querySelectorAll('.card')).filter((c) => !c.hidden).length);
  ok('断网仍可搜索', offr > 0, `visible=${offr}`);
  await off.close();
} finally {
  await browser.close();
}

const bytes = fs.statSync(path.resolve(file)).size;
console.log(`页面 ${path.basename(file)} · ${(bytes / 1048576).toFixed(2)} MB`);
console.log(`结论:${fail === 0 ? 'PASS' : 'FAIL'}(${pass} 通过 / ${fail} 失败)`);
process.exit(fail === 0 ? 0 : 1);
