---
type: note
tags: [Zephyr, CI, west, 开源, 嵌入式]
date: 2026-09-22
status: done
related: "[[2026Q4-参与Zephyr开源社区/!项目说明|!项目说明]] / [[00-环境与流程]] / [[提交清单]]"
---

# Zephyr CI 与 west PR #1006:全貌讲解

> **这份文档给谁看**:想快速建立"Zephyr 的 CI 是怎么回事"与"west 那个 PR 到底在改什么"两件事全貌的人(首先是我自己,其次是面试官可能问到的技术叙述)。
>
> **两种读法并存**:每节先给**科学定义**(可核对、可引用的严谨表述),再给**白话**(类比与直觉)。只想快速懂就看白话,要写进材料或答问就引科学定义。
>
> **数据时点**:2026-09-22。所有数字与文件清单都是当天用 `gh` 实测,来源与复现命令见第 7 节。

---

## 0. 一页速览

| 对象 | 一句话 | 规模(实测) | 我在这条链上的位置 |
|------|--------|------------|-------------------|
| **Zephyr RTOS** | 可缩放的实时操作系统,给资源受限的微控制器用 | 16,582 star / 10,022 fork / 4,612 贡献者 / 4,025 个未关闭 issue+PR / 仓库约 962 MB | 目标是长期贡献者 |
| **Zephyr CI** | 41 个 GitHub Actions workflow + 仓内 `scripts/ci` + 独立 `ci-tools` + twister 测试运行器组成的质量门禁体系 | 每个 PR 触发约 19 项检查 | PR #119887 走完全流程:合规 1 次失败后转 success |
| **west** | Zephyr 的多仓库管理 + 构建封装 + 扩展命令工具 | 366 star / 162 fork / 41 贡献者 / 74 个未关闭 issue | PR #1006(重构 `manifest.py`) |
| **PR #1006** | 把"west 扩展命令列表"与它依赖的"命令来自哪个 manifest 目录"合并成一个类 | 3 文件 +177/-62;测试 350 → 359 passed | 作者,已提交待 review |

---

## 1. 先看全局:三个仓库、两种角色

### 1.1 三个仓库的关系

```text
        ┌─────────────────────────── Zephyr RTOS(主仓,zephyrproject-rtos/zephyr)───────────────────────────┐
        │  内核 + 子系统 + 驱动 + 板级定义 + 文档 + 仓内 CI 脚本(scripts/ci/)+ 测试用例(tests/、samples/)     │
        └───────────────▲──────────────────────────────────┬───────────────────────────────────────────────────┘
                        │ 用 west 拉取工作区                │ 用 twister 跑测试
        ┌───────────────┴──────────────┐        ┌───────────▼──────────────────────┐
        │  west(zephyrproject-rtos/west)│        │  ci-tools(zephyrproject-rtos/     │
        │  多仓管理、构建封装、扩展命令  │        │  ci-tools):合规检查与 lint 规则   │
        └───────────────────────────────┘        │  check_compliance.py / gitlint    │
                                                 └───────────────────────────────────┘
```

**科学定义**:三者是"工具链—主体—质量规则"的分工。west 负责把几十个 Git 仓库组装成一个可构建的工作区;Zephyr 主仓是被组装的主体(同时也是 CI 的执行现场);`ci-tools` 是独立仓库,存放**跨仓库复用的合规检查脚本与提交信息规则**,由主仓的 CI 调用。

**白话**:把 Zephyr 想成一家汽车厂。**west** 是"物料调度系统"(按清单把几百个零件仓配到一起);**主仓**是整车与总装线;**ci-tools** 是"质检标准手册"(写死了螺丝必须拧几圈、单据怎么填)。任何人的改动都要过这套质检线才能进厂。

### 1.2 科学定义 vs 白话:一句话对照

| 概念 | 科学定义 | 白话 |
|------|----------|------|
| CI(持续集成) | 每次代码变更自动触发构建、测试与静态检查,并把结果作为合并前置条件 | 交作业前的自动批改机:不但判分,还拒绝收录不合格的作业 |
| 门禁(Gate) | 未通过必需检查的 PR 无法合并 | 门没开就是进不去,和人情无关 |
| 工作区(workspace) | 由一份 manifest 描述的多仓库目录结构 | 一张物料清单 + 按清单摆好的货架 |
| 测试运行器(twister) | 扫描测试用例、为每个用例生成 build/run 任务、按平台矩阵并行执行并汇总状态 | 自动化抽检机器人:把每个零件按多种工况试一遍 |
| 提交信息合规 | 提交标题/正文/签署行必须满足项目规则,由 gitlint 等工具校验 | 单据格式检查:抬头、编号、签字一个都不能少 |

---

