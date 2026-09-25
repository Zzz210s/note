---
type: tutorial
tags: [开发工具, CI, CD, 持续集成, 持续交付, GitHub Actions, 自动化, Node.js]
status: done
date: 2026-09-21
related: "[[测试夹具是什么]]"
---

# CI/CD 与 GitHub Actions 实战

> 目标:先**用比喻讲透 CI/CD 到底在解决什么**,再**从零给一个 Node.js 项目配上 GitHub Actions 自动化流水线**,最后把 **YAML 语法 / 触发器 / Jobs 与 Steps / 环境变量**这四块细节拆开讲清。
> **本文的固定写法**:每个概念按「**为解决什么痛点而生 / 一句话定义 / 大白话注解**」三段给出,再展开细节。
> 关联阅读:[测试夹具是什么](<../../!名词解释/20-知识/测试夹具是什么.md>)(流水线里跑的"验收清单")、[Node.js,npm,pnpm的作用与关系](<../../!名词解释/20-知识/Node.js,npm,pnpm的作用与关系.md>)(`npm ci` / lockfile)、[CLI,TUI,GUI三种界面的区别](<../../!名词解释/20-知识/CLI,TUI,GUI三种界面的区别.md>)。

---

## 一句话速览

| 名称 | 一句话定义 | 为解决什么痛点而生 |
| --- | --- | --- |
| **CI(持续集成)** | 每次提交都把代码合并进主干,并**自动**跑构建与测试来验证 | 多人各写各的分支,临发布才合并 → "合并地狱"与最后一刻爆炸 |
| **持续交付(CD,Delivery)** | 在 CI 基础上,自动把通过验证的产物**打包成随时可发布**的状态 | 发布要人工打包、手工填一堆参数,流程不可重复 |
| **持续部署(CD,Deployment)** | 在持续交付基础上,**自动**把产物部署到线上,无需人工点确认 | 每次上线都靠人守着点按钮,慢且易错 |
| **流水线(pipeline)** | 一串"拉代码 → 装依赖 → 检查 → 测试 → 打包 → 部署"的自动化阶段 | 这些步骤原本靠人按文档手动敲,漏一步就出事 |
| **Workflow(工作流)** | GitHub Actions 里的一个自动化流程定义(`.github/workflows/*.yml`) | 需要有个地方把"何时触发、做什么"写下来 |
| **Job(作业)** | 工作流里的一段任务,跑在**一台独立机器**上 | 任务要隔离:一个挂了不该影响另一个,还要能并行 |
| **Step(步骤)** | Job 里的一步操作(跑命令 or 调用现成 Action) | 任务要拆成可读、可定位的原子操作 |
| **Action(动作)** | 别人写好、可复用的"一块功能"(如检出代码、装 Node) | 每个仓库都重写一遍检出/缓存逻辑纯属浪费 |
| **Runner(运行器)** | 真正执行 Job 的那台机器(GitHub 托管或自建) | 需要有人提供干净、可随时重建的执行环境 |

---

## 一、概念解析:用比喻讲透 CI 与 CD

### 1.1 先看"没有 CI/CD 的世界"

假设三个人协作写一个项目,传统做法是:

1. 各人在自己的分支上写几天;
2. 发布前,分别往主干合并 —— **冲突集中爆发**,谁也不确定合完还能不能跑;
3. 手工跑测试、手工打包、手工上传服务器;
4. 上线后发现 bug,却说不清"是哪次改动引入的"。

问题不在"人不够勤奋",而在于:**反馈太晚、动作靠人、过程不可复现。**

### 1.2 CI(持续集成)

> **为解决什么痛点而生**:多人各自开发,代码越攒越久才合并 —— 冲突越攒越大、集成问题挤在发布前集中爆发;而且"合完能不能用"没人自动告诉你,只能靠人记得测。
> **一句话定义**:持续集成是**要求开发者频繁地把代码合入主干,并且每次合入都由机器自动完成构建与测试**的工程实践。
> **大白话注解**:别攒着,写完一点就交一点,而且**每次交作业都有人当场批改**,错了立刻知道。

