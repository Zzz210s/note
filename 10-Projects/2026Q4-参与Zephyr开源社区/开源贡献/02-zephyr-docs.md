---
type: log
tags: [开源, Zephyr, 文档, west, PR]
date: 2026-09-22
related: "[[!实施计划]] / [[提交清单]]"
---

# 补丁 2:Zephyr 文档 —— west 里"在项目中开发"的工作流

- **issue**:https://github.com/zephyrproject-rtos/zephyr/issues/24328(2020-04 创建;`tejlmand` 2026-08-04 明确说仍然有效)
- **PR**:https://github.com/zephyrproject-rtos/zephyr/pull/119887(提交 `7bc140d`,1 文件 +58/-0)
- **状态**:open(2026-09-22 提交);文档构建已过,合规检查首轮失败后已修

## 一、缺口在哪(读现有文档得出)

| 已有 | 位置 |
|------|------|
| 为什么 west 安全(安全 / 确定性两条要求,detached HEAD 的取舍) | `doc/develop/west/why.rst` 的 "``west update`` detached HEADs" 节,末尾还给了 `--rebase` / `--keep-descendants` 各一句适用场景 |
| 两个选项的细节与失败行为 | `doc/develop/west/built-in.rst` 的 `west update` 选项说明与 note |
| west 拥有哪些 Git ref | `doc/develop/west/workspaces.rst` 的 `manifest-rev` 与 `refs/west/*` 两节 |

**缺的正是"工作流"** —— tejlmand 的原话:"It's good they are described... but it doesn't help people to understand how a good workflow is ensured."(选项被描述了,但没人告诉你怎么做才是在项目里开发的正确姿势。)

## 二、方案

在 `workspaces.rst` 的 `The refs/west/* Git refs` 之后新增一节 **`Developing in a project`**(并加标签 `west-developing-in-a-project`)。选这页的理由:它正是解释"west 拥有哪些 ref"的那页,而"你的分支是你的"这条保证必须紧挨着它讲。

内容三段:

1. **保证**:不被打扰时 west 只创建/更新 `manifest-rev` 与 `refs/west/` 下的 ref;你建的分支是你的,除非你显式用 `west update --rebase` 要求它改写
2. **工作流**:在项目里建分支并提交 → `west update --rebase`(唯一一次 west 动你的分支)→ 或者普通 `west update`(分支留在原地、detached HEAD)→ 或 `--keep-descendants`(不 rebase 但尽量保留分支)
3. **提醒**:不要在 west 留下的 detached HEAD 上提交再 update(那些提交不属于任何分支,可能被 gc)

外加一句术语说明:Zephyr 用户把这类项目叫 *module*,对 west 而言就是普通 project,所以这套工作流同样适用。**交叉引用 `why.rst` 与 `built-in.rst` 而不是复制内容。**

## 三、踩的两个坑(都值得复用)

- **CRLF 陷阱**:全局 `core.autocrlf=true` 让 clone 出来的文件在工作树里是 CRLF,而 Zephyr 的 `.gitattributes` **没有** `text=auto` → 不设 `core.autocrlf false` 就会把 CRLF 原样提交进去。修法:`git config core.autocrlf false` 后 `git rm --cached -r -q . && git reset --hard`(整树以 LF 重写),再用 `git status` 确认干净。
- **`--signoff` 与手写 trailer 重复**:消息里写了 `Signed-off-by:` 又用了 `git commit --signoff` → trailer 出现两条。改用 `git commit -F <file>`(消息里一次性写好 `Signed-off-by` + `Assisted-by`),不加 `--signoff`。

## 四、本地验证(没能构建文档)

本机是 Windows,且用的是稀疏检出,无法跑 Zephyr 的 Sphinx 构建。改做的检查:

- `docutils` 解析整个文件无结构错误(只有既有的 Sphinx 专有角色如 `:file:` 报"未知角色")
- 本节用到的三个 `:ref:` 目标都存在:`west-update`、`west-update-detached-heads`、`west-manifest-rev`
- 标题下划线长度全部足够