## 2. Zephyr 项目

### 2.1 科学定义

Zephyr 是一个**可缩放的实时操作系统(RTOS)**,面向资源受限设备,采用 Apache-2.0 许可,由 Linux Foundation 旗下的 Zephyr Project 治理。其特征:

- **多架构**:ARM Cortex-M/R/A、RISC-V、x86、ARC、Xtensa、MIPS 等;
- **可配置性**:以 **Kconfig** 做编译期功能裁剪,以 **devicetree** 描述硬件拓扑;
- **许可与治理**:宽松许可 + 开放治理,厂商(Intel、Nordic、NXP、Espressif、Renesas 等)作为成员参与;
- **工具链**:官方提供 Zephyr SDK,构建系统基于 **CMake** + **Ninja**,多仓管理用 **west**;
- **测试**:单元测试框架 ztest + 测试运行器 **twister**。

**规模(2026-09-22 实测)**:16,582 star、10,022 fork、约 4,612 贡献者、4,025 个未关闭 issue/PR、仓库体积约 962 MB、默认分支 `main`。

### 2.2 白话

一堆不同厂家的单片机(芯片),每家都有自家的 SDK、编译方式、寄存器手册。Zephyr 做的事是:**把"操作系统"这件事抽出来做一遍,然后通过配置系统适配到各家的板子上**。厂商不再需要重复造操作系统,应用开发者也不再需要为换一颗芯片而重写项目。

代价是:它必须支持极多的板子与配置组合,所以**测试矩阵极大**——这也是它 CI 复杂、贡献门槛看似高的根本原因。

### 2.3 技术栈

| 组件 | 作用 | 为什么存在 |
|------|------|-----------|
| west | 多仓管理、构建封装、扩展命令 | 一个 Zephyr 工作区由几十个仓库组成,裸 git 无法管理 |
| CMake + Ninja | 构建系统 | 交叉编译需要灵活的目标/工具链配置 |
| Kconfig | 编译期配置 | 同一份代码要适配成百上千种功能组合 |
| devicetree | 硬件描述 | 把"板子长什么样"从代码里剥离成数据 |
| Zephyr SDK | 预编译交叉工具链 | 让开发者不必自建工具链 |
| ztest | 单元测试框架 | 嵌入式也要能做单元测试 |
| twister | 测试运行器 | 在平台矩阵上批量构建与运行,并产出报告 |
| ci-tools | 合规与 lint 规则 | 多仓库共用一套规则,避免各处复制 |

### 2.4 应用场景

- **消费电子与 IoT**:可穿戴、智能家居、传感器节点、连接模组;
- **工业与基础设施**:工业控制、电力、医疗设备(对确定性实时性有要求);
- **车规与边缘**:部分场景下与 Linux、其他 RTOS 混布;
- **教学与竞赛**:板卡生态成熟,入门成本低。

对求职方向的意义:嵌入式/IoT 是出海硬件公司的核心栈,而 Zephyr 是这些公司招人时真正写在 JD 里的 RTOS 之一(Nordic、NXP、Espressif 都是成员,模组厂生态大量使用)。

### 2.5 术语

| 术语 | 含义 |
|------|------|
| board | 一块具体的开发板/硬件目标(如 `nrf52840dk/nrf52840`) |
| SoC / arch | 芯片与架构,决定可用外设与指令集 |
| test / sample | `tests/` 下是测试用例,`samples/` 下是示例程序 |
| testcase.yaml / sample.yaml | 声明该用例支持哪些平台、需要什么硬件、如何判定通过 |
| harness | 测试的判定方式(如 ztest、pytest、console、bsim) |
| build_only | 只构建不运行(例如缺硬件) |
| manifest | 描述工作区由哪些仓库、什么版本组成的那份 YAML |
| module | Zephyr 语境下的"外挂仓库",对 west 来说就是普通 project |

---

## 3. Zephyr CI

### 3.1 科学定义

Zephyr CI 是**基于 GitHub Actions 的分层质量门禁体系**,由四部分构成:

1. **触发与编排层**:`.github/workflows/` 下的 41 个 workflow 文件(实测),按事件(pull_request / push / schedule)触发;
2. **规则层**:仓内 `scripts/ci/`(check_compliance.py、guideline_check.py、test_plan.py、twister_report_analyzer.py 等)+ 独立仓库 `ci-tools`(check_compliance.py、gitlint 规则、build-docs.sh);
3. **执行层**:twister 测试运行器在平台矩阵上构建/运行用例,文档构建用 Sphinx(+ doxygen),安全扫描用 CodeQL 与 Scancode;
4. **汇总与反馈层**:每个 job 把结果回写为 check run(PR 页面上的绿色勾/红色叉),并用 `--annotate` 把违规生成可点击的行内注释。

