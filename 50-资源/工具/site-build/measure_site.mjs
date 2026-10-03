/* 0-Note 站 · 浏览器实测(工作台口径,file:// 开生成物)。用法:node measure_site.mjs <页面路径> [--shots 目录]
 * 判据来自 spec V4~V8:交互(点课出标签 / 快速打开 / 分屏 / 拖标签 / 侧栏 / 关标签 / 刷新恢复)、
 * 计数(烘焙 + 本地增量 + 清空)、主题(工作台变暗、内嵌课仍浅色)、375px、无障碍、对比度 ≥4.5、
 * 零外部资源、断网可用、三张截图。交互断言一律等 ≥600ms,避免读到中间态。探针见 measure_site_probe.mjs。
 */
import { createRequire } from 'module';
import fs from 'fs';
import path from 'path';
import { GENERIC, TOUCH, FOCUS, SIDE, sleep, fresh, shot, lum, ctrl, reporter } from './measure_site_probe.mjs';

const require = createRequire(import.meta.url);
const puppeteer = require('C:/Users/23652/AppData/Roaming/npm/node_modules/puppeteer-core');
const EXE = 'C:/Users/23652/AppData/Local/ms-playwright/chromium_headless_shell-1228/chrome-headless-shell-win64/chrome-headless-shell.exe';

const file = process.argv[2];
const shotsArg = process.argv.indexOf('--shots');
const shots = shotsArg > 0 ? process.argv[shotsArg + 1] : '';
if (!file || !fs.existsSync(file)) { console.error('用法:node measure_site.mjs <页面路径> [--shots 目录]'); process.exit(2); }
if (shots) fs.mkdirSync(shots, { recursive: true });
const url = 'file:///' + path.resolve(file).split(path.sep).join('/');
const VAULT = path.dirname(path.resolve(file));
const COURSE = '0001-CLI-TUI-GUI';   /* counts-seed.json 里 0001-CLI,TUI,GUI = 2 次 */
const { ok, count } = reporter();

