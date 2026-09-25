---
type: concept
tags: [开发工具, CI, 持续集成, 自动化, GitHub Actions, 概念辨析]
status: done
date: 2026-09-25
related: "[[巡检器]]"
---

# CI(持续集成)是什么

> 「在这个 PR 上 CI 挂了」「等 CI 绿了再合并」—— 这句话里的 CI 到底在干什么?为什么它一挂就没人敢合并?
> 本文讲清 CI 这个词的严格含义、它在一次真实提交里长什么样,以及它和 linter / 测试夹具 / 巡检器的分工。
> **本文的固定写法**:每个概念按「**为解决什么痛点而生 / 一句话定义 / 大白话注解**」三段给出,再展开细节。
> 关联阅读:[巡检器](<巡检器.md>)(同一个「检查」思路的手动版)、
> [CI/CD 与 GitHub Actions 实战](../../!系统与工具/20-知识/CI-CD与GitHub-Actions实战.md)(怎么从零写一个 workflow)。

---

## 一句话速览

| 名称 | 一句话定义 | 大白话注解 |
| --- | --- | --- |
| **CI(持续集成)** | 一种开发实践:每个人**至少每天**把自己改动合进同一条主线,并由**自动化构建(含测试)**验证这次合并 | 不是工具,是「天天合、合完自动验」的规矩 |
| **自动化构建(build)** | 一条命令就能从源码得到可运行的系统 | 「换台干净机器、拉代码、敲一条命令,系统跑起来」 |
| **流水线(pipeline)** | 把构建与检查串成有先后的一串阶段 | 排队过关:先语法、再单测、最后检查密钥 |
| **workflow / job / step** | GitHub Actions 里的三层容器:一个 workflow 有多个 job,一个 job 有多个 step | workflow = 一份剧本,job = 一幕,step = 一句台词 |
| **CD(持续交付/部署)** | 把验证通过的产物**自动送到**待发布或已发布状态 | CI 管「有没有坏」,CD 管「送不送出去」 |

---

## 一、CI 到底在解决什么