**前置条件**:所有必需检查通过才允许合并(`Prevent Merging`、`ready-to-merge.yml` 等负责强制)。

### 3.2 白话

把它想成**进厂质检线**:

- 先查**单据**(提交信息、签署、PR 元数据)——单据不合格,后面都不用看;
- 再查**装配能不能跑通**(twister 构建大量测试与示例到各种板子);
- 再查**产品说明书**(文档构建,PR 里改了文档就会触发;没改就跳过);
- 再查**有没有夹带危险品**(CodeQL、Scancode、许可证检查);
- 最后**打包归档**(测试结果、覆盖率、报告)。

每一项都是"机检",不看态度只看规则。所以第一次贡献者的典型体验是:先被单据格式拦下来一次,改完再进真正的技术评审。

### 3.3 架构:四层(实测自具体 workflow 文件)

| 层 | 载体 | 例子 | 谁在跑 |
|----|------|------|--------|
| 触发/编排 | `.github/workflows/*.yml` | `compliance.yml`、`twister.yaml`、`doc-build.yml` | GitHub 托管 runner(ubuntu-24.04 等) |
| 规则 | `scripts/ci/*`、`ci-tools/scripts/*`、`ci-tools/.gitlint` | `check_compliance.py`、`zephyr_commit_rules.py` | 在 runner 内以 Python/Node 执行 |
| 执行 | twister、Sphinx、doxygen、CodeQL、Scancode、Zephyr SDK | `twister -T tests --platform ...` | 容器内并行矩阵 |
| 汇总 | check runs、PR 注释、artifact、ES 上传 | `upload-results`、`Publish Unit Tests Results` | Actions 平台 |

关键设计:**规则与执行分离**——规则放在独立仓(`ci-tools`)可被多个仓库复用;检查结果通过 **annotations** 直接落到 PR 的 diff 行上,而不是让人去翻日志。

### 3.4 41 个 workflow,按用途分类

(依据仓内 `.github/workflows/` 实测清单分类)

| 类别 | workflow 文件 | 白话 |
|------|---------------|------|
| **提交与礼貌性合规** | `compliance.yml`、`dco.yml`、`pr_metadata_check.yml`、`greet_first_time_contributor.yml`、`assigner.yml` | 单据检查、签字检查、首次贡献者欢迎与自动指派人 |
| **编码规范** | `coding_guidelines.yml`、`coding_guidelines_full.yml`、`devicetree_checks.yml`、`errno.yml`、`doxygen-checks.yml`、`license_check.yml`、`pylib_tests.yml`、`scripts_tests.yml` | 代码风格、命名、设备树绑定、文档注释、脚本自测 |
| **构建与测试(核心)** | `twister.yaml`、`twister_tests.yml`、`twister_tests_blackbox.yml`、`twister-publish.yaml`、`bsim-tests.yaml`、`bsim-tests-publish.yaml`、`sanitizers.yml`、`gcc-analyzer.yml`、`codecov.yaml`、`footprint-tracking.yml`、`hello_world_multiplatform.yaml` | 大规模构建/运行、二进制仿真、内存与静态分析、体积回归 |
| **文档** | `doc-build.yml`、`doc-publish.yml`、`doc-publish-pr.yml` | 文档能否构建、能否预览、发布 |
| **安全与供应链** | `codeql.yml`、`scorecards.yml`、`pinned-gh-actions.yml`、`dependency-review`(west 侧) | 静态安全扫描、供应链评级、锁定 Action 版本 |
| **发布与分支管理** | `release.yml`、`backport.yml`、`backport_issue_check.yml`、`manifest.yml`、`push_artifacts.yml`、`stats_merged_prs.yml` | 版本发布、向维护分支回移、清单校验、统计 |
| **仓库卫生** | `stale_issue.yml`、`stale-workflow-queue-cleanup.yml`、`ready-to-merge.yml` | 清理陈旧 issue、清理卡住的流水线、合并前门禁 |
| **其他** | `daily_test_version.yml`、`west_cmds.yml` | 每日版本化测试、west 命令测试 |

### 3.5 一次 PR 的完整旅程(实例:我的 #119887)

这是一个**只改了一个文档文件**的 PR(`doc/develop/west/workspaces.rst`,+58 行),实测触发了 **19 项检查**:

