#!/usr/bin/env python3
"""0-Note 在线阅读站 · 渲染层与静态资源的接口契约(唯一真源)。

`site_css.CSS` 与 `site_js.JS` 都照 `CONTRACT` 描述产出/消费 DOM;Task 4 的
`site_render.py` / `build_site.py` 必须逐字照它产出,否则页面会坏(下面标 ★ 的
都是「漏一项就坏页面/坏无障碍」的项,不是可选建议)。

契约只此一份:site_css / site_js 的模块 docstring 都指向这里,改契约先改本文件
(为守住库规「每个 .py ≤ 200 行」,契约从 CSS 模块里拆出来单独成文件)。
"""

CONTRACT = """\
DOM 契约(渲染层逐字照此产出,site_js 依赖同一套;★ = 漏一项就坏页面/坏无障碍)
  顶层:html[data-theme=light|dark](由 site_js.BOOT 在 <head> 内联设定,免首屏闪烁)
        body(滚动 >40px 加 .scrolled → 移动端收起搜索行)
        a.skip[href=#main](键盘跳转;★类 .skip,缺则常显在页首) · span.sr(纯视觉隐藏,给 #q 当 <label>)
  顶栏 header.bar > .bar-inner >
    a.brand(纯文本 + <small>) · div.search-wrap(有搜索词时由 JS 加 .has-text)
    div.search-wrap > span.search-ico★(内联 SVG,绝对定位 left:10px;缺则图标 static 挤在输入框前)
      + input.search#q[type=search](★类 .search;无障碍名用 aria-label 或 <label class="sr">)
      + button.search-clear#clear[aria-label](★类 .search-clear;缺则原生按钮样式且一直显示)
      + span.search-count#count[aria-live=polite](命中数;无筛选时为空串)
    span.spacer★(flex:1;缺则主题按钮左贴、右侧顶栏空着)
    button.icon-btn#theme[aria-label][aria-pressed](主题开关,aria-pressed 表示是否暗色)
    button.icon-btn.menu-btn#menu[aria-label][aria-expanded=false](★类 .menu-btn;缺则桌面 1200px 也可见)
  布局:main#main > .layout(≥1024px 才是 grid:var(--side) 侧栏 + 1fr 正文,以下单列)
        nav.side[aria-label] > ul.toc > li > a[href=#sec-<slug>] > span.dot[data-status][aria-hidden=true] + span.n
          ★ .dot[aria-hidden=true]:状态色不是唯一线索,读屏不该念出这个纯装饰点
        div.content(★ .overview / .filters / .proj-grid / section.sec / p#empty 都是它的子节点;
          与 .layout 平级会让总览条跑到侧栏左侧)
          div.overview(> span,内含 <b>)
          div.filters(> span.lbl 说明 + button.chip 若干)
          div.proj-grid > div.proj-card(> h3.proj-name + p.proj-desc + div.proj-stats(> span > b)
            + progress.proj-prog[value][max][aria-label],value/max 必填否则进度条不动)
          section.sec#sec-<slug> > h2.sec-title + div.cards
          p.no-result#empty[hidden 初始;无命中时由 JS 去掉 hidden] > button.link-btn#clear2[aria-label]
            (★类 .link-btn;缺则原生按钮)
  卡片:div.cards > article.card#<slug>[data-kind=course|know|project]
        [data-status=learning|todo|done|not-started|""](没有状态时留空串)
        > div.card-head(> h3.card-title > a + div.card-meta(> span.badge[data-type][data-status] + span.when))
          + p.card-sum + p.card-win(仅课卡片,可缺) + div.card-rel(可缺)
        ★ .card-title a 与 p.card-sum 只放纯文本:搜索高亮 mark() 用 textContent 整段重建,
          里面放 <span> 会在第一次按键后被抹掉,且清空搜索也回不来
        span.when 是日期小字(.card-meta .when)· div.card-rel 是相关链接行
  筛选:button.chip[data-group=kind|status][data-value][aria-pressed=false] > span.n
        ★ data-value 取值必须与卡片 data-kind / data-status 完全一致,否则计数恒 0
        ★ data-value 不得为空(JS 把空值当「无约束」,但空 value 的 chip 本身没有意义)
  其它:button.to-top#toTop[aria-label] · div.side-mask · footer.foot
  徽章 data-type:course / know / project / log / index / template

无障碍必填(★)
  #count 有 aria-live=polite;#theme / #menu / #clear / #clear2 / #toTop 五个纯图标控件各有无障碍名;
  #menu 初始 aria-expanded=false;.toc .dot 有 aria-hidden=true;#q 配 <label class="sr"> 或 aria-label;
  .card-title a / .card-sum 只放文本节点。

内联索引 JSON(window.__INDEX__)
  渲染层必须按 json.dumps(index, ensure_ascii=False).replace("<", "\\\\u003c") 写出。
  ★ 不转义 "<" 时,任一条目含 "</script>" 会提前闭合脚本 → SyntaxError → window.__INDEX__
    不是数组 → 整个交互脚本不执行(主题/搜索/筛选/目录/返回顶部全死),JSON 尾巴还会当正文显示。
  "<!--" 无需处理(已实测安全)。条目字段:{title,summary,text,kind,status,anchor,href},anchor == 卡片 id。
"""