**用做菜来类比**:

| 传统方式 | 持续集成 |
| --- | --- |
| 每个人在家把整道菜做完,端到宴席才拼盘 | 每人只负责一道小菜,**每做好一样就尝一口** |
| 拼盘时才发现咸淡不搭、有人买了同样的菜 | 味道不对当场发现,立刻调整 |
| 靠厨师长记性保证质量 | 有一套**固定口味的品控流程**,自动执行 |

CI 的核心动作只有三步:**拉最新代码 → 装依赖 → 跑检查(构建 + 测试)**。它的价值在于**把反馈时间从"几天"压到"几分钟"**。

三条让 CI 真正生效的前提:

- **提交要小要频繁**(一天多次,而不是一周一次);
- **测试要快**(慢测试跑不完,人就会绕开它);
- **坏了要立刻修**(主干长期是红的,CI 就失去意义)。

### 1.3 CD 之一:持续交付(Delivery)

> **为解决什么痛点而生**:代码验证通过了,但"上线"仍是手工活儿 —— 手动打包、手动传文件、手动改配置。步骤一多必然出错,且"上次是怎么发的"没人能完整复述。
> **一句话定义**:持续交付是**在 CI 通过后,自动把产物打包并准备好随时可发布**,但**最终发布由人决定**的实践。
> **大白话注解**:菜已经装盘、摆好、随时能上桌 —— **但什么时候端出去,还是你说了算**。

### 1.4 CD 之二:持续部署(Deployment)

> **为解决什么痛点而生**:即便打包自动化了,每次上线还要人守着点确认 —— 发布变成"少数人敢做的仪式",频率上不去、节奏跟不上市场。
> **一句话定义**:持续部署是**在持续交付基础上,让通过全部验证的产物自动进入生产环境**,不需要人工确认的实践。
> **大白话注解**:装好盘就**自动端上桌**,不需要谁再说一句"上菜"。
> **两个 CD 只差一步 —— 那一步叫"人工确认"。** 团队先做到持续交付,等测试覆盖率、监控、回滚手段足够硬,再考虑把最后一步也自动化。

### 1.5 三者关系一张图

```text
写代码 ──提交──> [CI] 构建 + 测试 ──通过──> [CD-交付] 打包 + 预备发布
                        │                              │
                     失败就拦下                     ┌────┴────┐
                  （别让坏代码往下走）            人工确认   自动发布
                                              （持续交付） （持续部署）
```

**一句话总结**:CI 管"**合得进、跑得通**",持续交付管"**随时能发**",持续部署管"**自动去发**"。三者是**递进关系**,不是三件互不相干的事。

### 1.6 收益要落到具体数字上

| 维度 | 没有流水线 | 有流水线 |
| --- | --- | --- |
| 发现问题的时机 | 发布前集中爆发(数天~数周) | 提交后几分钟 |
| 回归测试耗时 | 人工点一遍,漏测靠运气 | 机器全跑,时间固定 |
| 发布动作 | 靠文档 + 记忆,步骤易漏 | 一条命令或自动触发 |
| 定位责任变更 | 翻提交记录猜 | 直接指向红掉的那次提交 |
| 新人上手 | 得找人带一遍发布流程 | 流水线就是可执行的流程文档 |

### 1.7 三个常见误区

1. **"跑个测试就叫 CI 了"** —— CI 的前提是**频繁合并**;一天提交一次、一月合并一次,再多的测试也只是"批量验收"。
2. **"CD 就是每次提交都直接上生产"** —— 那是持续部署,而且是团队成熟后的选项;多数团队需要的是持续交付。
3. **"流水线越快越好,所以跳过测试"** —— 跳过之后,流水线就从"安全网"变成"心理安慰";正确做法是**把慢测试分层**(提交跑快的一层,合并/夜间跑全量)。

---

## 二、实战:从零给 Node.js 项目配上 GitHub Actions