| # | 检查项 | 结果 | 备注 |
|---|--------|------|------|
| 1 | Pull Request/Issue Assignment | success | 自动指派评审人 |
| 2 | Manifest | success | `pull_request_target` 类,无需批准即跑 |
| 3 | **Run compliance checks on patch series (PR)** | **先 failure,修后 success** | 首轮 UC2/UC4 失败 |
| 4 | Check DCO sign-off | success(修后) | 首轮被合规一并拦下 |
| 5 | Run coding guidelines checks | success | 代码规范 |
| 6 | Scan code for licenses | success | 许可证扫描 |
| 7 | Analyze (actions) / (javascript-typescript) / (python) | success | CodeQL 三语言 |
| 8 | CodeQL | success | 汇总 |
| 9 | Check for doc changes | success | 判定是否触发文档构建 |
| 10 | Documentation Build (HTML) | 最后仍在跑 | 文档实际构建 |
| 11 | Documentation Build (PDF) | skipped | 按设计跳过 |
| 12 | Documentation Build Status | success | 汇总 |
| 13 | twister-build-prep / twister-build | skipped | 纯文档改动不动固件,被条件跳过 |
| 14 | Check Twister Status / all jobs passed | success | twister 汇总 |
| 15 | Publish Unit Tests Results | skipped | 同上 |
| 16 | Prevent Merging | success | 门禁本身 |

**关键观察**:CI 是**条件化**的。一个纯文档 PR 不会去跑 twister 全平台构建(那是给代码改动准备的),但**合规、DCO、许可证、CodeQL、文档构建**一样都不少。这解释了为什么"改一行文档"的 PR 也会触发近 20 项检查。

**首次贡献者门槛**:新账号的 push 会让大部分 workflow 停在 `action_required`(需要维护者点批准才运行),这是防滥用机制。批准后才会看到 `Compliance Checks`、`Documentation Build` 等真正跑起来。

### 3.6 每个关卡细讲

| 关卡 | 科学定义 | 白话 | 常见失败原因 | 本地自检 |
|------|----------|------|--------------|----------|
| Compliance Checks | 在 PR 的提交区间上跑 `scripts/ci/check_compliance.py --annotate -c origin/<base>..` | 单据与规范的总检 | 提交信息格式、签署、代码风格、Kconfig 拼写等 | `./scripts/ci/check_compliance.py -c origin/main..` |
| DCO Check | 校验每个提交有 `Signed-off-by`,且形如 `First Last <email>`、与作者一致 | 签字画押:声明"这是我能合法提交的代码" | 忘签名、单字昵称、签署邮箱与提交邮箱不一致 | 自写脚本复刻(见下) |
| Coding Guidelines | 按项目编码规范检查改动 | 公司着装规定 | 命名、缩进、注释风格 | `./scripts/ci/guideline_check.py` |
| PR Metadata Check | 检查 PR 标题/描述/关联 issue | 表格必填项 | 描述缺失、未关联 issue | 人工看一遍 PR 描述 |
| Documentation Build | Sphinx 构建文档(含 doxygen 与交叉引用校验) | 说明书排版校样 | 未定义引用、语法错误、缺图片 | 见 3.9 的文档构建命令 |
| CodeQL | GitHub 的语义级静态安全扫描 | 危险品安检机 | 新引入的可疑数据流(主要对代码) | 由 Actions 执行,本地一般不做 |
| Scancode(license_check) | 扫描许可证合规 | 原料来源核查 | 引入不明许可文件 | 由 Actions 执行 |
| Twister | 在平台矩阵上构建并(尽量)运行测试 | 抽检机器人 | 编译失败、平台回归、超时 | 本地跑 twister(见 3.7/3.9) |
| Backport | 判定是否需要回移到维护分支 | 老版本要不要同步打补丁 | 缺少 `backport` 标签或缺 cherry-pick 检查结果 | 提交时声明 backport 需求 |
| Assigner / Greet | 自动指派与欢迎 | 前台引导 | 无(纯自动化) | 无 |

**DCO 与合规的规则差异(实测对比)**:

| | Zephyr 主仓 | west 仓 |
|---|---|---|
| 用的工具 | `ci-tools/scripts/gitlint/zephyr_commit_rules.py` + `scripts/ci/check_compliance.py` | `zephyrproject-rtos/action-dco` |
| 签署要求 | **两词全名** + 邮箱;标题格式、正文行长也查 | 只要求 `First Last <email>` 且与作者一致 |
| 实测后果 | `ChenChen` 被判失败,必须写成 `Chen Chen` | `ChenChen` 能过,但为统一仍改 |

### 3.7 twister 专章

**科学定义**:twister 是 Zephyr 的**测试运行器**,位于主仓 `scripts/twister`,文档在 `doc/develop/twister/`。它扫描仓库中的测试应用,为每个用例生成构建/运行任务;默认在板级定义中被标为 `default` 的板子上构建,并在有仿真环境的架构上运行(如 qemu、`native_sim`)。它产出 `twister.json` 等报告,并给每个用例一个状态(见 `twister_statuses.rst`)。

