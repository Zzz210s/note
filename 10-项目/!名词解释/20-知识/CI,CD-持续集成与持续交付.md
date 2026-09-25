---
type: concept
tags: [开发工具, CI, CD, 持续集成, 持续交付, 持续部署, 自动化, GitHub Actions, 概念辨析]
status: done
date: 2026-09-25
related: "[[巡检器]]"
---

# CI/CD(持续集成与持续交付 / 部署)是什么

> 「在这个 PR 上 CI 挂了」「等 CI 绿了再合并」「CD 那边还没配」—— 这三句话里的 CI 与 CD 到底各指什么?
> 为什么 CI 挂了就没人敢合并,而 CD 又分成两个只差「有没有人按一下」的版本?
> 本文讲清 CI / 持续交付 / 持续部署这三层各自的严格含义、判定口径与前提条件,以及它们和 linter / 测试夹具 / 巡检器的分工。
> **本文的固定写法**:每个概念按「**为解决什么痛点而生 / 一句话定义 / 大白话注解**」三段给出,再展开细节。
> 关联阅读:[巡检器](<巡检器.md>)(同一个「检查」思路的手动版)、
> [CI/CD 与 GitHub Actions 实战](../../!系统与工具/20-知识/CI-CD与GitHub-Actions实战.md)(怎么从零写一个 workflow)。

---

## 一句话速览

| 名称 | 一句话定义 | 大白话注解 |
| --- | --- | --- |
| **CI(持续集成)** | 一种开发实践:每个人**至少每天**把自己改动合进同一条主线,并由**自动化构建(含测试)**验证这次合并 | 不是工具,是「天天合、合完自动验」的规矩 |
| **持续交付(CD, delivery)** | CI 通过后**自动**把产物打包成「随时可发布」的状态,但**上线与否由人决定** | 车随时能开,钥匙还在人手上 |
| **持续部署(CD, deployment)** | 在持续交付之上,验证通过的产物**自动进入生产**,没有人工确认 | 钥匙也交给机器,过了就发 |
| **CD 这个缩写** | 同时是 continuous **delivery** 与 continuous **deployment** | 看到 CD 先问一句:是哪个 D? |
| **流水线(pipeline)** | 把构建与检查串成有先后的一串阶段 | 排队过关:先语法、再单测、最后检查密钥 |
| **workflow / job / step** | GitHub Actions 里的三层容器:一个 workflow 有多个 job,一个 job 有多个 step | workflow = 一份剧本,job = 一幕,step = 一句台词 |

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

## 二、CD 的两个意思:交付(delivery)与部署(deployment)