> **为解决什么痛点而生**:多人同时改一份代码,各改各的,谁也不知道对方的改动会不会把自己的搞崩 ——
> 直到某天要发布,才把几周的分支合到一起,冲突与 bug 一起爆发,这种场面叫「集成地狱」。
> **一句话定义**:CI 是**每个成员至少每天一次把自己的改动与同事的改动合到同一条主线**,且**每一次这样的合并都由自动化构建(含测试)验证**,以尽早发现集成错误
> ([Martin Fowler: Continuous Integration](https://martinfowler.com/articles/continuousIntegration.html));
> 维基百科的说法是「频繁集成源码改动,并保证集成后的代码库处于可用状态;通常由自动化系统来构建与测试」
> ([Wikipedia: Continuous integration](https://en.wikipedia.org/wiki/Continuous_integration))。
> **大白话注解**:把「攒到最后一起合」改成「天天合、合完自动验」;谁的改动把主线弄坏了,当场就知道,而不是等两周后。
> Kent Beck 的原话是「**代码不要超过几个小时还没被集成**」—— 这句话里半小时还是两小时无所谓,关键是「频繁」。

Fowler 把这套实践列成了清单,其中三条最能说明它和「跑个测试」的区别:
**Automate the Build**(构建必须自动化)、**Make the Build Self-Testing**(构建自己会判断对错)、
**Fix Broken Builds Immediately**(主线一红立刻修)。还有一条容易被忽略:**Keep the Build Fast** ——
XP 的经验值是**让构建控制在十分钟内**;理由是「每砍掉一分钟构建时间,每个开发者每次提交都省一分钟」。

---

## 二、本机实例:一次真实的 CI 运行记录

本机另一个仓库 `Zzz210s/ai-session-hub` 真的接了 CI。四条真实运行记录,时间倒序
(`gh run list -R Zzz210s/ai-session-hub --limit 5`,2026-09-25 实测):

```text
completed  success  test: 删除相关用例改为平台无关(修 CI 在 Linux 上失败)  test  master  push 35519548484  10s
completed  failure  chore: package.json 关键词补全(CRLF 导致上次未生效)        test  master  push 35519431229  11s
completed  failure  fix: 补入被误忽略的 src/live/(克隆后无法运行)+ 关键词      test  master  push 35519243094   8s
completed  failure  chore: 加入 CI、版本 0.5.0、描述与关键词更新               test  master  push 35519029229  10s
```

这四行就是 CI 的全部意义:**连续三次红,改到第四次绿**。每次 `git push` 之后 8~11 秒,
一个云端机器就重跑了同一套检查并把结论记录下来 —— 人不在场、也不用记得跑。

那个仓库的 workflow(`.github/workflows/test.yml`)一共三件事,每件都是「人本来要手动做的事」:

| 阶段 | 命令 | 手动版本就是 |
| --- | --- | --- |
| 单元测试 | `node --test test/*.test.js` | 自己在本地敲一遍 |
| shell 语法检查 | `bash -n setup.sh` | 自己记得检查一遍脚本语法 |
| 误提交检查 | `grep -rnE` 扫三类正则(家目录路径 / 疑似密钥) | 自己人肉翻自己有没有把家目录路径提交上去 |

它的注释里写着一个诚实的边界:**Windows 专属能力(UIA 标签聚焦、系统回收站、ConPTY)在 CI 里无法覆盖**,
那部分只能靠本机验证。所以 CI 覆盖的是「换台 Linux 机器也能跑的那一半」,不是全部。

---

## 三、CI 就是把手动跑的那条命令自动化

本笔记库自己的检查是**手动跑**的:

```bash
$ cd F:/0-Note/50-资源/工具/vault-check && python -B check_vault.py --quiet; echo rc=$?
[A1 断链] 0 处
... (13 行分类计数)
结论:PASS
rc=0
```

**把这条命令写进 CI,CI 就形成了。** 如果给本库接上 GitHub Actions,最小骨架是这样(逐行讲):

```yaml
name: vault-check                    # 这份剧本的名字,会出现在运行列表里
on:
  push: { branches: [master] }       # 推送到 master 时触发
  pull_request:                      # 提 PR 时也触发
  workflow_dispatch:                 # 允许在网页上手动点一次
jobs:
  check:
    runs-on: ubuntu-latest           # 用一台临时 Linux 机器,跑完就销毁
    steps:
      - uses: actions/checkout@v4    # 第 1 步:把仓库拉下来
      - name: 结构体检                # 第 2 步:跑那条本来就该手动跑的命令
        run: cd 50-资源/工具/vault-check && python -B check_vault.py --quiet
```

三行配置(`on` / `jobs` / `steps`)就抵掉了「记得跑」这件事 —— 这正是 CI 的全部魔法:
**把纪律写成配置,让机器替所有人守**([GitHub 官方: Workflow syntax](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax))。
顺带一个真实约束:本库目前**没有** `.github/workflows/`(2026-09-25 实测),所以这段只是骨架,不是现状。

---

## 四、CI 与相邻词的分界

| 名字 | 它做什么 | 什么时候跑 | 和 CI 的关系 |
| --- | --- | --- | --- |
| **测试夹具(fixture)** | 摆好前提 + 逐条断言,报 `PASS=n FAIL=m` | 被人/被脚本调用时 | CI 里跑的**内容**之一 |
| **linter(markdownlint)** | 检查单篇文本格式 | 提交前 / 写的时候 | 同一类检查,通常也塞进 CI |
| **巡检器(vault-check)** | 检查跨篇结构关系,结论落在退出码 | 手动 `python -B check_vault.py` | 上面那条命令的手动版,可以原样搬进 CI |
| **CI 服务(GitHub Actions)** | 在云端机器上按配置**自动**跑上面那些 | 推送 / 提 PR / 定时 | CI 实践的**载体**,不是 CI 本身 |
| **CD(持续交付/部署)** | 把验证过的产物送到待发布/已发布 | 检查通过之后 | CI 的下一步,常写在同一个 workflow 里 |

一句话:**夹具、linter、巡检器都是「检查」,CI 是「让检查自动发生」的那套规矩与场地**。
Fowler 专门提醒过一个混淆:只在**功能分支**上跑自动构建,那只是「半集成」;
真正的 CI 要求「每个人都往主线推,每次推都触发构建」。

---

## 五、怎么读一次 CI 结果

| 你看到的 | 含义 | 下一步 |
| --- | --- | --- |
| 绿(success) | 那一套检查全过 | 可以合并;但要知道它**没覆盖**什么(如 Windows 专属能力) |
| 红(failure) | 至少一条检查没过 | 立刻看日志,修完重推 —— 「Fix Broken Builds Immediately」 |
| 灰/未跑(skipped/queued) | 被条件跳过,或还在排队 | 别把「没报」当「过了」;和巡检器那条纪律同源 |
| 红在**别人**的提交上 | 主线已坏,谁的改动都可能被误伤 | 先修主线,再谈自己的改动 |
| 只跑了部分阶段 | 配置里漏了 job,或某步被 `if` 跳过 | 核对 workflow 的 `on` 与 `jobs` |

---

## 六、常见误解

| 说法 | 问题在哪 | 更准的说法 |
| --- | --- | --- |
| 「CI 就是跑测试」 | 测试只是其中一步;构建、静态检查、密钥扫描同样在里面 | CI 是「自动验证这次集成」,内容随项目而定 |
| 「有 GitHub Actions 就等于有 CI」 | 只给功能分支跑自动构建 = 半集成 | CI 的核心是「每天往主线合 + 每次合都验证」 |
| 「本地跑过了就不用 CI」 | 别人的机器、别的系统、别人改的文件都会出错 | 本机实测那次真红:CI 在 Linux 上失败,本机看不见 |
| 「CI 配好就不用再管」 | 配置会腐坏:依赖升版、用例写死平台、步骤被跳过 | 绿的流水线也要定期核对它到底跑了什么 |
| 「CI 绿 = 可以发」 | CI 只证明「配置里那些检查过了」 | 发布还要人判断范围、兼容与回滚方案 |

---

## 七、和相邻术语的关系

| 术语 | 一句话定义 | 与 CI 的关系 |
| --- | --- | --- |
| **构建自动化(build automation)** | 把「源码 → 可运行产物」的步骤写成脚本 | CI 的前置条件,没有它就没得自动化 |
| **持续交付(delivery)** | 每时每刻都有一份**随时可发布**的产物 | 建立在 CI 之上:先保证不坏,再保证能发 |
| **持续部署(deployment)** | 验证通过就**自动发布到生产** | 比持续交付更进一步,风险门槛也更高 |
| **冒烟测试(smoke test)** | 只验证「主要功能还能跑起来」的最小集合 | 常作为 CI 的第一道关 |
| **分支保护(branch protection)** | 规定「CI 必须绿才能合并」 | 把 CI 的结论变成**制度**,而不是建议 |

**一句话总结**:CI 这个词指的不是某个工具,而是「**频繁合进主线 + 每次合并都自动验证**」这条规矩;
GitHub Actions / Jenkins 之类只是执行它的场地。判断一个项目有没有 CI,不看它有没有 workflow 文件,
而看它**每次推送是不是真的会被自动检查一遍**。

---

速查卡:[CI 速查](../reference/CI速查.html)(判定表、workflow 三层结构、症状反查、真实运行记录)·
课程:[0008 · CI](../lessons/0008-CI.html) · 对照阅读:[巡检器](<巡检器.md>)