### 2.1 认识 GitHub Actions 的骨架

| 概念 | 在文件里的位置 | 说明 |
| --- | --- | --- |
| Workflow | `.github/workflows/<名字>.yml` 一个文件 | 顶层容器 |
| 触发器 | `on:` | 什么事件让它跑 |
| Job | `jobs.<id>:` | 跑在一台独立机器上的任务 |
| Step | `jobs.<id>.steps[]` | Job 内的一步 |
| Action | `steps[].uses:` | 复用别人写好的功能 |

**新手最容易懵的一点**:每个 Job 都是一台**全新的、空的**机器 —— 上一步 Job 拉下来的代码,下一个 Job 里**不存在**;想传文件得用 **artifact**,想传值得用 **outputs**。

### 2.2 前置:示例项目长什么样

```text
my-app/
├─ src/
├─ test/
├─ package.json
├─ package-lock.json
└─ .github/
   └─ workflows/
      └─ ci.yml        <-- 接下来要写的文件
```

`package.json` 里准备好脚本(本地能跑,CI 才能跑):

```json
{
  "scripts": {
    "lint": "eslint .",
    "test": "vitest run",
    "build": "tsc -p tsconfig.json"
  }
}
```

> 关键原则:**CI 只调你本地也在用的同一条命令**。若 CI 里另写一套参数,就变成了两个真相。

### 2.3 第一版:最小可用的 ci.yml

新建 `.github/workflows/ci.yml`:

```yaml
name: CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    name: 构建与测试
    runs-on: ubuntu-latest
    steps:
      - name: 检出代码
        uses: actions/checkout@v4
      - name: 安装 Node.js
        uses: actions/setup-node@v4
        with:
          node-version: 22
      - name: 安装依赖
        run: npm ci
      - name: 代码检查
        run: npm run lint
      - name: 运行测试
        run: npm test
      - name: 构建
        run: npm run build
```

推上去之后:`push` 到 main、或有针对 main 的 PR 时,**GitHub 会自动开一台 Ubuntu 机器**把这几步跑一遍;结果出现在 PR 页面的 **Checks** 区域。

### 2.4 第二版:加缓存,把时间压下来

每次重新下载依赖是最常见的浪费。`setup-node` 自带缓存开关:

```yaml
      - name: 安装 Node.js
        uses: actions/setup-node@v4
        with:
          node-version: 22
          cache: npm
```

缓存键默认按 `package-lock.json` 的哈希计算 —— **锁文件一改,缓存自动失效**,不必手工操心。

**为什么用 `npm ci` 而不是 `npm install`**:

| | `npm install` | `npm ci` |
| --- | --- | --- |
| 依赖来源 | 按 `package.json` 求解,可能更新 lockfile | **严格按 lockfile** 安装 |
| 结果确定性 | 可能装出与本地不同的版本 | 与 lockfile 完全一致 |
| 速度 | 较慢 | 较快(先删 `node_modules`) |
| 适用 | 本地开发(加新包) | **CI 专用**(要求 lockfile 存在) |

> 推理很直白:**CI 的职责是"验证这份代码在锁定的依赖下能不能过",不是"顺便升个版本"**。

### 2.5 第三版:矩阵测试(多 Node 版本 × 多系统)

库要给外部用,就得知道"哪些环境能跑":

```yaml
jobs:
  test:
    runs-on: ${{ matrix.os }}
    strategy:
      fail-fast: false        # 一个组合挂了,别取消其他组合
      matrix:
        os: [ubuntu-latest, windows-latest, macos-latest]
        node: [18, 20, 22]
        exclude:
          - os: macos-latest  # 举例:macOS 上只测最新 Node
            node: 18
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: ${{ matrix.node }}
          cache: npm
      - run: npm ci
      - run: npm test
```

一个 3×3 的矩阵会被展开成多个 Job **并行**跑,`matrix.os` / `matrix.node` 用 `${{ }}` 取值。

