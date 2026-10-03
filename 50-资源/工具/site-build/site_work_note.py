#!/usr/bin/env python3
"""0-Note 在线阅读站 · 笔记正文惰性实例化(`NOTE_TPL_JS`)。

正文不再预置在实时 DOM,而是每篇一个 `<template class="note-tpl" data-key>`(惰性,不占节点);
首次打开某篇笔记时由 `W.instantiateNote(key, host)` 把模板内容 `cloneNode(true)` 成一个
`div.note-body.card-body[data-key]` 塞进该组的 `.group-body[data-kind=note]`,之后复用已实例化的
那个(调用方 `showKind` 先查已有 `.note-body` 再调本函数)。

负向:模板缺失 / `data-key` 对不上(模板被改坏)-> 给「内容缺失」提示,不白屏、不抛异常
(行为自检见 `selftest_notes.py`)。契约见 `site_dom.CONTRACT`。
"""
from __future__ import annotations

NOTE_TPL_JS = r"""
/* 工作台·笔记正文惰性实例化(样式见 site_work_css,契约见 site_dom)。 */
(function () {
  "use strict";
  var doc = document, W = window.__work = window.__work || {};
  W.instantiateNote = function (key, host) {   /* 只做一次:调用方先查已有 .note-body */
    var nb = doc.createElement("div");
    nb.className = "note-body card-body";
    nb.setAttribute("data-key", key);
    nb.hidden = true;
    var tpl = null;
    try { tpl = doc.querySelector('template.note-tpl[data-key="' + W.esc(key) + '"]'); }
    catch (e) { tpl = null; }   /* key 含非法选择器字符也不能炸 */
    if (tpl && tpl.content && tpl.content.cloneNode) {
      nb.appendChild(tpl.content.cloneNode(true));
    } else {
      var p = doc.createElement("p");
      p.className = "note-missing";
      p.textContent = "内容缺失:找不到这篇笔记的正文(模板未找到)。";
      nb.appendChild(p);
    }
    host.appendChild(nb);
    return nb;
  };
})();
"""