只构建不运行的原因(raw 文档列举):用例自身标了 `build_only: true`;或声明了 `harness` 但本机没有该 harness 环境。

**白话**:它是"抽检机器人"。它不试图测完所有组合(文档原话说:因为覆盖有限,twister **不能保证**本地改动在全量构建环境里成功),但会挑足够多的板子与配置把整个代码树压一遍,防止"某个改动把别的板子搞崩"。

**为什么 CI 要它**:Zephyr 的贡献者规模(4,612 人)与硬件组合量决定了"人肉回归"不可能;twister + 矩阵并行是唯一现实方案。CI 里对应的 workflow(`twister.yaml`)先用 twister 生成**测试计划**,再据此决定矩阵规模,然后分片并行执行,最后汇总。

### 3.8 首次贡献者门槛:action_required

**科学定义**:仓库启用了"外部贡献者需批准才运行 workflow"的策略,未批准时对应 workflow 的运行状态为 `action_required`(不是失败,是没开始)。

**白话**:新面孔第一次来,保安先核对身份才让进车间;批准之后就正常跑。

**实测**:我的 #119887 第二次 push 后,`Compliance Checks`、`Documentation Build`、`DCO Check`、`Coding Guidelines`、`CodeQL`、`Scancode` 一度全为 `action_required`,随后维护者批准,才逐一转成 success。

### 3.9 本地复现清单(把 CI 搬到本机)

```bash
# 0) 准备:west 工作区(以 Zephyr 为主仓)
west init -m https://github.com/zephyrproject-rtos/zephyr --mr main zephyrproject
cd zephyrproject && west update

# 1) 合规(与 CI 同一脚本)
export ZEPHYR_BASE=$PWD
./scripts/ci/check_compliance.py --annotate -c origin/main..

# 2) 只跑与你改动相关的测试目录(比全量快得多)
west twister -T tests/kernel -p native_sim -v

# 3) 单板+单用例
west build -b nrf52840dk/nrf52840 tests/kernel/sched/schedule_api

# 4) 文档构建(与 doc-build.yml 等价,较慢且需 doxygen)
cd doc && cmake -B build -DCMAKE_DOCS_BUILD_SPHINX=ON . && ninja -C build html

# 5) (本机自用)提交信息规则预检:复刻 gitlint 的 UC 规则
python check-commit-msg.py            # 见 10-项目/2026Q4-参与Zephyr开源社区/开源贡献/
```

### 3.10 CI 规模与成本感

- 主仓 **41 个 workflow 文件**;单次 PR 实测 **19 项检查**;
- 仓库体积约 **962 MB**,完整 `west update` 的工作区更大;
- `twister.yaml` 采用"先生成测试计划、再按计划分片"的两阶段设计,说明测试量已大到必须动态规划矩阵;
- 有专门的 `stale-workflow-queue-cleanup.yml` 清理卡住的流水线——流水线自身的运维也是 CI 的一部分。

---

## 4. west 与 PR #1006

### 4.1 west 是什么

**科学定义**:west 是 Zephyr 的**元工具(meta-tool)**:① 多仓库管理(按 manifest 拉取/更新一组 Git 仓库);② 构建封装(`west build`/`flash`/`debug`,内部调用 CMake 与调试器);③ **扩展命令机制**(项目通过 `west-commands` 声明 YAML 描述文件,注册自己的子命令)。它不自带构建系统,而是编排既有工具。

**规模(实测)**:366 star、162 fork、约 41 贡献者、74 个未关闭 issue、仓库约 2 MB、默认分支 `main`。

**白话**:west 是"项目总管 + 包管理器"。你要开发的不是一个仓库,而是几十个仓库凑成的流水线;west 负责按清单把货架摆好,并提供一个统一入口让你敲 `west build` 而不是记一堆 CMake 参数。它还允许别人往这个入口里"插命令"——这就是扩展命令。

### 4.2 west 的架构

| 层 | 文件/模块 | 职责 |
|----|-----------|------|
| 命令行层 | `src/west/app/*`、`src/west/commands.py` | 解析参数、分发到具体命令、发现并加载扩展命令 |
| 清单层 | `src/west/manifest.py` | 解析 manifest、处理 import、投影成 `Manifest`/`Project` 对象、序列化回 YAML |
| 项目层 | `src/west/manifest.py` 的 `Project`/`ManifestProject` | 单个仓库的元数据与 Git 操作入口 |
| 配置层 | `src/west/configuration.py` | 读取/写入 west 配置(全局、系统、工作区) |
| 工具层 | `src/west/util.py`、`src/west/log.py` 等 | 路径、日志、shell 辅助 |

**扩展命令的数据流**(本 PR 的核心):