### 2.6 第四版:加一个"只在 main 上跑"的部署 Job

```yaml
  deploy:
    name: 部署到生产
    needs: test                       # 等 test 全部通过才跑
    if: github.ref == 'refs/heads/main' && github.event_name == 'push'
    runs-on: ubuntu-latest
    environment: production           # 关联 GitHub 的 Environment(可设人工审批)
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 22
          cache: npm
      - run: npm ci
      - run: npm run build
      - name: 部署
        env:
          DEPLOY_TOKEN: ${{ secrets.DEPLOY_TOKEN }}
        run: ./scripts/deploy.sh
```

三个关键点:

- **`needs: test`** —— Job 之间有顺序;不加就并行,可能"坏代码也部署"。
- **`if:`** —— 只在 main 分支的 push 上部署,PR 不部署。
- **`environment: production`** —— 可在仓库设置里给这个环境配**必须人工批准**,于是"持续交付"与"持续部署"的差别就落在这一个选项上。

### 2.7 第五版:让 Job 之间传文件(artifact)

```yaml
      - name: 上传构建产物
        uses: actions/upload-artifact@v4
        with:
          name: dist
          path: dist/

  smoke:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/download-artifact@v4
        with:
          name: dist
      - run: ls -la dist
```

**注意**:artifact 是用来"在 Job 之间搬运文件"和"留证给人事后下载查看"的,不是部署通道。

### 2.8 第六版:并发控制与超时(容易忽略的稳定性细节)

```yaml
concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true

jobs:
  test:
    runs-on: ubuntu-latest
    timeout-minutes: 15
```

- **`concurrency`**:同一分支连续推两次,取消上一次还在跑的 —— 省额度、也避免旧结果覆盖新结果。
- **`timeout-minutes`**:防止某个步骤卡死把默认 6 小时额度烧光。

### 2.9 看结果与徽章

- PR 页面底部 **Checks**:绿勾/红叉,点进去能看每个 Step 的日志。
- **Actions 标签页**:历史运行记录、重跑、下载 artifact。
- README 加个状态徽章:

```markdown
![CI](https://github.com/<owner>/<repo>/actions/workflows/ci.yml/badge.svg)
```

### 2.10 本地先跑一遍(可选但强烈建议)

用 `act` 可以在本地用 Docker 模拟 GitHub Actions:

```bash
act -j test          # 只跑 test 这个 job
act -l               # 列出会被触发的工作流
```

> 也可退而求其次:**在本地把 CI 里的命令原样敲一遍**。凡是"本地没跑过就推上去试"的调试,都是在用 CI 当编辑器。

---

## 三、细节拆解

### 3.1 YAML 语法速成

YAML 的目标是"人能读的结构化数据",而它在 GitHub Actions 里最常出错的地方只有一个:**缩进**。

| 概念 | 写法 | 说明 |
| --- | --- | --- |
| 键值 | `name: CI` | 冒号后**必须**有空格 |
| 映射(对象) | 缩进比父级深 2 空格 | 表示"属于上一级" |
| 列表 | `- 条目` | 短横线后**必须**有空格 |
| 字符串 | `"双引号"` / `'单引号'` / 裸写 | 含 `:`、`#`、`{}` 时务必加引号 |
| 多行文本 | `\|` 保留换行,`>` 折叠为空格 | 写多行 shell 脚本常用 `\|` |
| 注释 | `# 到行尾` | 只能整行或行尾,不能行中乱插 |
| 布尔与空 | `true` / `false` / `null` | 注意裸写的 `on`、`y`、`no` 在某些解析器里会被当成布尔 |

**三条铁律**:

1. **只用空格,不用 Tab** —— 用 Tab 会直接解析失败。
2. **同级元素缩进必须完全一致** —— 差一个空格就是"层级不同",报错往往指向别处。
3. **别靠肉眼对齐** —— 提交前让编辑器(VS Code 的 YAML 插件)或 `act -l` 校验一次。

多行脚本的两种写法:

```yaml
      - name: 多行命令(保留换行)
        run: |
          npm ci
          npm test

      - name: 折行书写(合成一行)
        run: >
          npm run build &&
          echo 构建完成
```

### 3.2 触发器设置(`on`)

**最常用的四类**:

| 触发器 | 何时跑 | 典型用途 |
| --- | --- | --- |
| `push` | 向分支/标签推送 | 主干验证、打标签发版 |
| `pull_request` | PR 被打开/更新 | 合并前的门禁(最该配的一个) |
| `schedule` | 定时(cron,**UTC 时区**) | 每日回归、依赖安全扫描 |
| `workflow_dispatch` | 手动点按钮触发,可带输入参数 | 手动发布、运维任务 |

**完整示例**:

```yaml
on:
  push:
    branches: [main, 'release/**']      # 分支过滤,支持通配
    tags: ['v*']                         # 只在版本标签上触发
    paths:                               # 只有这些路径变了才跑
      - 'src/**'
      - 'package.json'
      - '.github/workflows/ci.yml'
    paths-ignore:
      - '**/*.md'                        # 纯文档改动不跑测试
  pull_request:
    branches: [main]
    types: [opened, synchronize, reopened]
  schedule:
    - cron: '0 18 * * *'                 # 每天 UTC 18:00(北京 02:00)
  workflow_dispatch:
    inputs:
      environment:
        description: 部署到哪个环境
        required: true
        default: staging
        type: choice
        options: [staging, production]
```

**几个必须记住的点**:

- **`schedule` 用 UTC**,写 cron 时要自己换算时区。
- **`paths` 与 `paths-ignore` 不能同时用**在同一触发器的同一层级。
- **`pull_request` 来自 fork 时拿不到 secrets**(这是安全设计,不是 bug),所以"PR 里部署"这种设计本身就不成立。
- **`workflow_dispatch` 的输入用 `${{ inputs.environment }}` 取**。

### 3.3 Jobs 与 Steps 配置

**Job 级常用键**:

| 键 | 作用 |
| --- | --- |
| `runs-on` | 跑在哪种机器:`ubuntu-latest` / `windows-latest` / `macos-latest` / 自建 |
| `needs` | 依赖哪些 Job 先成功 |
| `if` | 条件不满足就跳过整个 Job |
| `strategy.matrix` | 参数矩阵展开成多个并行 Job |
| `strategy.fail-fast` | 某组合失败时是否取消其他(`false` = 全部跑完) |
| `env` | 该 Job 内所有 Step 可用的环境变量 |
| `outputs` | 暴露给下游 Job 的值 |
| `timeout-minutes` | 超时上限 |
| `continue-on-error` | 失败了也继续(如"允许失败的实验性检查") |
| `environment` | 关联部署环境(可加人工审批与环境保护规则) |
| `permissions` | 该 Job 的 `GITHUB_TOKEN` 权限(最小化原则) |

**Step 级常用键**:

| 键 | 作用 |
| --- | --- |
| `name` | 显示在日志里的名字(**写好它能省掉大量排错时间**) |
| `id` | 供后续用 `steps.<id>.outputs.x` 取值 |
| `uses` | 用现成 Action,如 `actions/checkout@v4` |
| `run` | 执行 shell 命令 |
| `with` | 传给 Action 的参数(如 `node-version`) |
| `env` | 仅该 Step 生效的环境变量 |
| `if` | 条件执行 |
| `shell` | 指定 shell(跨系统时有用,如 `bash`) |
| `working-directory` | 工作目录(monorepo 常见) |
| `continue-on-error` | 该步失败不算整个 Job 失败 |

**进阶但很实用**:

```yaml
      - name: 只有当上一步输出满足条件时才跑
        if: steps.check.outputs.changed == 'true'
        run: echo 有变更

      - name: 无论前面成功失败都跑(清理/上传日志)
        if: always()
        run: ./scripts/cleanup.sh

      - name: 上一步失败时才跑
        if: failure()
        run: ./scripts/report-failure.sh
```

