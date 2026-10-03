/* 0-Note 站 · 工作台优化(V1/V2/V4/V5)实测补充,由 measure_site.mjs 调用(拆出守 ≤200 行)。
 * V1 搜索面板真输入「伪终端 / 前缀键 / SIGHUP」-> 各 ≥1 条命中且含 <mark>;
 * V2 活动栏三面板切换后侧栏内容真的不同; V4 侧栏(无 chip / 笔记树项 ≤80 / 默认展开 1 组);
 * V5 实时 DOM ≤4000 · load ≤400ms · 搜索 ≤30ms · 页面 ≤2.35MB。判据见 design §10。
 */
import { sleep } from './measure_site_probe.mjs';

const TERMS = ['伪终端', '前缀键', 'SIGHUP'];
const ACTS = { files: '.act[data-panel="files"]', search: '.act[data-panel="search"]', commands: '.act[data-panel="commands"]' };

const SIG = `(() => {
  const b = document.querySelector('.side-body:not([hidden])');
  return { panel: b && b.getAttribute('data-panel'), nodes: b ? b.querySelectorAll('*').length : 0,
    len: b ? b.textContent.trim().length : 0, aside: document.querySelector('.sidebar').getAttribute('data-panel') };
})()`;

/* V4 侧栏:筛选入口收在区块标题行(.side-head 下不再有 chip)· 笔记树项 ≤80 · 分组头默认只展开 1 个 */
export async function runSidebar(page, ok) {
  const r = await page.evaluate(() => ({
    chip: document.querySelectorAll('.side-head .chip').length,
    noteItems: document.querySelectorAll('.tree[data-group="note"] .tree-item').length,
    expanded: document.querySelectorAll('.tree-group[aria-expanded="true"]').length,
    groups: document.querySelectorAll('.tree-group').length,
  }));
  ok('V4 侧栏筛选入口已收(.side-head 无 chip)', r.chip === 0, `chip=${r.chip}`);
  ok('V4 笔记树项 ≤80(不再两视图叠加)', r.noteItems > 0 && r.noteItems <= 80, `noteItems=${r.noteItems}`);
  ok('V4 分组头默认只展开 1 个', r.expanded === 1, `expanded=${r.expanded}/${r.groups}`);
}

/* V2 活动栏三面板内容各不相同(2026-10-03 前是 1392 -> 1392)· V1 搜索真输入 · V5 搜索耗时 */
export async function runSearchPanels(page, ok) {
  const sigs = {};
  for (const [name, sel] of Object.entries(ACTS)) {
    await page.click(sel); await sleep(280);
    sigs[name] = await page.evaluate(SIG);
  }
  await page.click(ACTS.search); await sleep(280);   /* 面板可见才能真输入 */
  const s = sigs;
  ok('V2 三面板切换后侧栏内容真的不同',
    s.files.panel === 'files' && s.search.panel === 'search' && s.commands.panel === 'commands'
    && s.files.aside === 'files' && s.search.nodes !== s.files.nodes
    && s.commands.nodes !== s.files.nodes && s.commands.nodes !== s.search.nodes,
    Object.entries(s).map(([k, v]) => `${k}:${v.panel}/${v.nodes}节点/${v.len}字`).join(' | '));

  for (const term of TERMS) {
    await page.evaluate(() => { const q = document.getElementById('panel-q'); q.value = ''; q.dispatchEvent(new Event('input', { bubbles: true })); });
    await sleep(200);
    await page.type('#panel-q', term, { delay: 12 });   /* 真键盘输入 */
    await sleep(330);                                    /* 去抖 120 + 渲染 */
    const r = await page.evaluate(() => {
      const rows = document.querySelectorAll('#panel-results .res');
      return { res: rows.length, mark: document.querySelectorAll('#panel-results .res mark').length,
        typed: document.getElementById('panel-q').value,
        first: rows[0] ? rows[0].textContent.replace(/\s+/g, ' ').slice(0, 46) : '' };
    });
    ok(`V1 搜索面板输入「${term}」有结果且含 <mark>`, r.typed === term && r.res >= 1 && r.mark >= 1,
      `typed=${r.typed} res=${r.res} mark=${r.mark} 首条=${r.first}`);
  }
  await page.click(ACTS.files); await sleep(250);   /* 后续用例从资源管理器起 */
  const ms = await page.evaluate(() => {   /* 一次完整搜索(全库 110 条)的同步耗时 */
    const el = document.getElementById('panel-scope'); el.value = 'all';
    const t0 = performance.now(); el.dispatchEvent(new Event('change', { bubbles: true }));
    return performance.now() - t0;
  });
  ok('V5 全库搜索 ≤30ms', ms <= 30, `${ms.toFixed(1)}ms`);
}

/* V5 性能:实时 DOM · 首屏 load · 页面体量(须在 fresh 后、任何面板/标签改动前调用) */
export async function runPerf(page, ok, pageBytes) {
  const r = await page.evaluate(() => {
    const n = performance.getEntriesByType('navigation')[0];
    return { dom: document.getElementsByTagName('*').length,
      load: n ? Math.round(n.loadEventEnd - n.startTime) : -1 };
  });
  ok('V5 实时 DOM ≤4000(惰性 template)', r.dom > 0 && r.dom <= 4000, `实时 DOM=${r.dom}`);
  ok('V5 首屏 load ≤400ms', r.load > 0 && r.load <= 400, `load=${r.load}ms`);
  ok('V5 页面 ≤2.35MB', pageBytes <= 2_350_000, `${(pageBytes / 1048576).toFixed(2)}MB / 2.35MB`);
}