const browser = await puppeteer.launch({ executablePath: EXE, args: ['--no-sandbox', '--allow-file-access-from-files'] });
try {
  /* ================= 桌面 1200×930 ================= */
  const page = await browser.newPage();
  await page.setViewport({ width: 1200, height: 930 });
  await fresh(page, url);

  const g = await page.evaluate(GENERIC);
  ok('桌面 无横向滚动', g.scrollW <= g.innerW + 1, `scrollW=${g.scrollW} innerW=${g.innerW}`);
  ok('桌面 对比度 >=4.5', g.contrast >= 4.5 && g.statusContrast >= 4.5, `正文=${g.contrast} 状态栏=${g.statusContrast}`);
  ok('桌面 零外部资源', g.external === 0, `external=${g.external}`);
  ok('V6 默认浅色', g.theme === 'light' && lum(g.bg) > 200, `theme=${g.theme} bg=${g.bg}`);

  /* V5 计数:烘焙初值 */
  const c0 = await page.evaluate((k) => ({ tree: document.querySelector('.tree-item[data-key="' + k + '"] .t-count').textContent,
    seed: window.__COUNTS__[k].count, get: window.__counts.get(k).count }), COURSE);
  ok('V5 侧栏次数 == 烘焙种子(0001=2)', c0.tree === '2' && c0.seed === 2 && c0.get === 2, JSON.stringify(c0));

  /* V4 点课程树项 -> 标签 + iframe 真路径 */
  await page.click(`.tree-item[data-key="${COURSE}"]`);
  await sleep(650);
  const r1 = await page.evaluate(() => ({ tabs: document.querySelectorAll('.tab').length,
    src: document.querySelector('.group[data-group="1"] iframe.lesson-frame').getAttribute('src') }));
  ok('V4 点课出 1 个标签', r1.tabs === 1, `tabs=${r1.tabs}`);
  let real = false;
  try { real = !!r1.src && fs.existsSync(path.join(VAULT, decodeURIComponent(r1.src))); } catch (e) { /* ignore */ }
  ok('V4 iframe src 指向真实课文件', real, r1.src ? decodeURIComponent(r1.src) : '(空)');

  const c1 = await page.evaluate((k) => ({ tree: document.querySelector('.tree-item[data-key="' + k + '"] .t-count').textContent,
    get: window.__counts.get(k).count }), COURSE);
  ok('V5 打开一次后 == 3', c1.tree === '3' && c1.get === 3, JSON.stringify(c1));

  /* V4 Ctrl+P 快速打开 -> 输入课号 -> Enter */
  await ctrl(page, 'p'); await sleep(300);
  const p1 = await page.evaluate(() => ({ hidden: document.getElementById('palette').hidden, focus: document.activeElement.id }));
  ok('V4 Ctrl+P 打开快速打开', p1.hidden === false && p1.focus === 'palette-q', JSON.stringify(p1));
  await page.type('#palette-q', '0002', { delay: 20 }); await sleep(300);
  const p2 = await page.evaluate(() => Array.from(document.querySelectorAll('#palette-list li .p-name')).map((n) => n.textContent));
  ok('V4 输入课号有结果', p2.length > 0, JSON.stringify(p2.slice(0, 3)));
  await page.keyboard.press('Enter'); await sleep(650);
  const p3 = await page.evaluate(() => ({ hidden: document.getElementById('palette').hidden, tabs: document.querySelectorAll('.tab').length }));
  ok('V4 Enter 打开标签', p3.hidden === true && p3.tabs === 2, JSON.stringify(p3));

  /* V4 Ctrl+\ 分屏 */
  await ctrl(page, 'Backslash'); await sleep(300);
  const s1 = await page.evaluate(() => { const gs = document.querySelector('.groups'), g2 = document.querySelector('.group[data-group="2"]');
    return { split: gs.getAttribute('data-split'), hidden: g2.hidden, disp: getComputedStyle(g2).display }; });
  ok('V4 Ctrl+\\ 出第二组', s1.split === 'true' && s1.hidden === false && s1.disp !== 'none', JSON.stringify(s1));

  /* V4 拖第一个标签到第二组(page.mouse 模拟原生拖拽;必须先开拖拽拦截,否则 drag() 等不到 dragIntercepted) */
  const before = await page.evaluate(() => document.querySelectorAll('.tab').length);
  const tb = await (await page.$('.group[data-group="1"] .tab')).boundingBox();
  const tgt = await (await page.$('.group[data-group="2"] .group-body[data-kind="welcome"]')).boundingBox();
  await page.setDragInterception(true);
  await page.mouse.dragAndDrop({ x: tb.x + tb.width / 2, y: tb.y + tb.height / 2 }, { x: tgt.x + tgt.width / 2, y: tgt.y + 40 });
  await page.setDragInterception(false);
  await sleep(400);
  const after = await page.evaluate(() => ({ total: document.querySelectorAll('.tab').length,
    g1: document.querySelectorAll('.group[data-group="1"] .tab').length, g2: document.querySelectorAll('.group[data-group="2"] .tab').length }));
  ok('V4 拖标签换组(总数守恒)', after.total === before && after.g2 === 1 && after.g1 === 1, `before=${before} after=${JSON.stringify(after)}`);

  /* V4 Ctrl+B 侧栏开合 */
  const b0 = await page.evaluate(SIDE);
  await ctrl(page, 'b'); await sleep(250);
  const b1 = await page.evaluate(SIDE);
  await ctrl(page, 'b'); await sleep(250);
  const b2 = await page.evaluate(SIDE);
  ok('V4 Ctrl+B 侧栏开合 + 桌面无遮罩', b0.open === 'true' && b1.open === 'false' && b2.open === 'true' && [b0, b1, b2].every((x) => x.mask === 'none'), `${b2.open} mask=${b0.mask}/${b1.mask}/${b2.mask}`);

  /* V4 Ctrl+W 关标签 */
  const w0 = await page.evaluate(() => document.querySelectorAll('.tab').length);
  await ctrl(page, 'w'); await sleep(350);
  const w1 = await page.evaluate(() => document.querySelectorAll('.tab').length);
  ok('V4 Ctrl+W 关标签', w1 === w0 - 1, `tabs=${w0}->${w1}`);

  /* V4 刷新 -> 布局恢复 */
  const pre = await page.evaluate(() => ({ tabs: document.querySelectorAll('.tab').length,
    split: document.querySelector('.groups').getAttribute('data-split'),
    keys: Array.from(document.querySelectorAll('.tab')).map((t) => t.getAttribute('data-key')) }));
  await page.reload({ waitUntil: 'load', timeout: 120000 }); await sleep(700);
  const post = await page.evaluate(() => ({ tabs: document.querySelectorAll('.tab').length,
    split: document.querySelector('.groups').getAttribute('data-split'),
    keys: Array.from(document.querySelectorAll('.tab')).map((t) => t.getAttribute('data-key')) }));
  ok('V4 刷新后布局恢复', pre.tabs === post.tabs && pre.split === post.split && JSON.stringify(pre.keys) === JSON.stringify(post.keys),
    `pre=${JSON.stringify(pre)} post=${JSON.stringify(post)}`);

  /* V5 命令面板「清空本地计数」:只清增量,烘焙仍在 */
  await ctrl(page, 'p', true); await sleep(300);
  await page.evaluate(() => { const i = document.getElementById('palette-q'); i.value = '清空本地计数'; i.dispatchEvent(new Event('input', { bubbles: true })); });
  await sleep(250);
  await page.keyboard.press('Enter'); await sleep(350);
  const cc = await page.evaluate((k) => { const store = JSON.parse(localStorage.getItem('note:counts') || '{}');
    const adds = Object.keys(store).map((x) => (store[x].add || 0));
    return { maxAdd: adds.length ? Math.max.apply(null, adds) : 0, seed: window.__COUNTS__[k].count,
      get: window.__counts.get(k).count, tree: document.querySelector('.tree-item[data-key="' + k + '"] .t-count').textContent }; }, COURSE);
  ok('V5 清空只清增量(烘焙仍在)', cc.maxAdd === 0 && cc.seed === 2 && cc.get === 2 && cc.tree === '2', JSON.stringify(cc));

  /* V8 无障碍:Tab 走一遍(先收侧栏,少走几百个树项),焦点环非 none */
  await ctrl(page, 'b'); await sleep(200);
  await page.evaluate(() => { if (document.activeElement) document.activeElement.blur(); });
  const seen = { act: false, tab: false, tree: false };
  for (let i = 0; i < 25 && !(seen.act && seen.tab); i++) {
    await page.keyboard.press('Tab');
    const f = await page.evaluate(FOCUS);
    if (/(^| )act( |$)/.test(f.cls) && f.ring) seen.act = true;
    if (/(^| )tab( |$)/.test(f.cls) && f.ring) seen.tab = true;
  }
  await ctrl(page, 'b'); await sleep(250);   /* 重新开侧栏 */
  await page.evaluate(() => document.getElementById('side-q').focus());
  for (let i = 0; i < 8 && !seen.tree; i++) {
    await page.keyboard.press('Tab');
    const f = await page.evaluate(FOCUS);
    if (/(^| )tree-item( |$)/.test(f.cls) && f.ring) seen.tree = true;
  }
  ok('V8 Tab 可达活动栏且焦点环可见', seen.act, JSON.stringify(seen));
  ok('V8 Tab 可达标签且焦点环可见', seen.tab, JSON.stringify(seen));
  ok('V8 Tab 可达树项且焦点环可见', seen.tree, JSON.stringify(seen));

  /* V6 主题:切暗色后工作台变暗,内嵌课 iframe 仍浅色 + 三张截图 */
  if (shots) await shot(page, shots, 'work-desktop-light.png');
  await page.click('#theme'); await sleep(350);
  const dk = await page.evaluate(() => ({ theme: document.documentElement.getAttribute('data-theme'),
    bg: getComputedStyle(document.body).backgroundColor, frameBg: getComputedStyle(document.querySelector('.lesson-frame')).backgroundColor }));
  ok('V6 暗色:工作台暗 / 课仍浅色', dk.theme === 'dark' && lum(dk.bg) < 90 && lum(dk.frameBg) > 200, JSON.stringify(dk));
  if (shots) await shot(page, shots, 'work-desktop-dark.png');
  await page.click('#theme'); await sleep(300);

  /* 断网:只放行 file://,点课仍要出标签 */
  const off = await browser.newPage();
  await off.setViewport({ width: 1200, height: 930 });
  await off.setRequestInterception(true);
  off.on('request', (req) => (req.url().startsWith('file:') ? req.continue() : req.abort()));
  await fresh(off, url);
  await off.click(`.tree-item[data-key="${COURSE}"]`); await sleep(650);
  const offr = await off.evaluate(() => ({ tabs: document.querySelectorAll('.tab').length,
    src: document.querySelector('.lesson-frame').getAttribute('src'), counts: !!window.__counts }));
  ok('断网可用(点课仍出标签)', offr.tabs === 1 && offr.counts && !!offr.src, `tabs=${offr.tabs} counts=${offr.counts}`);
  await off.close();
  await page.close();

  /* ================= 375×812 ================= */
  const m = await browser.newPage();
  await m.setViewport({ width: 375, height: 812 });
  await fresh(m, url);
  const mg = await m.evaluate(GENERIC);
  ok('375px 无横向滚动', mg.scrollW <= mg.innerW + 1, `scrollW=${mg.scrollW} innerW=${mg.innerW}`);
  const small = await m.evaluate(TOUCH);
  ok('375px 触达 >=44px', small.length === 0, small.join(' | '));
  ok('375px 对比度 >=4.5', mg.contrast >= 4.5 && mg.statusContrast >= 4.5, `正文=${mg.contrast} 状态栏=${mg.statusContrast}`);
  ok('375px 零外部资源', mg.external === 0, `external=${mg.external}`);
  const mv = await m.evaluate(() => { const b = document.getElementById('menu'); return { disp: getComputedStyle(b).display, box: b.offsetParent !== null }; });
  ok('V7 #menu 可见', mv.disp !== 'none' && mv.box, JSON.stringify(mv));
  const o0 = await m.evaluate(SIDE);
  ok('V7 全新状态抽屉默认关闭(无布局)', o0.open === 'false' && o0.mask === 'none', JSON.stringify(o0));
  await m.click('#menu'); await sleep(300);
  const o1 = await m.evaluate(SIDE);
  await m.mouse.click(340, 400); await sleep(300);   /* 点抽屉右侧的遮罩区(抽屉宽 300) */
  const o2 = await m.evaluate(SIDE);
  ok('V7 开抽屉遮罩可见、点遮罩关闭', o1.open === 'true' && o1.mask !== 'none' && o2.open === 'false' && o2.mask === 'none', JSON.stringify([o1, o2]));
  await ctrl(m, 'Backslash'); await sleep(350);
  const ms = await m.evaluate(() => { const gs = document.querySelector('.groups'), g2 = document.querySelector('.group[data-group="2"]');
    return { split: gs.getAttribute('data-split'), disp: getComputedStyle(g2).display, cols: getComputedStyle(gs).gridTemplateColumns }; });
  ok('V7 375px 分屏不出现', ms.split === 'true' && ms.disp === 'none', JSON.stringify(ms));
  if (shots) { await m.click('#menu'); await sleep(300); await shot(m, shots, 'work-375.png'); }
  await m.close();
} finally {
  await browser.close();
}

const bytes = fs.statSync(path.resolve(file)).size;
const { pass, fail } = count();
console.log(`页面 ${path.basename(file)} · ${(bytes / 1048576).toFixed(2)} MB`);
console.log(`结论:${fail === 0 ? 'PASS' : 'FAIL'}(${pass} 通过 / ${fail} 失败)`);
process.exit(fail === 0 ? 0 : 1);