`needs` 与 `if` 一起用,就能表达"**测试全过 且 是 main 分支 且 是 push 事件**"这类门禁。

### 3.4 环境变量的使用

**三个层级(就近者优先)**:`workflow.env` < `job.env` < `step.env`。

```yaml
env:                        # ① 全工作流
  NODE_ENV: test

jobs:
  test:
    env:                    # ② 该 Job 全部 Step
      CI: true
    steps:
      - name: 只这一步生效
        env:                # ③ 只这个 Step
          API_BASE: https://example.test
        run: echo "$API_BASE / $NODE_ENV / $CI"
```

**几种"变量"要分清**:

| 类型 | 取值写法 | 特点 |
| --- | --- | --- |
| 普通环境变量 | `${{ env.NAME }}` 或 shell 的 `$NAME` | 明文,写进文件里,别放敏感值 |
| 密钥 | `${{ secrets.NAME }}` | 仓库/组织/环境级配置,**日志自动打码** |
| 配置变量 | `${{ vars.NAME }}` | 仓库级非敏感配置,可在设置界面改 |
| 上下文 | `${{ github.sha }}` 等 | GitHub 提供的只读信息 |
| 矩阵值 | `${{ matrix.node }}` | 由 `strategy.matrix` 展开 |
| 上游 Job 输出 | `${{ needs.build.outputs.version }}` | 跨 Job 传值 |

**常用内置上下文**:

| 变量 | 含义 |
| --- | --- |
| `github.sha` | 本次运行的提交 SHA |
| `github.ref` / `github.ref_name` | 完整引用 / 短名(如 `main`) |
| `github.event_name` | 触发事件名(`push` / `pull_request` …) |
| `github.repository` | `owner/repo` |
| `github.workspace` | 工作目录 |
| `runner.os` | `Linux` / `Windows` / `macOS` |
| `GITHUB_TOKEN` | 自动注入的临时令牌(权限由 `permissions` 控制) |

**两个高频坑**:

1. **`${{ }}` 是"运行前替换",`$VAR` 是"shell 里读"**。写 `run: echo ${{ env.FOO }}` 会在脚本生成阶段就被替换掉;写 `run: echo $FOO` 才是运行时读取。含敏感值是后者更安全(不会出现在生成的脚本里)。
2. **shell 里 `export` 的变量不会跨 Step 存在**。`run: export FOO=bar` 只对这条命令有效;要让后面的 Step 用到,得写进 `$GITHUB_ENV`:

```yaml
      - name: 设置一个供后续 Step 使用的变量
        run: echo "VERSION=$(node -p "require('./package.json').version")" >> "$GITHUB_ENV"
      - name: 后续 Step 直接可用
        run: echo "版本是 $VERSION"
```

同理,`>> $GITHUB_OUTPUT` 给同 Job 的后续 Step(用 `steps.<id>.outputs`),`>> $GITHUB_PATH` 追加可执行目录。

### 3.5 权限与安全(起码别踩雷)

```yaml
permissions:
  contents: read          # 默认只给读,需要什么再开什么
```

- **最小权限原则**:不写 `permissions` 时,`GITHUB_TOKEN` 的默认权限由仓库设置决定,可能偏大;显式声明更安全。
- **别在日志里打印 secret**:`echo ${{ secrets.X }}` 会被打码,但**拼进 URL/命令里绕过打码**的情况仍可能泄漏 —— 尽量用 `env` 注入而不是内联。
- **`pull_request_target` 很危险**:它以"目标仓库的权限"运行且能读到 secrets,若在其中 `checkout` 了 PR 的代码并执行,等于把钥匙交给陌生人的代码。除非你非常清楚在做什么,否则用 `pull_request`。
- **第三方 Action 固定版本**:`uses: foo/bar@v1` 是标签(可被移动),更严格的做法是固定到 commit SHA;至少不要用 `@master`。
- **部署用 OIDC 代替长期密钥**(云厂商场景):`permissions: id-token: write`,让云平台按身份临时授权,省掉长期 token。

