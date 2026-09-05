---
type: tutorial
tags: [markdown, 锚点, markdownlint, slug, MD033, MD051]
status: done
date: 2026-09-05
related: "[[Markdown-锚点跳转]]"
---

# Markdown 锚点与 markdownlint:为何 debug 的写法才 0 报错

> 场景:待办/清单类文件(如 `10-Projects/debug/` 下的三份)常以 `---` 分成多个**板块**,想在文件开头放一行「板块速览」链接,点击跳到对应板块。
> 本文回答:**为什么只有「每板块一个真实标题 + 速览链接写标题 slug」的写法,在装了 VS Code markdownlint 后 0 报错**;HTML 显式锚点为何在此环境不可用。
> 前置:锚点通用做法见 [Markdown-锚点跳转.md](<Markdown-锚点跳转.md>)。

---

## 一、现象:同一种诉求,三种写法的报错差异

给三个带板块的文件做「开头速览 + 板块跳转」,三种写法在 VS Code markdownlint 下的实测结果:

| 写法 | 样子 | lint 结果 |
|------|------|-----------|
| A. HTML 显式锚点 | 每板块前 `<a id="v1-0-0"></a>`,速览写 `[v1.0.0](#v1-0-0)` | 报 **MD033**(no-inline-html) |
| B. 纯标题 + 手写自定义链接 | `## v1.0.0`,速览写 `[v1.0.0](#v1.0.0)` | 报 **MD051**(link-fragments) |
| C. 纯标题 + 标题 slug 链接 | `## v1.0.0`,速览写 `[v1.0.0](#v100)` | **0 报错** |

markdownlint 实测命令(`markdownlint-cli2`,规则集默认):
- A 报 `MD033/no-inline-html Inline HTML [Element: a]`
- B 报 `MD051/link-fragments Link fragments should be valid [Context: "[v1.0.0](#v1.0.0)"]`
- C 干净通过

## 二、为什么:两条 lint 规则决定了「唯一解」

### 1. MD033 / no-inline-html:禁内联 HTML

markdownlint 默认规则**禁止在 Markdown 里写内联 HTML**,`<a id="...">` 属于内联 HTML,直接报错。
=> 想在文件里"自己设一个跳转点"的 `<a id>` 方案(即 [Markdown-锚点跳转.md](<Markdown-锚点跳转.md>) 里的「HTML 显式锚点」),在默认 lint 环境下**不可用**。

### 2. MD051 / link-fragments:链接片段必须能解析

markdownlint 会校验 `[x](#fragment)` 里的 `#fragment` **是否指向文件里真实存在的锚点目标**。它认的目标是:

- **标题自动生成的 slug**(`## 标题` → 系统按规则转 slug);
- 内联 HTML 里的 `id`(但 MD033 已先把它禁了)。

所以最稳的合法目标 = **标题的自动 slug**;手写的、与标题 slug 不一致的 fragment(如 `#v1.0.0`)会被 MD051 判为"无效链接片段"。

### 3. 标题 slug 到底怎么生成(关键)

规则(GitHub / markdownlint / VS Code 同一套,叫 GitHub-style slug):

> **转小写、空格变 `-`、去掉标点符号(点 `.`、括号 `()` 等)。**

实测对照(可直接复验):

| 标题 | 自动 slug | 速览应写 |
|------|-----------|----------|
| `## v1.0.0` | `#v100`(点被去掉) | `[v1.0.0](#v100)` |
| `## v1.1.1` | `#v111` | `[v1.1.1](#v111)` |
| `## 1. 标签页名称显示会话名` | `#1-标签页名称显示会话名`(点去掉、空格变 `-`、中文保留) | `[标签页名称显示会话名](#1-标签页名称显示会话名)` |
| `## 待办` | `#待办`(纯中文无标点 → 原样) | `[待办](#待办)` |

注意:标题 slug 对**中文标点/括号也会去掉**(如 `## 标题带(括号)内容` → slug 不含括号),速览里别写标题原文,要写 slug 后的形态。

## 三、规范:待办清单做「板块速览跳转」的正确姿势

1. **每个板块必须是一个真实标题**:`## v1.0.0`、`## 1. todo 功能增强`、`## 待办` 等;不要只写裸文本再用 `<a id>` 去锚。
2. **开头速览一行**,链接直接写**标题 slug**:

   ```markdown
   > **板块速览**:[v1.0.0](#v100) | [v1.1.1](#v111) | [待办](#待办)
   ```

3. **写链接时心里过一遍 slug 转换**:英文数字标题去点(`v1.0.0`→`#v100`);编号标题去点、空格变 `-`(`1. 标签页...`→`#1-标签页...`);纯中文标题原样。
4. **不要用 `<a id>`**:在装 markdownlint 的环境必然报 MD033;若某处实在要(非标题位置、中文精确锚点),需在 `.markdownlint.json` 显式关闭 `MD033` 才行:

   ```json
   { "MD033": false }
   ```

   (关闭后 `<a id>` 与 `#id` 即可用——见 [Markdown-锚点跳转.md](<Markdown-锚点跳转.md>) 的 HTML 显式锚点一节。)

## 四、debug 文件夹现状对照

- `10-Projects/debug/EmberTimer.md` — 版本板块(`## v1.0.0` 等)+「待办」板块,速览 `#v100`…`#待办` ✓
- `10-Projects/debug/pi-tab-status.md` — 两个 `## 1./## 2.` 板块,速览 `#1-…`、`#2-…` ✓
- `10-Projects/debug/config-ai.md` — 单板块编号清单,无多板块跳转需求(不开速览) ✓

三份均通过 markdownlint(除行宽 MD013 提示属另一规则,与锚点无关)。

## 相关

- [Markdown-锚点跳转.md](<Markdown-锚点跳转.md>) — 锚点通用做法(标题锚点 + HTML 显式锚点)
- [Markdown语法.md](../Markdown语法.md) — Markdown 全语法速查(15. 目录与锚点)