> **为解决什么痛点而生**:CI 让「代码有没有坏」当场有答案,但「发出去」这件事仍靠人:手工打包、手工填参数、手工传服务器、半夜守着点按钮。
> 结果是流程不可复现(每次发的步骤都不一样)、发版变成一件需要挑日子的事。
> **一句话定义**:持续交付是**在 CI 通过后自动把产物打包并准备好随时可发布**,而**最终发布由人决定**
> ([Fowler: Continuous Delivery](https://martinfowler.com/bliki/ContinuousDelivery.html));
> 持续部署是**在持续交付之上,让通过全部验证的产物自动进入生产环境**,不需要人工确认
> ([Wikipedia: Continuous deployment](https://en.wikipedia.org/wiki/Continuous_deployment))。
> **大白话注解**:两个 CD 只差**一步**,那一步叫「人工确认」—— 交付是「车随时能开,钥匙在人手上」,
> 部署是「钥匙也交给机器」。团队通常先做到交付,等测试覆盖、监控、回滚都够硬,再考虑把最后一步也自动化。

### 判定表:看到这个,就是这个结论

| 你观察到的现象 | 结论 | 判据 |
| --- | --- | --- |
| 只跑构建与测试,没有任何发布动作 | 只有 CI | 流水线到「检查」就结束了 |
| 自动打出可发布产物(包 / 镜像 / 站点目录),但没人接着发 | 做到了交付的前半 | 有产物、没有部署步骤 |
| 产物就绪后,要人去网页/终端点一下「发布」才上线 | **持续交付** | 那一下点击就是 delivery 与 deployment 的分界 |
| 提交通过后几分钟内,线上自动换成了新版本 | **持续部署** | 没有人工确认这一环 |
| 上线是自动的,但只自动到预发环境 | 持续交付(到 staging) | 生产那一跳还留着人 |

### 持续部署的前提条件(缺一条,自动上线就只是自动出事)

| 前提 | 为什么必须有 |
| --- | --- |
| **CI 本身可靠** | 检查拦不住问题,自动上线就是把问题自动送进生产 |
| **可一键回滚** | 自动发得出去,也要能自动收回来;否则一次坏版本就是一次事故 |
| **特性开关(feature flag)** | 代码先上线、功能后开,把「部署」与「发布」拆成两件事 |
| **监控与告警** | 自动上线的前提是能自动发现「上线之后坏了」 |
| **数据库迁移可前后兼容** | 新旧两个版本会同时存在几分钟,迁移不能只朝一个方向走 |

Fowler 在 [ContinuousDelivery](https://martinfowler.com/bliki/ContinuousDelivery.html) 里给的定义也是这个次序:
先把「每次改动都能安全地进生产」做成一条**可重复的流水线**,再谈自动化到哪一步;
两个 CD 的差别不在技术难度,而在**团队对失败的处理能力**。

---

## 三、本机实例:一次真实的 CI 运行记录

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
注意 workflow 那一列叫 `test`:这几条记录**全是检查,没有一步是部署** —— 有 CI 不等于有 CD;
本机另有真在跑的 CD 仓库(下一节),和这个仓库正好对照。

那个仓库的 workflow(`.github/workflows/test.yml`)一共三件事,每件都是「人本来要手动做的事」:

| 阶段 | 命令 | 手动版本就是 |
| --- | --- | --- |
| 单元测试 | `node --test test/*.test.js` | 自己在本地敲一遍 |
| shell 语法检查 | `bash -n setup.sh` | 自己记得检查一遍脚本语法 |
| 误提交检查 | `grep -rnE` 扫三类正则(家目录路径 / 疑似密钥) | 自己人肉翻自己有没有把家目录路径提交上去 |

它的注释里写着一个诚实的边界:**Windows 专属能力(UIA 标签聚焦、系统回收站、ConPTY)在 CI 里无法覆盖**,
那部分只能靠本机验证。所以 CI 覆盖的是「换台 Linux 机器也能跑的那一半」,不是全部。

---

## 四、CD 的出口在本机:两个真在跑的仓库 + 部署 CLI

CI 的出口是「网页上一行绿或红」,CD 的出口是「线上多了一个新版本」。本机**有接 CD 的仓库** ——
2026-09-25 逐仓读原文件、并用 `gh run list` 核对过运行记录(仓库与 workflow 数按
`git ls-files '.github/workflows/*'` 数,`F:/0-code` 下):

| 仓库 | 自己写的 workflow | 性质 |
| --- | --- | --- |
| `Zzz210s/personal-content` | `trigger-site.yml`(全文 14 行) | **持续部署**:push `main` → 打 Cloudflare Pages deploy hook → 站点自动重建上线 |
| `Zzz210s/GoodNight` | `ci.yml`(68 行) | **持续交付到发布**:PR/push 跑测试;打 `v*` tag → 构建 APK 并自动发 Release(`draft: false`) |
| `Zzz210s/personal-site` | `ci.yml` | 只检查:typecheck / test / lint / build / 站内死链 |
| `Zzz210s/ai-session-hub` | `test.yml` | 只检查:上一节那三件事 |
| `Zzz210s/west`(fork) | 8 个 | 上游 `zephyrproject-rtos/west` 原样 |
| `Zzz210s/zephyr`(fork) | 41 个 | 上游 `zephyrproject-rtos/zephyr` 原样 |

### 真 CD 长什么样:一条 `curl` 就是差距那一步

`personal-content/.github/workflows/trigger-site.yml` 全文只有 14 行,有效逻辑就一条(原文逐字):

```yaml
name: trigger-site

on:
  push:
    branches: [main]

jobs:
  trigger:
    runs-on: ubuntu-latest
    steps:
      - name: Call Cloudflare Pages deploy hook
        run: curl --fail --silent --show-error -X POST "$CF_DEPLOY_HOOK_URL"
        env:
          CF_DEPLOY_HOOK_URL: ${{ secrets.CF_DEPLOY_HOOK_URL }}
```

push 到 `main` 就 `curl` 打一下 Cloudflare Pages 的 **deploy hook**,站点自动重建并上线,**没有人按确认** ——
这就是**持续部署**。它还纠正一个直觉:**CD 的出口不必是 `vercel` / `wrangler` 这类部署 CLI**;
云平台给的 hook(一个只含令牌的 URL,POST 一下就触发构建)同样是 CD 的出口,而且更省事。
运行记录也对得上(`gh run list -R Zzz210s/personal-content --limit 3`,2026-09-25):

```text
completed  success  content: 修正双系统项目桌面环境与两处措辞  trigger-site  main  push 36140570122  7s
completed  success  fix: 修正项目文案的事实错误与合并日期      trigger-site  main  push 36139718266  8s
completed  success  content: 补 16 个项目条目、外部平台链接与上游贡献  trigger-site  main  push 36138218400  8s
```

### 持续交付长什么样:人工只剩「打 tag 那一下」

`GoodNight/.github/workflows/ci.yml`(68 行)用 `on` 与 `if` 把两种触发分开:PR / 普通 push 只跑回归,打 `v*` tag 才构建并发布。
下为节选,行内 `← 注` 为本文所加、`(……略)` 为省略处:

```yaml
on:
  pull_request:
  push:
    branches: [main]
    tags: ['v*']
permissions:
  contents: write                    # ← 注:建 Release 需要写权限,默认 token 只读会 403
jobs:
  test:                              # 回归门禁
    runs-on: ubuntu-latest
    if: ${{ !startsWith(github.ref, 'refs/tags/') }}
    steps:
      - uses: actions/checkout@v4
      - run: ./gradlew test
  release:                           # 打 v* tag 触发
    runs-on: ubuntu-latest
    if: startsWith(github.ref, 'refs/tags/')
    steps:
      # (setup-java / setup-gradle / 签名配置 / APK 改名等步骤此处略)
      - run: ./gradlew assembleRelease
      - name: Publish to GitHub Release
        uses: softprops/action-gh-release@v2
        with:
          name: ${{ github.ref_name }}
          files: GoodNight-*.apk
          generate_release_notes: true
          draft: false
```

打 `v*` tag 之后:构建 → 签名 → 发布 GitHub Release,全程无人再确认;人工动作只有**建那个 tag**。
那一下正是 delivery 与 deployment 的分界 —— 它留在人手上,所以这是**持续交付**的落地形态,
而不是「检查一绿就自动上生产」的持续部署。实测 `v2.2.0` 的 tag 运行 3m41s,随后 `gh release list` 里就出现 `v2.2.0`。
两个仓库对照着读,差别一句话:**`personal-content` 连「那一下」都没有;`GoodNight` 把「那一下」留给打 tag。**

### 手动版仍在:部署 CLI

本机还装着两个部署 CLI(实测),它们是「持续部署」那一步的**手动版**:人敲 `vercel deploy` 或 `wrangler deploy`,
产物才会上线;把它们写进 workflow 的部署 job,那一步就从「人敲」变成「CI 通过后自动敲」:

```bash
$ npm ls -g --depth=0 | grep -E "vercel|wrangler"
├── vercel@59.26.0
└── wrangler@4.138.0
```

本库 `10-项目/2027-掌握边缘函数原理/` 的课程地图里,第 5 节正是「动手:部署你的第一个边缘函数」——
它就是亲手写那一步的学习出口(见 [课程地图](../../2027-掌握边缘函数原理/reference/课程地图.html))。

### 本库自己呢

`Zzz210s/note`(本库)2026-09-25 实测尚无 `.github/workflows/`:结构体检(vault-check)仍靠手动跑,
「搬进 CI」的骨架就是 `on` + `jobs` + `steps` 三层各一行(逐行注见速查卡)。

---

## 五、CI / 交付 / 部署与相邻词的分界

| 名字 | 它做什么 | 什么时候跑 | 和 CI/CD 的关系 |
| --- | --- | --- | --- |
| **[测试夹具(fixture)](<测试夹具是什么.md>)** | 摆好前提 + 逐条断言,报 `PASS=n FAIL=m` | 被人/被脚本调用时 | 流水线里跑的**内容**之一 |
| **linter(markdownlint)** | 检查单篇文本格式 | 提交前 / 写的时候 | 同一类检查,通常也塞进 CI |
| **巡检器(vault-check)** | 检查跨篇结构关系,结论落在退出码 | 手动 `python -B check_vault.py` | 上面那条命令的手动版,可以原样搬进 CI |
| **CI 服务(GitHub Actions)** | 在云端机器上按配置**自动**跑上面那些 | 推送 / 提 PR / 定时 | CI 实践的**载体**,不是 CI 本身 |
| **部署工具(vercel / wrangler)** | 把产物送上目标平台 | 人敲,或被 workflow 调用 | CD 那一步的手动版 |
| **云平台 deploy hook(Cloudflare Pages / Vercel)** | 一个只含令牌的 URL,POST 一下就触发平台重新构建上线 | 被 workflow 里的 `curl` 调用 | CD 的另一种出口,省掉部署 CLI 与本地凭据 |

一句话:**夹具、linter、巡检器都是「检查」,CI 是「让检查自动发生」,CD 是「让发布自动发生」**。
Fowler 专门提醒过一个混淆:只在**功能分支**上跑自动构建,那只是「半集成」;
真正的 CI 要求「每个人都往主线推,每次推都触发构建」。

---

## 六、怎么读一次 CI/CD 结果

| 你看到的 | 含义 | 下一步 |
| --- | --- | --- |
| 绿(success) | 那一套检查全过 | 可以合并;但要知道它**没覆盖**什么(如 Windows 专属能力) |
| 红(failure) | 至少一条检查没过 | 立刻看日志,修完重推 —— 「Fix Broken Builds Immediately」 |
| 灰/未跑(skipped/queued) | 被条件跳过,或还在排队 | 别把「没报」当「过了」;和巡检器那条纪律同源 |
| 红在**别人**的提交上 | 主线已坏,谁的改动都可能被误伤 | 先修主线,再谈自己的改动 |
| 绿了但线上还是旧版本 | 流水线停在**交付**,没走到部署 | 正常现象;看是否有部署 job 或人工确认那一环 |
| 上线是自动的,但只到预发 | 部署到了 staging,生产那一跳仍留着人 | 这就是「持续交付」的常见落地形态 |

---

## 七、常见误解

| 说法 | 问题在哪 | 更准的说法 |
| --- | --- | --- |
| 「CI 就是跑测试」 | 测试只是其中一步;构建、静态检查、密钥扫描同样在里面 | CI 是「自动验证这次集成」,内容随项目而定 |
| 「有 GitHub Actions 就等于有 CI」 | 只给功能分支跑自动构建 = 半集成 | CI 的核心是「每天往主线合 + 每次合都验证」 |
| 「CD 就是每次提交都直接上生产」 | 那是**持续部署**,而且是团队成熟后的选项 | 多数团队先要的是持续交付:随时能发,发不发人说了算 |
| 「CI 配好就不用再管」 | 配置会腐坏:依赖升版、用例写死平台、步骤被跳过 | 绿的流水线也要定期核对它到底跑了什么 |
| 「CI 绿 = 可以发」 | CI 只证明「配置里那些检查过了」 | 能不能发还要看回滚、监控、迁移这些前提 |

---

## 八、和相邻术语的关系

| 术语 | 一句话定义 | 与 CI/CD 的关系 |
| --- | --- | --- |
| **构建自动化(build automation)** | 把「源码 → 可运行产物」的步骤写成脚本 | CI 与 CD 的共同前置条件,没有它两边都无从自动化 |
| **冒烟测试(smoke test)** | 只验证「主要功能还能跑起来」的最小集合 | 常作为流水线的第一道关 |
| **分支保护(branch protection)** | 规定「CI 必须绿才能合并」 | 把 CI 的结论变成**制度**,而不是建议 |
| **特性开关(feature flag)** | 让功能在代码已上线的情况下仍可关掉 | 持续部署的常见护具:把「部署」与「发布」拆开 |
| **金丝雀发布(canary)** | 先给一小部分用户上新版本,看指标再放量 | 持续部署之后的放量手段,和自动上线配套 |

**一句话总结**:CI 管「**合得进、跑得通**」,持续交付管「**随时能发**」,持续部署管「**自动去发**」。
三者是**递进关系**,不是三件互不相干的事;判断一个项目走到哪一层,不看它有没有 workflow 文件,
而看它**每次推送之后,自动发生的事到哪一步为止**。

---

速查卡:[CI/CD 速查](../reference/CI,CD速查.html)(三层判定表、前提条件、workflow 三层结构、真实运行记录)·
课程:[0008 · CI/CD](../lessons/0008-CI,CD.html) · 对照阅读:[巡检器](<巡检器.md>)
