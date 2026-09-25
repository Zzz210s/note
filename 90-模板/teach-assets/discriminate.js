/* 0-Note 教学工作区 · 共享辨析练习组件(名词解释类工作区通用)
   「辨析」练的不是知识,是技能:给一个真实场景,判断它属于哪个名词。
   每例即时反馈(复用 quiz.js 的反馈环,不重复实现),整组给一次计分。

   用法(见 10-项目/!名词解释/lessons/0001-*.html):
     <div class="drill">
       <div class="item quiz" data-answer="CLI">
         <p class="q">场景文字…</p>
         <button data-key="CLI">CLI</button>
         <button data-key="TUI">TUI</button>
         <button data-key="GUI">GUI</button>
         <p class="why">为什么:…</p>
       </div>
       … 3~5 例 …
     </div>

   依赖:先加载 quiz.js(暴露 window.teachQuiz.init)。
   `.item` 带 `quiz` 类是为了直接沿用共享样式;重复绑定由 quiz.js 的 `data-bound` 挡掉。 */
(function () {
  "use strict";

  function bindDrill(drill) {
    var items = Array.prototype.slice.call(drill.querySelectorAll(".item"));
    if (!items.length || !window.teachQuiz) { return; }

    items.forEach(function (el) { window.teachQuiz.init(el); });

    var bar = document.createElement("p");
    bar.className = "drill-score";
    drill.appendChild(bar);

    function refresh() {
      var done = items.filter(function (el) { return el.dataset.done === "1"; }).length;
      var first = items.filter(function (el) { return el.dataset.tries === "1"; }).length;
      bar.textContent = done < items.length
        ? "已判断 " + done + " / " + items.length + " 例。"
        : items.length + " 例都判完了,一次答对 " + first + " 例。" +
          (first === items.length ? "判据已经在你手上。" : "没全对就回上面那张判定表再走一遍。");
    }

    drill.addEventListener("click", function () { setTimeout(refresh, 0); });
    refresh();
  }

  document.addEventListener("DOMContentLoaded", function () {
    Array.prototype.forEach.call(document.querySelectorAll(".drill"), bindDrill);
  });
})();
