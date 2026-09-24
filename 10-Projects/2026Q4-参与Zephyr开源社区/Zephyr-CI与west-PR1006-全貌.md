---
type: note
tags: [Zephyr, west, CI, 开源, PR]
status: done
date: 2026-09-22
related: "[[2026Q4-参与Zephyr开源社区/!项目说明|!项目说明]] / [[2026Q4-参与Zephyr开源社区/!实施计划|!实施计划]]"
---

# Zephyr CI 与 west PR #1006 全貌

> 一份"科学定义 + 白话解释"并行的说明,用于快速建立整体认知。
> 事实来源:本机 `gh api` 对 `zephyrproject-rtos/zephyr` 与 `zephyrproject-rtos/west` 的实测查询,以及 PR #1006 的元数据与评审内容(2026-09-22)。文末列出哪些是实测、哪些是推断。

---

## 一、一句话定位

| 对象 | 科学定义 | 白话 |
|---|---|---|
| **west** | Zephyr 生态的多仓库工作区管理工具(meta-tool):按 manifest 声明克隆/同步多个 Git 仓库,并提供可扩展的命令层 | 工地总管:按图纸把几十个仓库摆到该在的位置,并给工人一套统一口令 |
| **Zephyr CI** | 由 GitHub Actions 事件触发的检查流水线集合:合规、构建测试、文档、代码质量、发布 | 质检流水线:每次交活(PR/推送)都自动跑一遍规则、编译、测试、出文档 |
| **PR #1006** | west 中 `manifest.py` 的重构:引入 `WestCommands` 列表子类,让它自己持有每条 west-commands 条目所属的 manifest 目录 | 把"清单条目"和"条目出自哪张图纸"绑在一起,不再靠人手对齐两份数据 |

---

## 二、west 是什么(科学定义)

**形式化描述**

- **工作区(workspace)**:一个包含 `.west/` 元数据目录的根目录;其下是若干 Git 仓库,每个仓库在 manifest 中有唯一 `name`、`path`、`revision`。
- **manifest**:一份 YAML(默认 `west.yml`),声明 `manifest.self`(清单自身所在仓库)与 `manifest.projects`(其余仓库)。可 `import` 其它 manifest 形成层级。
- **west-commands 扩展协议**:仓库可通过 `west-commands.yml` 声明自定义命令,文件本身由 schema(`west-commands-schema.yml`)约束。
- **命令层**:`src/west/app/` 提供内置命令(`init`/`update`/`build`/`flash`/`config`/`manifest` 等),`project.py` 是最大的实现文件(实测 112 KB)。

**实测的仓库结构**(`gh api repos/zephyrproject-rtos/west/contents`):

```
.codecov.yml  .github  CONTRIBUTING.rst  LICENSE  MAINTAINERS.rst
MANIFEST.in   README.rst  pyproject.toml  src  tests  uv.lock
src/west/  ->  app/(config.py main.py project.py)  commands.py
               manifest.py  manifest-schema.yml  west-commands-schema.yml
               configuration.py  log.py  util.py  version.py
```

**白话解释**

Zephyr 不是一个仓库,而是几十个仓库(内核、HAL、各厂商模块、工具)。`west init` 读 `west.yml`,把该有的仓库拉齐;`west update` 按 `revision` 同步到指定版本;`west build`/`flash` 调 CMake/Ninja 与烧录工具。它同时是**插件的宿主**:任何仓库放一个 `west-commands.yml`,就能给 west 增加命令(例如 Zephyr 仓库自己提供的 `west build`)。

---

## 三、Zephyr CI 是什么

**科学定义**:由 GitHub Actions 承载的、按事件(PR、push、定时、发布)触发的检查与产物流水线集合;每个 workflow 是一组有依赖关系的 job,失败会阻塞合并。

**实测的 workflow 清单**(`.github/workflows/`,分类):

| 类别 | workflow |
|---|---|
| 合规与流程 | `compliance.yml`、`dco.yml`、`coding_guidelines.yml`(`_full` 变体)、`license_check.yml`、`pr_metadata_check.yml`、`greet_first_time_contributor.yml`、`stale_issue.yml`、`assigner.yml` |
| 构建与测试 | `twister.yaml`、`twister_tests.yml`、`twister_tests_blackbox.yml`、`twister-publish.yaml`、`sanitizers.yml`、`bsim-tests.yaml`、`footprint-tracking.yml`、`daily_test_version.yml` |
| 文档 | `doc-build.yml`、`doc-publish.yml`、`doc-publish-pr.yml`、`doxygen-checks.yml` |
| 代码质量 | `codeql.yml`、`gcc-analyzer.yml`、`devicetree_checks.yml`、`errno.yml`、`scorecards.yml`、`pinned-gh-actions.yml` |
| 发布与维护 | `release.yml`、`backport.yml`、`backport_issue_check.yml`、`manifest.yml`、`stats_merged_prs.yml` |
| west 集成 | `west_cmds.yml`("Zephyr West Command Tests") |

**合规流水线内部**(实测 `compliance.yml` 的步骤顺序):

```
更新 PATH(让 west 可用) → actions/checkout → rebase 到目标分支
  → setup-python → 安装 Python 依赖 → west setup
  → setup-node → npm --prefix ./scripts/ci ci
  → ./scripts/ci/check_compliance.py --annotate <excludes> -c origin/${BASE_REF}..
  → 上传 compliance.xml 与 dts_linter.patch 产物
```

**白话解释**

