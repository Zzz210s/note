/* 0-Note 教学工作区 · 共享测验组件
   用法(见 lessons/0001-*.html):
     <div class="quiz" data-answer="b">
       <p class="q">题干?</p>
       <button data-key="a">选项甲</button>
       <button data-key="b">选项乙</button>
       <p class="why">为什么:…</p>
     </div>
   行为:选对 → 变绿并展开解析;选错 → 变红并提示重试(允许反复尝试,符合"努力回忆"原则)。
   选项长度由作者保证等长,组件不做处理。
   2026-09-25:暴露 `window.teachQuiz.init(box)`,供其它组件(如 discriminate.js)复用同一个
   即时反馈环;重复绑定由 `data-bound` 挡掉,所以 `.quiz` 自动绑定与显式调用可以并存。 */
(function () {
  "use strict";

  function initQuiz(box) {
    if (box.dataset.bound === "1") { return; }
    box.dataset.bound = "1";
    var answer = (box.dataset.answer || "").trim();
    var why = box.querySelector(".why");
    var buttons = Array.prototype.slice.call(box.querySelectorAll("button[data-key]"));
    var tries = 0;

    var score = document.createElement("p");
    score.className = "score";
    box.appendChild(score);

    function refresh() {
      box.dataset.tries = String(tries);
      if (box.dataset.done === "1") {
        score.textContent = tries === 1 ? "一次答对。" : "答对了(第 " + tries + " 次)。";
      } else if (tries > 0) {
        score.textContent = "再想一次 —— 回到上一节的定义对照一下。";
      }
    }

    buttons.forEach(function (btn) {
      btn.addEventListener("click", function () {
        if (box.dataset.done === "1") { return; }
        tries += 1;
        if (btn.dataset.key === answer) {
          btn.classList.add("correct");
          box.dataset.done = "1";
          if (why) { why.classList.add("show"); }
          buttons.forEach(function (b) { b.disabled = true; });
        } else {
          btn.classList.add("wrong");
        }
        refresh();
      });
    });
    refresh();
  }

  window.teachQuiz = { init: initQuiz };

  document.addEventListener("DOMContentLoaded", function () {
    Array.prototype.forEach.call(document.querySelectorAll(".quiz"), initQuiz);
  });
})();
