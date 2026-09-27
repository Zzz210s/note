/*!
 * lesson-close-beacon.js —— 关掉课件时,悄悄告诉本机服务「这一节我读完了」。
 *
 * 为什么需要它:用户要的口径是「**关掉**课件才算读过一次」,而不是打开就算。
 * 页面自己写不了磁盘,但可以在关闭的那一刻发一个请求出去 —— 服务收到就 +1,并顺手改名。
 *
 * 特点(刻意做得最小):
 *  - 不显示任何东西、不改标题、不存本地计数;
 *  - 用 `navigator.sendBeacon`(关页面时也能发出去),不行再退回 `fetch(..., keepalive)`;
 *  - 服务没在跑就安静失败,不影响阅读(次数仍有兜底来源:VS Code 历史);
 *  - 只在 `pagehide` / `beforeunload` 触发,且每次打开只上报一次。
 */
(function () {
  "use strict";
  var SERVICE = "http://127.0.0.1:8787";
  var MARK = "/10-项目/";
  var sent = false;

  function rel() {
    var u = decodeURIComponent(location.href).split("?")[0].split("#")[0].replace(/\\/g, "/");
    var i = u.indexOf(MARK);
    return i < 0 ? null : "10-项目/" + u.slice(i + MARK.length);
  }

  function report() {
    if (sent) { return; }
    var r = rel();
    if (!r) { return; }
    sent = true;
    var body = JSON.stringify({ rel: r });
    try {
      if (navigator.sendBeacon) {
        navigator.sendBeacon(SERVICE + "/closed", new Blob([body], { type: "text/plain" }));
        return;
      }
    } catch (e) { /* 继续走 fetch */ }
    try {
      fetch(SERVICE + "/closed", { method: "POST", body: body, keepalive: true, mode: "no-cors" });
    } catch (e) { /* 服务没跑就什么都不做 */ }
  }

  window.addEventListener("pagehide", report);
  window.addEventListener("beforeunload", report);
})();