```text
manifest 中的 west-commands: 字段(str 或 list[str])
        │  解析
        ▼
Project.west_commands:WestCommands(list[str])  ← 本 PR 引入的类
        │  同时记录 manifest_dirs: {entry → 声明它的 manifest 所在目录}
        ▼
commands.py 加载扩展命令时:
   mfst_dir = project.west_commands.manifest_dirs.get(cmd)   ← 现为单次查询
   找到 <mfst_dir>/<entry> 这个 YAML,读取其中的命令定义,再按声明加载 Python 文件
```

### 4.3 manifest 数据模型(理解本 PR 的前提)

| 概念 | 含义 |
|------|------|
| workspace | 由 `west init` 建立、`west update` 维护的多仓目录 |
| `manifest-rev` | west 在每个项目里维护的分支,指向本次 update 指定的修订 |
| import | 一个 manifest 可以导入其他仓库里的 manifest,形成树 |
| self | manifest 所属仓库自身(它的 manifest 可能不在仓库根目录) |
| west-commands 条目 | 一个指向 YAML 的路径,声明扩展命令;**可能出现多个,且来自不同层的 import** |
| manifest_dirs(本 PR 引入) | 条目 → 声明它的 manifest 目录;用于把条目里的相对路径解析到正确根 |

**为什么需要 manifest_dirs**:条目可以来自项目自己的 manifest(`self: west-commands:`),也可以来自它**导入**的 manifest(位于子目录,如 `mf_subdir/west.yml`)。后者的相对路径要相对于**那个子目录**解析,而不是项目根。历史上这份映射是一份与列表平行的私有字典,必须手工同步——这正是 #959 要消除的重复。

### 4.4 问题的来历(时间线,均有实证)

| 时间 | 事件 | 内容 |
|------|------|------|
| 2024-08 | issue **#725** | 真实故障:模块的 manifest 不在模块根目录时(案例 `zmkfirmware/zmk`,manifest 在 `/app/west.yml`),被导入的 `west-commands` 无法解析 |
| 2026-06-08 | PR **#920** 合并 | 修复 #725:把命令路径重定位到项目根,**并新增一份平行字典**记录"命令 → 声明它的 manifest 目录"给 `commands.py` 用 |
| 2026-06-08 | issue **#961** | 由 #920 引入的不一致:`west manifest --resolve` 对路径的归一化"有时保留反斜杠、有时归一化",**priority: high**,milestone v1.6.0 |
| 2026-06-10 | PR **#966** | 更激进的方案:每条目一条 frozen record(`WestCommandsEntry(path, base_dir)`)+ 新公开属性 + **schema 变更**;`mergeable_state=blocked`,三个月未合 |
| (同期) | PR **#962** 合并 | 只是**加测试**,就暴露了 #961;marc-hb 由此立规矩:"记录现状的测试先合,再做重构" |
| 2026-09 | issue **#959** | marc-hb 提出:把这份平行结构收进一个"very basic but actual Python class" |
| 2026-09-21 | PR **#1006**(我) | 按 #959 字面要求实现:`WestCommands(list[str])` 持有 `manifest_dirs`;不改 schema、不改公开属性类型 |
| 2026-09-22 | 协调 | 在 #1006 与 #966 双向留言,请维护者定方向 |

**因果链一句话**:#725 是真 bug → #920 修了它但留下了两套必须同步的结构 → #959 要求消除重复 → 出现两种解法(#966 动 schema、#1006 只动内部)。

### 4.5 三种数据模型对比

| 方案 | 元数据放在哪 | 公开 API 是否变 | schema | 代价 |
|------|--------------|-----------------|--------|------|
| #920 现状 | 平行的私有 dict,手工同步 | 否 | 不变 | 结构可能失步(#959 的动机) |
| **#1006(我的)** | **容器子类持有映射** | **否** | **不变** | 元数据可被 list 原生变异绕过(已在 docstring 说明) |
| #966 | 每条目一条 frozen dataclass | 是(`west_commands` 将弃用) | 扩展为 `str \| list[str] \| list[{file, base-dir}]` | review 成本高;三个月未合 |

**另一种思路(维护者提的)**:模仿 rsync 的 `--relative`——让**路径本身**携带来源信息(用前导路径段导航),从而不需要额外元数据。缺点是会改变路径语义,讨论中未被采纳。

### 4.6 我的实现:WestCommands 类

**类职责(实测源码)**:`src/west/manifest.py`

```python
class WestCommands(list[str]):
    manifest_dirs: dict[str, str]      # 条目 → 声明它的 manifest 目录

    def __init__(west_commands=None)   # 接受 None/str/list,构造时归一化
    def add(entry, manifest_dir=None)  # 去重追加,并记录来源目录
    def merge(other)                   # 合并另一份(可为类或原始值),保留来源
    def as_manifest_value()            # 序列化:单个 → str,多个 → list
```

