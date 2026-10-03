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

工作台页(body.work;site_work_css.WORK_CSS + site_work_js 照此产出;★ = 漏一项就坏页面/坏无障碍)
  ★ 内联顺序:site_css.CSS → PROSE → WORK_CSS → site_work_panels_css.PANEL_CSS。工作台样式放最后,
    同 specificity 时压过站点基线(否则 .chip .n 的 11px/12px、.icon-btn 的 44px 谁生效取决于顺序)
  body.work(固定外壳:height:100vh + overflow:hidden;滚动只发生在 .side-tree 与 .group-body 内部。
    主题仍由 html[data-theme=light|dark] 决定,暗色选择器命中 body.work;正文基线 15px/1.75)
    a.skip[href="#editor"](★类 .skip;侧栏上百项时键盘用户跳进编辑区的唯一出口,样式复用 site_css)
    header.titlebar > span.tb-title + div.tb-actions
        > button.icon-btn#theme[aria-label][aria-pressed](aria-pressed 表示是否暗色)
        + button.icon-btn#menu[aria-label][aria-expanded](窄屏开关侧栏,桌面可留)
        ※ #theme 与活动栏的 #act-theme 都改主题,site_work_js 必须同步两者 aria-pressed
    div.work-body(活动栏 + 侧栏 + 编辑区的横向容器;flex:1 + min-height:0,不外溢)
      nav.activity[aria-label] > button.act[data-panel=files|search|commands][aria-pressed][aria-label]
        + span.act-spacer + button.act#act-theme[aria-label]
        ※ 点非当前面板 -> 切面板;点当前面板 -> W.setSide(false) 收起侧栏(VS Code 行为);
          收起时点任一面板都先展开
        ※ 每个纯图标控件都内联 svg.icon(<svg class="icon">);★ 缺 class="icon" 时裸 SVG 按默认 300×150 渲染
      aside.sidebar[data-open=true|false][data-panel=files|search|commands]
        (data-panel 与活动栏 .act 的 aria-pressed 同步,决定哪个 .side-body 显示:
         files = 两棵树(课 + 笔记);search = 搜索框 + 结果列表;commands = 命令列表)
        ★ .side-body[data-panel] 与 aside 的 data-panel 不匹配时必须隐藏(hidden):渲染层初始就给
          search / commands 加 hidden;site_work_panels.PANELS_JS 跟 aside.sidebar 的 data-panel
          (MutationObserver),活动栏 / Ctrl+K / 命令面板切面板都会同步。site_work_filter 的 #side-q
          过滤只服务 files 面板。
        > div.side-head(files 面板的头:> input#side-q + div.filters(> button.chip);
            panel != files 时由 site_work_panels_css.PANEL_CSS 隐藏)
        + div.side-body.side-tree[data-panel=files]
          ul.tree[data-group=course|note]
            > li(分组容器)
                > button.tree-group[aria-expanded=true|false](分组头:项目名 + 计数,点击折叠;
                    aria-expanded 放在这个可聚焦的 button 上,不放无法聚焦的 li)
                    > span.t-name + span.t-count
                + ul(> li > button.tree-item[...])(折叠时整组隐藏)
            > li > button.tree-item[data-key][data-kind][data-count][data-href](可选:未分组的平铺项)
                > span.t-name(名称)+ span.t-count(打开次数)+ span.badge[data-type](类型徽章)
                + span.tag(标签 chip,可多个)
          课 data-kind=lesson(或 course,site_work_js 归一为课),笔记 data-kind=note;
          data-count = 打开次数,首屏由 site_work_js 回填;
          ★ 课要能打开,树项必须带 data-href(课=仓库相对路径,笔记可省):site_work_js 依次读
            树项 data-href -> 课 iframe 的 data-src -> window.__INDEX__.href,都读不到则 iframe 停在 about:blank
          ★ .tree-item[aria-current=true] = 「当前在编辑区打开的那一条」(不是 hover/焦点)
        + div.side-body[data-panel=search]
          > div.panel-search
            > div.panel-search-row(> input#panel-q[type=search] + select#panel-scope)
                (scope 取值 all|course|note|tag,选项文字 全部/课程/笔记/标签)
            + ul#panel-results[role=listbox](> li.res[role=option][data-key] > span.res-head
                > span.badge[data-type] + span.res-name + span.res-snip > mark)
            + div#panel-empty(空状态:> p.pe-title + div.pe-actions
                > button.pe-btn[data-term](三个示例词:伪终端 / 恢复密钥 / tmux))
        + div.side-body[data-panel=commands]
          > div#cmds-list[role=list](> button.cmd[data-cmd][disabled?][aria-current?]
                > span.cmd-name + span.cmd-hint)
            (命令表唯一真源 = site_work_cmds.CMDS,17 条;注音 note-view 是禁用占位(Task 5 后启用),
             其余 16 条由 site_work_cmds.CMDS_JS 的 RUN 表逐条执行,每条都改变可观测状态;
             ↑↓ 在启用命令间移动(aria-current 标当前项)· Enter 执行 · Esc 回 files 并把焦点交回活动栏按钮)
      main.editor#editor(a.skip 的落点)
        div.groups[data-split=true|false] > section.group[data-group=1|2]
          > div.group-tabs[role=tablist](★ 每组自己的标签栏:VS Code 就是每组建标签栏,
              外层标签栏已删,不再有 .tabs —— 两层都渲染会白堆 70px)
                > div.tab-cell[role=presentation](一个标签 = 标签按钮 + 关闭按钮;
                    ★ 两者都是 <button>,不能再相互嵌套 —— 嵌套会被 HTML 解析器拆开)
                    > button.tab[role=tab][data-key][aria-selected] > span.t-name
                    + button.t-close[aria-label="关闭标签"](★ 纯图标控件:必须可聚焦且有无障碍名)
          + div.group-body[data-kind=welcome|note|lesson]
            (课:iframe.lesson-frame[src][title](可带 data-src 作路径兜底);笔记:div.note-body[data-key];
             欢迎页见下;★ 欢迎页是「该组无标签时的空态」,不占标签 —— 标签栏里只有真条目)
            ★ .group-body[hidden] 必须真隐藏 —— 与 [data-kind=lesson] 同为 (0,2,0),
              规则里用 display:none!important 兜底,否则隐藏面板仍占着编辑区
        ※ div.note-body 要带正文排版类(site_css_prose.PROSE 的 .card-body),与工作台 15px/1.75 一致
      footer.statusbar > button.st-item[data-act=welcome|open|read|thecount|theme|split]
        (.st-items + .st-open + .st-progress + .st-count + .st-theme + .st-split,六段全部可点)
        welcome = 清空当前组标签回空态 · open = 侧栏切 commands 面板 ·
        read = W.onlyUnread(true) 只筛未读的课 · thecount = 弹出当前课计数详情浮层 ·
        theme = 同 #act-theme · split = 同 Ctrl+\
        ※ thecount 的浮层是 site_work_status.STATUS_JS 自建的 div.st-pop#st-pop
          (role=dialog;hidden 时 display:none;点浮层 / 点别处 / Esc 收起,不用 alert);
        ※ 数字是首屏初值,site_work_status 的 W.status 按需回填(打开数 / 本课次数 / 已读进度)
    div.side-mask(★ 遮罩由 WORK_CSS 负责;站点 site_css 里也有一份 .side-mask 定义,以 WORK_CSS 为准)

