/*!
 * lesson-track.js —— 把「进入过几次」显示在课件名字的最前端(纯本机,不联网、不用 AI)
 *
 * 放在 `90-模板/teach-assets/` 全库共用一份。每节课在结尾引它:
 *   <script src="../../../90-模板/teach-assets/lesson-track.js"></script>
 *
 * 它做三件事:
 *  1. **页面自己数**:每次打开把本地计数 +1(存浏览器 localStorage),并把「[N 次] 原标题」
 *     写到标签页名字的最前面,正文标题前也插一条小标签 —— 任何打开方式都算(双击、VS Code、浏览器)。
 *  2. **能拿到全局数字就用全局的**:本机小服务(lesson-track/server.py)在跑的时候,
 *     向它要 `counts.json`,取「全局次数」与本页本地次数的较大者 —— 这样页面显示的数字
 *     与各项目 `00-索引.md` 里的是同一个。
 *  3. 服务没跑也不报错:安静退回本地计数。
 *
 * 它**不写磁盘**(页面没有那个权限),所以索引那边的数字仍然由
 * `更新进度.cmd` / 小服务负责回写 —— 两者对同一批数据取最大值,不会互相污染。
 */
(function () {
  "use strict";

  var SERVICE = "http://127.0.0.1:8787";
  var TITLE = document.title;
  var URLKEY = location.href.split("?")[0].split("#")[0];
  var K_COUNT = "lesson-entry:" + URLKEY;
  var K_LAST = "lesson-entry-last:" + URLKEY;

  function read(k) {
    try { return localStorage.getItem(k); } catch (e) { return null; }
  }
  function write(k, v) {
    try { localStorage.setItem(k, v); } catch (e) { /* 隐私模式等,忽略 */ }
  }

  /** 从页面地址里取出「10-项目/…」这一段,和 counts.json 的键对齐。 */
  function vaultRel() {
    var u = decodeURIComponent(URLKEY).replace(/\\/g, "/");
    var i = u.indexOf("/10-项目/");
    return i < 0 ? null : "10-项目/" + u.slice(i + "/10-项目/".length);
  }

  function today() {
    var d = new Date();
    return d.getFullYear() + "-" + ("0" + (d.getMonth() + 1)).slice(-2) + "-" + ("0" + d.getDate()).slice(-2);
  }

  var styleDone = false;
  function paint(count, last) {
    if (!count) { return; }
    document.title = "[" + count + " 次] " + TITLE;
    if (!styleDone) {
      var st = document.createElement("style");
      st.textContent = ".entry-count{font-size:.85rem;color:#6b6b6b;margin:.2rem 0 0;" +
                       "padding:.1rem .5rem;border:1px solid #d8d3ca;border-radius:3px;display:inline-block}";
      document.head.appendChild(st);
      styleDone = true;
    }
    var box = document.querySelector(".entry-count");
    if (!box) {
      box = document.createElement("p");
      box.className = "entry-count";
      var h1 = document.querySelector("h1");
      if (h1 && h1.parentNode) { h1.parentNode.insertBefore(box, h1); } else { document.body.insertBefore(box, document.body.firstChild); }
    }
    box.textContent = "进入 " + count + " 次" + (last ? "(最近 " + last + ")" : "");
  }

  // ① 本页自己 +1(任何打开方式都算)
  var mine = parseInt(read(K_COUNT) || "0", 10) + 1;
  write(K_COUNT, String(mine));
  var lastSeen = read(K_LAST) || today();
  write(K_LAST, today());
  paint(mine, lastSeen);

  // ② 服务在跑就用全局数字(与索引一致);取较大者,避免页面与服务互相污染
  if (typeof fetch === "function") {
    fetch(SERVICE + "/counts.json", { cache: "no-store" })
      .then(function (r) { return r.ok ? r.json() : null; })
      .then(function (data) {
        if (!data) { return; }
        var rec = data[vaultRel()];
        if (rec && rec.count) { paint(Math.max(rec.count, mine), rec.last || lastSeen); }
      })
      .catch(function () { /* 服务没跑,保持本地计数 */ });
  }
})();