**改造点(6 处)**:

1. 删除三个散落的模块级 helper(`_west_commands_list`、`_west_commands_maybe_delist`、`_west_commands_merge`),职责收进类;
2. `Project` / `ManifestProject` / `Manifest` 的构造与 `as_dict` 改用该类;
3. `_import_ctx`(NamedTuple)的字段类型改为 `WestCommands`;
4. `Manifest._load_self` 的合并改为 `self._ctx.manifest_west_commands.merge(...)`;
5. 序列化点(`as_dict`)改用 `as_manifest_value()`;
6. `commands.py` 的目录查询从"先查列表再查平行字典"变为一次 `manifest_dirs.get(cmd)`。

**三个设计取舍及理由**(全部写进了代码注释/PR 描述):

| 取舍 | 选择 | 理由 |
|------|------|------|
| dict 子类 vs **list 子类** | list 子类 | `west_commands` 是文档与测试固定的**公开属性**,`test_manifest.py` 明确断言它是"按导入顺序的列表";改类型是破坏性变更 |
| `__iadd__` vs **`merge()`** | `merge()` | `WestCommands` 是 list,`+=` 的既有语义是"追加且允许重复";改成去重会误导读代码的人 |
| `__str__` vs **`as_manifest_value()`** | `as_manifest_value()` | 序列化结果**可能是 str 也可能是 list**,`__str__` 只能返回 str 表达不了;且返回值必须是普通 list(`yaml.safe_dump()` 无法表示 list 子类) |

### 4.7 验证方法与证据

| 验证 | 做法 | 结果 |
|------|------|------|
| 行为零变化 | **不改任何既有测试**,全量跑 | 359 passed,2 skipped,1 xfailed(基线 350 passed) |
| 新增覆盖 | 加 8 个单元测试(构造/去重/合并/序列化/空值回归) | 全绿 |
| 静态检查 | `poe all` = pytest `-W error` + ruff check + ruff format + mypy | 全部通过,format 幂等 |
| 回归对照 | 用 worktree 检出 `upstream/main`,以 `PYTHONPATH` 指过去跑同一段脚本 | 证明空值回归确实是我引入的,并确认修复后行为与基线一致 |

**两个真实踩坑**:

1. **`core.autocrlf=true` 会让 `poe format` 改写 22 个文件**——west 配置写了 `line-ending = "lf"`,而本机检出为 CRLF;在该仓 `git config core.autocrlf false` 解决(west 没有 `.gitattributes` 兜底)。
2. **`_import_ctx` 是 NamedTuple,字段不能用 `+=` 重绑定**(`AttributeError: can't set attribute`),合并只能就地做。

**第一轮 review(Copilot 机器人)发现的真问题**:我把合并提到了真值判断之外,于是 `west-commands: ''` 从"没有命令"变成"一条空路径条目"。复现(对照基线)→ 修复 → 补回归测试 → 在 PR 里说明"改了什么、怎么验证、哪些没改"。这次处理方式被证明是对的:**机器人 review 也按真 review 对待**。

### 4.8 west 的协作文化(实测自 #920 的评审记录)

| 规则 | 原话/依据 |
|------|-----------|
| 提交标题 ≤ 80 字符,正文说明"修了什么问题" | marc-hb 在 #920 的评论 |
| 用 pathlib,不用 `os.path` | "You should never have to handle slashes and backslashes manually" |
| 不给只用两处的内部函数新增参数签名 | "Adding a new argument signature seems overkill" |
| 测试要"加压"(多加一层子目录去压代码) | 同 #920 |
| 错误信息要啰嗦 | "You can never be too verbose when something that unexpected and catastrophic happens" |
| 记录现状的测试先合,再做重构 | #962 → #961 的处理顺序 |
| **更新 PR 用 amend + force-push,禁止 fixup/merge 提交** | west `CONTRIBUTING.rst` |
| 用 `git commit --signoff`(DCO) | 同 |

### 4.9 应用场景:谁受这个 PR 影响

