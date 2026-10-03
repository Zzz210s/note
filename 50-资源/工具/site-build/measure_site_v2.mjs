/* 0-Note 站 · 工作台优化(V3/V6/V8)实测补充,由 measure_site.mjs 调用(拆出守 ≤200 行)。
 * V3 状态栏六段逐段点击都有可观测变化(六条独立断言); V6 四档宽度无横滚 / 卡片 ≤4 列 / 侧栏宽度;
 * V8 全键盘可达(活动栏 / 标签 / 树 / 状态栏)+ Esc 关面板后焦点回到原处。判据见 design §10。
 */
import { sleep, fresh, ctrl, FOCUS } from './measure_site_probe.mjs';

const ACTS6 = /^(welcome|open|read|thecount|theme|split)$/;

/* V3 状态栏六段:每段点击各一条断言(调用点需已有一节课打开、浅色、侧栏在 files) */
export async function runStatus(page, ok) {
  const click = async (act) => { await page.click(`.statusbar .st-item[data-act="${act}"]`); await sleep(320); };
  if (await page.evaluate(() => document.querySelectorAll('.tab').length) === 0) {   /* 确保有课可开 */
    await page.evaluate(() => { const it = document.querySelector('.tree-item[data-kind="course"]'); if (it) it.click(); });
    await sleep(700);
  }

  await click('thecount');
  const pop = await page.evaluate(() => { const p = document.getElementById('st-pop');
    return { shown: !!p && !p.hidden, rows: p ? p.querySelectorAll('.st-pop-row').length : 0 }; });
  ok('V3 状态栏 thecount 弹出计数浮层', pop.shown && pop.rows >= 1, JSON.stringify(pop));
  await page.keyboard.press('Escape'); await sleep(200);

  const sp0 = await page.evaluate(() => document.querySelector('.groups').getAttribute('data-split'));
  await click('split');
  const sp1 = await page.evaluate(() => document.querySelector('.groups').getAttribute('data-split'));
  ok('V3 状态栏 split 切换分栏', sp0 === 'false' && sp1 === 'true', `split ${sp0}->${sp1}`);

  const th0 = await page.evaluate(() => document.documentElement.getAttribute('data-theme'));
  await click('theme');
  const th1 = await page.evaluate(() => document.documentElement.getAttribute('data-theme'));
  ok('V3 状态栏 theme 切换明暗', th0 !== th1, `theme ${th0}->${th1}`);

  await click('read');
  const rd = await page.evaluate(() => ({
    pressed: Array.from(document.querySelectorAll('.sec-filter')).map((b) => b.getAttribute('aria-pressed')),
    count: (document.getElementById('count') || {}).textContent || '' }));
  ok('V3 状态栏 read 只筛未读的课', rd.pressed.length >= 2 && rd.pressed.every((p) => p === 'true') && /\d+ \/ \d+ 条/.test(rd.count),
    JSON.stringify(rd));

  await click('open');
  const op = await page.evaluate(() => ({ aside: document.querySelector('.sidebar').getAttribute('data-panel'),
    shown: !document.querySelector('.side-body[data-panel="commands"]').hidden }));
  ok('V3 状态栏 open 侧栏切到命令面板', op.aside === 'commands' && op.shown, JSON.stringify(op));

  const t0 = await page.evaluate(() => document.querySelectorAll('.group[data-group="1"] .tab').length);
  await click('welcome');
  const t1 = await page.evaluate(() => document.querySelectorAll('.group[data-group="1"] .tab').length);
  ok('V3 状态栏 welcome 清空标签回欢迎页', t0 >= 1 && t1 === 0, `tabs ${t0}->${t1}`);
}