---

## 四、一套可直接抄的完整示例

`.github/workflows/ci.yml`:

```yaml
name: CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

permissions:
  contents: read

concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true

env:
  NODE_ENV: test

jobs:
  test:
    name: 测试(Node ${{ matrix.node }} / ${{ matrix.os }})
    runs-on: ${{ matrix.os }}
    timeout-minutes: 15
    strategy:
      fail-fast: false
      matrix:
        os: [ubuntu-latest]
        node: [18, 20, 22]
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: ${{ matrix.node }}
          cache: npm
      - name: 安装依赖(严格按 lockfile)
        run: npm ci
      - name: 代码检查
        run: npm run lint
      - name: 单元测试
        run: npm test
      - name: 构建
        run: npm run build
      - name: 失败时上传日志
        if: failure()
        uses: actions/upload-artifact@v4
        with:
          name: logs-node${{ matrix.node }}
          path: |
            npm-debug.log*
            coverage/

  deploy:
    name: 部署到生产
    needs: test
    if: github.ref == 'refs/heads/main' && github.event_name == 'push'
    runs-on: ubuntu-latest
    environment: production
    timeout-minutes: 20
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 22
          cache: npm
      - run: npm ci
      - run: npm run build
      - name: 部署
        env:
          DEPLOY_TOKEN: ${{ secrets.DEPLOY_TOKEN }}
        run: ./scripts/deploy.sh
```

---

## 五、排错速查表

| 现象 | 常见原因 | 修法 |
| --- | --- | --- |
| 工作流根本没触发 | `on` 条件不匹配;文件不在 `.github/workflows/`;YAML 语法错 | 看 Actions 页有无该工作流;用编辑器校验;确认分支/路径过滤 |
| `Unexpected value` / 解析失败 | Tab 缩进、同级缩进不一致、`:` 后漏空格 | 全改空格;对齐同级 |
| `npm ci` 报 lockfile 不匹配 | `package.json` 改了但没更新 `package-lock.json` | 本地 `npm install` 后提交 lockfile |
| 找不到某个文件 | 忘了 `actions/checkout`;另一个 Job 里的文件不存在 | 每个 Job 都要 checkout;跨 Job 用 artifact |
| 缓存没生效 | 缓存键变化(lockfile 改动);路径不对 | 检查 lockfile 是否提交;用 `setup-node` 的 `cache: npm` |
| Windows runner 上脚本报错 | 行尾 CRLF;`bash` 特有语法 | 指定 `shell: bash`;用 `.gitattributes` 规范行尾 |
| PR 里 secrets 为空 | fork 的 PR 不注入 secrets(安全设计) | 改为合并后触发,或使用无需 secrets 的检查 |
| 部署 Job 没跑 | `needs` 上游失败;`if` 条件不满足 | 看上游为什么会红;核对 `github.ref` / `github.event_name` |
| 任务卡住跑满 6 小时 | 某步在等输入或死循环 | 加 `timeout-minutes`;检查是否有交互式命令需要加 `--yes` |
| 日志刷屏看不出重点 | Step 没有 `name` | 给每个 Step 起名,便于定位 |

---

## 六、落地建议(按此顺序推进最省力)

1. **先只配一件事**:`pull_request` 触发 + `npm ci` + `npm test`。能跑绿就是胜利。
2. **再加缓存与超时**,把单次时长压到 5 分钟以内(超过 10 分钟,人就开始绕开它)。
3. **再加 lint 与构建**,把"能跑"升级为"能交付"。
4. **再加矩阵**,确定支持的环境边界。
5. **最后才加部署**:先做到"一键可发"(持续交付),等回滚与监控到位,再考虑自动发布(持续部署)。
6. **配 `concurrency`**,避免同分支重复排队烧额度。

> 一句话:**流水线的价值不在"配置得多全",而在"红了一定有人管、绿了真敢发"。**