- **合规检查**干的事:提交信息是否规范(主题长度、`Signed-off-by` 的 DCO 认证、不能有 merge 提交)、许可证头、代码风格、Devicetree 绑定等。`check_compliance.py` 是执行者,产出 `compliance.xml` 报告并回帖到 PR。
- **twister** 是 Zephyr 的测试运行器:按 `tests/` 下的 `testcase.yaml`/`sample.yaml` 生成测试计划,在大量板子上编译并运行,结果汇总发布。
- **dco.yml** 专门验证 `Signed-off-by`(开发者来源认证)。这与 AI 协作直接相关:AI 不得代签。

---

## 四、PR #1006 在整体中的位置

**它改的是 west 的清单模型,不是 Zephyr 内核,也不改 CI 流程本身。** 但因为 Zephyr 的 CI 会跑 `west_cmds.yml`(west 命令测试),west 的行为变化最终会被 CI 覆盖。

**问题(#959)**:每条 `west-commands` 条目所属的 manifest 目录,原先存在 `Project`/`ManifestProject` 的一个私有属性里,需要**人手与条目列表保持同步**——两处数据、一处真相,容易漂移。

**方案(实测 PR 元数据 + 讨论)**:

| 设计点 | 选择 | 理由 |
|---|---|---|
| 容器类型 | **list 子类**(`WestCommands`),不是 dict 子类 | `west_commands` 是**公开且被测试**的"路径列表"(`tests/test_manifest.py` 断言导入顺序),改成 dict 会破坏外部使用者;list 子类则 `manifest.py` 之外无需改动 |
| 去重合并 | 新增 `merge()`,不重载 `+=` | 对 list 而言 `+=` 语义是"追加、允许重复",重载成"去重"会反直觉 |
| 序列化 | `as_manifest_value()` 返回普通 `str`/`list`,不用 `__str__` | `yaml.safe_dump()` 无法表示 list 子类,必须退化为原生类型 |
| 空值 | `west-commands: ''` 仍视为"无命令" | 保持既有行为;`merge()` 放在原有真值判断之内 |
| 元数据同步 | 记录"条目 → manifest 目录";用 `append()` 加入的条目**没有目录**,按文档语义相对项目根解析 | 不做"不可伪造"的元数据(那需要组合而非继承,会改变公开属性类型) |

**评审记录**:Copilot 指出 `self: west-commands: ''` 的假值回归(会记录一个空路径、并让 `as_dict()` 输出空值);已修并补了回归测试 `test_west_commands_falsey_value_in_self_is_ignored`。

**当前状态**(实测):`OPEN`,`mergeable_state: blocked`,1 个提交,+179 / −62,3 个文件;提交信息含人工 `Signed-off-by`,并按 Zephyr 的 AI 政策补了 `Assisted-by:` 披露尾注。

---

## 五、应用场景

| 角色 | 用 west 做什么 | 受 CI 约束什么 |
|---|---|---|
| 应用开发者 | `west init/update` 拉齐工作区;`west build -b <board>` 编译;`west flash` 烧录 | 提交信息与许可证合规;改动需通过 twister 测试矩阵 |
| 模块/驱动维护者 | 在自己的仓库里用 `west-commands.yml` 扩展命令 | 新增命令要过 `west_cmds.yml` 测试 |
| 下游发行版/集成商 | 用自定义 manifest 组合不同 revision 的仓库 | manifest 变更由 `manifest.yml` 检查 |
| 工具开发者(本 PR 的语境) | 修改 west 的清单模型与命令层 | west 自身的测试 + Zephyr 侧的 west 命令测试 |

---

## 六、技术栈

| 层 | 技术 |
|---|---|
| west | Python(打包 `pyproject.toml`,锁文件 `uv.lock`),测试在 `tests/`(pytest),schema 用 YAML schema |
| Zephyr 构建 | CMake + Ninja + Kconfig + Devicetree,工具链按架构切换 |
| 测试运行器 | **twister**(生成 testplan,批量编译/运行,汇总结果) |
| CI | **GitHub Actions**;合规脚本 `scripts/ci/check_compliance.py`(Python)+ `scripts/ci`(Node 依赖,`npm ci`) |
| 制品 | `compliance.xml`、`dts_linter.patch`、测试结果、文档站点产物 |

---

## 七、快速上手(常用命令)

```bash
# 工作区
west init -m https://github.com/zephyrproject-rtos/zephyr --mr main zephyrproject
cd zephyrproject && west update

# 构建与烧录
west build -b <board> samples/hello_world
west flash

# 清单与扩展
west manifest --path            # 当前 manifest 位置
west manifest --validate        # 校验 manifest
# 仓库内提供 west-commands.yml 即可新增命令

# 测试(在 Zephyr 仓库内)
./scripts/twister -T tests/ -p <board>
```

---

## 八、把两者连起来看(一句话串完)

> **west** 负责"把代码摆对、把命令给全",**manifest** 是它的唯一真相源;**Zephyr CI** 负责"每次交活自动验一遍",其中合规与测试都依赖 west 的能力;**PR #1006** 做的正是加固那个真相源——让"命令条目"与"它出自哪张清单"不再可能失配。

---

## 附:事实边界(本文的可信度声明)

| 内容 | 来源 |
|---|---|
| west 仓库目录、`src/west/` 结构、`project.py` 大小、Zephyr 的 workflow 清单、`compliance.yml` 步骤、`west_cmds.yml` 名称 | **实测**:本机 `gh api` 查询(2026-09-22) |
| PR #1006 的改动、设计理由、评审意见、状态、`Assisted-by` | **实测**:`gh pr view` / `gh api` 读取 PR 元数据、评论与 diff 概要 |
| manifest 语义、west-commands 协议、twister 定位、`check_compliance.py` 职责 | 领域知识(与实测结构一致);具体实现细节以其文档与源码为准 |
| "应用场景"一节的角色划分 | 归纳,非官方分类 |