/* V6 五档断点中的四档:480 抽屉 / 900 侧栏 220 / 1100 侧栏 260 / 1500 侧栏 280 */
export async function runWidths(browser, url, ok) {
  for (const [w, exp] of [[480, 'drawer'], [900, 220], [1100, 260], [1500, 280]]) {
    const p = await browser.newPage();
    await p.setViewport({ width: w, height: 930 });
    await fresh(p, url);
    const r = await p.evaluate(() => {
      const sb = document.querySelector('.sidebar'), cs = getComputedStyle(sb);
      return { scrollW: document.documentElement.scrollWidth, innerW: window.innerWidth,
        cols: getComputedStyle(document.querySelector('.proj-grid')).gridTemplateColumns.split(' ').length,
        pos: cs.position, sideW: sb.offsetWidth };
    });
    const sideOk = exp === 'drawer' ? r.pos === 'fixed' && r.sideW > 0 : Math.abs(r.sideW - exp) <= 1;
    ok(`V6 ${w}px 无横滚 + 卡片 ≤4 列`, r.scrollW <= r.innerW + 1 && r.cols >= 1 && r.cols <= 4,
      `scrollW=${r.scrollW} innerW=${r.innerW} cols=${r.cols}`);
    ok(`V6 ${w}px 侧栏宽度合理(${exp === 'drawer' ? '抽屉' : exp + 'px'})`, sideOk, `pos=${r.pos} offsetWidth=${r.sideW}`);
    await p.close();
  }
}

/* V8 全键盘可达 + Esc 还焦点(替代原先内联的 Tab 块,顺带补状态栏与 Esc) */
export async function runKeys(page, ok) {
  if (await page.evaluate(() => document.querySelector('.sidebar').getAttribute('data-open')) === 'true') {
    await ctrl(page, 'b'); await sleep(250);
  }
  await page.evaluate(() => { if (document.activeElement) document.activeElement.blur(); });
  const seen = { act: false, tab: false, tree: false };
  for (let i = 0; i < 40 && !(seen.act && seen.tab); i++) {
    await page.keyboard.press('Tab');
    const f = await page.evaluate(FOCUS);
    if (/(^| )act( |$)/.test(f.cls) && f.ring) seen.act = true;
    if (/(^| )tab( |$)/.test(f.cls) && f.ring) seen.tab = true;
  }
  await ctrl(page, 'b'); await sleep(250);   /* 重开侧栏走树 */
  await page.evaluate(() => document.getElementById('side-q').focus());
  for (let i = 0; i < 8 && !seen.tree; i++) {
    await page.keyboard.press('Tab');
    const f = await page.evaluate(FOCUS);
    if (/(^| )tree-item( |$)/.test(f.cls) && f.ring) seen.tree = true;
  }
  ok('V8 Tab 可达活动栏且焦点环可见', seen.act, JSON.stringify(seen));
  ok('V8 Tab 可达标签且焦点环可见', seen.tab, JSON.stringify(seen));
  ok('V8 Tab 可达树项且焦点环可见', seen.tree, JSON.stringify(seen));

  /* 状态栏:关掉所有标签回欢迎页(编辑区最后一项是卡片链接),Tab 应一路走完六段 */
  let tabs = await page.evaluate(() => document.querySelectorAll('.tab').length);
  while (tabs-- > 0) { await ctrl(page, 'w'); await sleep(120); }
  const last = await page.evaluate(() => {
    const els = Array.prototype.filter.call(
      document.querySelectorAll('.editor button,.editor a[href],.editor [tabindex]:not([tabindex="-1"])'),
      (e) => e.offsetParent !== null);
    if (!els.length) return null;
    els[els.length - 1].focus();
    return els[els.length - 1].className || els[els.length - 1].tagName;
  });
  const acts = [];
  for (let i = 0; i < 8; i++) {
    await page.keyboard.press('Tab');
    const a = await page.evaluate(() => { const e = document.activeElement;
      return e && e.classList && e.classList.contains('st-item') ? e.getAttribute('data-act') : ''; });
    if (!ACTS6.test(a)) break;
    acts.push(a);
  }
  ok('V8 Tab 可达状态栏六段', !!last && new Set(acts).size === 6, `起点=${last} 序列=${acts.join(',')}`);

  await page.evaluate(() => { const it = document.querySelector('.tree-item[data-kind="course"]'); if (it) it.focus(); });
  const key = await page.evaluate(() => (document.activeElement.getAttribute || function () {}).call(document.activeElement, 'data-key'));
  await ctrl(page, 'p'); await sleep(300);
  const opened = await page.evaluate(() => !document.getElementById('palette').hidden);
  await page.keyboard.press('Escape'); await sleep(300);
  const back = await page.evaluate(() => { const e = document.activeElement;
    return { key: (e.getAttribute || function () {}).call(e, 'data-key'), hidden: document.getElementById('palette').hidden }; });
  ok('V8 Esc 关面板后焦点回到原处', opened && back.hidden && !!key && back.key === key, `key=${key} 回来=${back.key}`);
}