真正的检查交给 CI 的文档构建。

## 六、marc-hb 的 review(2026-09-22)与第二轮修改

维护者 marc-hb 给了实质反馈(非套话),五条:

| 他的意见 | 我的处理 |
|----------|----------|
| 位置与文字都好,但"有点啰嗦";建议提及 `west update -h` 并删掉与它的重叠 | 节从 58 行压到 **47 行**(文件层面 26 插入 / 35 删除);第 3 步不再复述 `--keep-descendants` 行为,改为指向 `west update --help` 的 `checked out branch behavior` 选项组与 `:ref:`west-update`` |
| 术语:issue 标题说 module,west 说 project,**两者不是同一回事**、这不是措辞偏好,应说明并链接到已有页面 | 加了一句明确区分,并链到 :ref:`modules-vs-projects`(即 `doc/develop/modules.rst` 的 "Modules vs west projects" 一节,它又链到 `west-workspace` / `west-manifests-projects`) |
| west 的 "project" 一词含糊,建议用更精确的 "git repo",甚至改节标题 | 采纳:节标题改为 **"Developing in a git repository"**,标签改名 `west-developing-in-a-git-repository`,正文用 git repository |
| 文档构建越来越重(现在还要 twister 生成内容),希望有"轻量构建" | 不在本 PR 范围;已回复:若他指定位置(doc/Makefile 或贡献文档),我另开 PR 加 rstcheck 用法 |
| “你是指单文件直接跑 rstcheck 和 rst2html?” | 如实回答:我用的是 docutils 的 `publish_doctree` API(并把 Sphinx 专有角色注册为空实现);并给出一条**实测可用**的 rstcheck 单文件命令(见下) |
| 为什么不用 WSL2 | 如实回答:本机只有 `docker-desktop` 这个 distro,没有通用发行版;我为内核线本就要装真 Linux,下一次文档改动会在那里跑完整构建 |

新提交 `55b40ff`(amend + force-push)。推送后 CI 再次回到 `action_required`(首次贡献者需维护者批准)。

**实测可用的单文件 rstcheck 命令**(rstcheck 6.3.0;不加参数会把每个 `:ref:` 报成 unknown role):

```bash
rstcheck --report-level warning \
  --ignore-roles ref,file,envvar,kconfig,option,command,kbd,abbr,term,numref,download \
  --ignore-directives code-block,toctree,literalinclude,doxygenstruct,doxygengroup,csv-table,table,figure,image \
  doc/develop/west/workspaces.rst
# 本次输出:Success! No issues detected.
```

`--report-level warning` 是必需的:跨文件引用的标签会在单文件检查里报 `INFO Hyperlink target ... is not referenced`。

## 五、首轮 CI:文档构建过了,合规检查卡在提交信息

| 检查 | 结果 |
|------|------|
| Documentation Build (HTML) / Status | **success**("all jobs passed") |
| Copilot review | `Approval recommended, findings: None` |
| **Compliance Checks** | **failure** —— 两条规则:UC2、UC4 |

两条失败及修法:

- **UC2**:`Signed-off-by` 必须两词全名。规则实现(`ci-tools/scripts/gitlint/zephyr_commit_rules.py`)是 `re.search(r"(^)Signed-off-by: ([-'\w.]+) ([-'\w.]+) (.*)")`,`ChenChen` 单字 → fail。改为 `Chen Chen <chenchen237038@qq.com>`
- **UC4**:正文单行上限 **75** 字符,我三行超宽(76/78/76)→ 拆行至 ≤75

修法:`git commit --amend --reset-author -F <已重排的消息文件>` 后 `--force-with-lease=分支:旧 sha` 强推(`7bc140d`)。**注意**:同时手写 trailer 又加 `--signoff` 会产生两条 `Signed-off-by`(我在 west 那边先踩过一次)。

## 六、待跟进

- [ ] CI 文档构建结果(首次向 zephyr 仓库提交,部分 workflow 可能需要批准)
- [ ] 等 review;若被要求改 placement(独立页)或 module/project 措辞,按意见改