工作台欢迎页(.group-body[data-kind=welcome] 的内部内容)
  ★ 只含:div.overview(总览条)+ div.proj-grid > div.proj-card(项目卡网格)
    + div.cards > article.card(条目流)+ div.filters > button.chip(筛选)+ p.no-result#empty(无结果提示)
  ★ 不含外壳元素:旧阅读页的 header.bar / a.skip / main#main / nav.side / input#q / button#theme /
    button#menu / button.to-top#toTop —— 这些由工作台外壳提供,重复会出现两套顶栏 / 两套主题键
  ★ 欢迎页保留并复用的 id / 类:#count(命中数,外壳不占)· #empty · #clear2 · .filters · .chip · .card
  (工作台外壳里的 #side-q / #theme / #menu / #editor / #act-theme 与上列不撞车)

工作台★(漏了就坏)
  body.work 固定高度(100vh + overflow:hidden):长侧栏下 document.body.scrollHeight == innerHeight,
    否则活动栏被拉到数千像素、随页面滚走,.side-tree{overflow:auto} 永不生效
  .sidebar[data-open=false] 必须 visibility:hidden(只 width:0 时屏外元素仍可被 Tab 聚焦)
  .tab[aria-selected=true] 必须有可辨高亮(顶部强调线 + 文字用强调色),否则看不出当前打开的是哪一个
  iframe.lesson-frame 必须 height:100%(缺则退化成默认约 150px,课区一片空白)
  .statusbar 固定底部,body 用 padding-bottom:var(--w-status) 抵消(缺则遮住正文末尾)
  .groups[data-split=false] 时 .group[data-group=2] 必须隐藏(site_work_js 拆分时去掉它的 hidden
  与 .group-tabs 的 hidden、合并时加回;只靠 CSS 不够)
  课容器必须有"内嵌文档"标题条(.group-body[data-kind=lesson]::before),说明它是独立页面、未随工作台换肤
  活动栏 / 标签栏 / 侧栏树全键盘可达,每个纯图标控件各有无障碍名;≤768px 侧栏走 .side-mask 抽屉
  ≤768px 触达 ≥44px(活动栏按钮 / 图标按钮 / 标签 / 树项 / 筛选 chip):
    .side-head .chip 桌面是 22px,移动端必须显式抬到 44px,否则会压过 site_css 的 44px 规则

命令面板 / 快速打开(site_work_palette.PALETTE_JS 在 window.__work 就绪后自建并 append 到 body;
  ★ 渲染层不产出这段 DOM,模态的显隐与焦点全归该脚本;样式在 site_work_css.WORK_CSS
  —— 脚本不再自注入 <style>,仍是零外部资源,不是 <link rel=stylesheet>,也不是 @import)
  div.palette#palette[role=dialog][aria-modal=true][aria-label=快速打开|命令面板][hidden]
    > div.palette-box
      > input#palette-q[type=text][role=combobox][aria-expanded][aria-controls=palette-list]
        [aria-activedescendant][autocomplete=off]
      > ul#palette-list[role=listbox] > li[role=option][id=palette-opt-<n>][aria-selected=true|false]
      > div.palette-hint(快捷键提示)
  ★ hidden 时不可见且不可聚焦(display:none!important;只用 opacity/visibility 屏外仍可 Tab);
    打开时焦点进 #palette-q;关闭时焦点精确还回「打开前」那个元素;aria-activedescendant 指向当前
    高亮 li 的 id(无高亮时为空串);aria-expanded 反映面板开合。
  ★ 焦点陷阱:面板开着时 Tab 在面板内循环,focusin 逃逸即拉回 #palette-q;Esc 关闭并还原焦点。
    打开条目一律走 window.__work 的 open/close/empty/setSplit/setSide(不另写标签逻辑),
    清空本地计数走 window.__counts.clear()。
"""