- **manifest 不在仓库根目录的项目**(典型:ZMK,以及一切用子目录做主 manifest 的 SDK 分发);
- **通过 import 组织多层 manifest 的大型工作区**(命令描述文件散落在多层);
- **任何在项目里注册扩展命令的团队**:命令能否被正确定位,取决于"条目 → manifest 目录"这份映射是否可靠;
- **维护者视角**:消除"两处结构手工同步"的隐患,让后续改动(如 #961 的路径一致性)有更清晰的落点。

### 4.10 术语表

| 术语 | 含义 |
|------|------|
| manifest / manifest-rev | 工作区描述文件 / west 维护的修订分支 |
| import / self | 从其他仓库导入 manifest / 当前 manifest 所属仓库自身 |
| west-commands | 声明扩展命令的 YAML 路径(str 或 list) |
| 扩展命令 | 项目注册到 west 的子命令,由 YAML + Python 文件实现 |
| DCO | Developer Certificate of Origin,用 `Signed-off-by` 声明提交权利 |
| tree / commit | Git 的数据结构;对同一内容 amend 后 tree 不变、commit 变 |
| trailer | 提交信息末尾的结构化字段(如 `Signed-off-by`、`Assisted-by`) |

---

## 5. 两条线的交汇:为什么个人贡献者必须懂 CI

1. **CI 是开源的"社会契约"**:4,612 个贡献者的仓库无法靠人工守质量,门禁就是规则本身。不懂 CI 的人第一次提交几乎必然被拦。
2. **CI 失败信息是最高密度的反馈**:`Compliance Checks` 用 annotations 直接指出行号与规则号(UC2/UC4),这是免费的、逐条的代码审查意见。
3. **本地复现能力决定迭代速度**:能本地跑 `check_compliance.py`、twister、文档构建的人,一轮就能过;不能的人会靠推 PR 试错,每次要等维护者批准 CI。
4. **同一套 CI 语言跨项目通用**:DCO、amend+force-push、rebase 而非 merge、记录现状的测试先行——这些在 Zephyr、Linux 内核、west 之间是同构的。学会一次,处处可用。
5. **对本人的直接价值**:这是"能写代码的技术型销售"叙事的硬证据链——能读 4,612 人规模项目的 CI 规则、能在其门禁下把补丁合进去。

---

## 6. 我的三个 PR 与当前状态(2026-09-22)

| # | 仓库 | 标题 | 提交 | 状态 |
|---|------|------|------|------|
| 1 | west | manifest: add a WestCommands class for west-commands entries | `287a718` | open,3 文件 +177/-62,等维护者对 #1006/#966 定方向 |
| 2 | zephyr | doc: west: describe the workflow for developing in a project | `7bc140d` | open,1 文件 +58;CI 已由维护者批准:**合规、DCO、Coding Guidelines、CodeQL、Scancode 全 success**,仅 Documentation Build (HTML) 在跑 |
| 3 | local | `check-commit-msg.py`(复刻 Zephyr gitlint 规则的自检脚本) | — | 双向验证:旧提交复现 CI 的 4 条违规,新提交通过 |

---

## 7. 数据来源与可复现命令

本文所有数字与清单,均可由下列命令复现(2026-09-22 实测):

```bash
# 仓库规模
gh api repos/zephyrproject-rtos/zephyr --jq '.stargazers_count, .forks_count, .open_issues_count, .size'
gh api "repos/zephyrproject-rtos/zephyr/contributors?per_page=1&anon=1" -i | grep -i '^link:'   # 估算贡献者总数

# workflow 清单
gh api repos/zephyrproject-rtos/zephyr/contents/.github/workflows --jq '.[].name'
gh api repos/zephyrproject-rtos/west/contents/.github/workflows --jq '.[].name'

# 合规规则与配置
gh api repos/zephyrproject-rtos/ci-tools/contents/.gitlint --jq '.content' | base64 -d
gh api repos/zephyrproject-rtos/ci-tools/contents/scripts/gitlint/zephyr_commit_rules.py --jq '.content' | base64 -d
gh api repos/zephyrproject-rtos/zephyr/contents/.github/workflows/compliance.yml --jq '.content' | base64 -d

# 一个 PR 触发了哪些检查(把 <sha> 换成 PR 的 head)
gh api repos/zephyrproject-rtos/zephyr/commits/<sha>/check-runs --jq '.check_runs[].name' | sort -u

# twister 文档与源码位置
gh api repos/zephyrproject-rtos/zephyr/contents/doc/develop/twister --jq '.[].name'
```

**不确定/需谨慎表述的点**:

- 贡献者总数 4,612 是"含匿名提交者、按分页估算"的口径;GitHub 页面的公开 contributors 端点有 500 上限,不同口径数字会不同。
- twister 在 CI 里的具体矩阵规模会随提交内容与计划动态变化,本文只描述机制,不给固定数字。
- `Documentation Build (HTML)` 在撰写时仍在运行,最终结论以 CI 页面为准。

---

## 8. 一句话总结

**Zephyr CI 是一台为 4,600 人协作、数百种硬件组合而设计的自动质检线;west PR #1006 则是一个把"两套结构手工同步"收敛成一个类的重构。两者的交汇点是同一条规则:改动必须可验证、可复现、说得清为什么。**
