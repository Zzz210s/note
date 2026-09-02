# pi-config 模块拆解(config-pi 仓库)

> 真源:私有仓库 `github.com/Zzz210s/config-pi`(本地 `~/config-pi`),部署目标 `~/.pi/agent/`。
> 核心链路:**改真源 -> `setup.sh` 部署 -> `git push`**;pi 升级后:`pi update -> setup.sh -> verify.sh`。
> 相关笔记:[pi会话机制与电脑重启后恢复](<./pi会话机制与电脑重启后恢复.md>)

## 一、总体架构

```text
~/config-pi(单一真源,git 管理)
  ├── setup.sh        一键部署到 ~/.pi/agent(幂等)
  ├── verify.sh       部署体检(7 组 31 项,pi update 后自愈验证)
  ├── config/         全局指令 + 设置 + 密钥模板
  ├── extensions/     pi 扩展(目录型 5 个 + 散装 12 个)
  ├── patches/        对 pi 本体 dist 的二进制补丁
  ├── prompts/        subagent 任务模板
  ├── agents/         subagent 角色定义
  ├── skills/         技能库(17 个)
  └── specs/          设计文档与实现计划
```

`pi update` 只替换 pi npm 包,**不动** `~/.pi/agent` 用户内容;真正会失效的是 dist 补丁与扩展依赖,由 setup.sh 重跑自愈(verify.sh 全绿即链路完好;实测该体检抓出过补丁静默空转、依赖重装失败两个真实隐患)。

## 二、config/ —— 配置与全局指令

| 文件 | 作用 | 使用 | 效果 |
|---|---|---|---|
| `AGENTS.md` | pi 全局指令(所有会话自动注入) | 内含 Git 规则、自动调用规则(gh/chrome-dev/code_find/github-readme)、pi 配置同步规则、禁 emoji、代码文件 <=200 行等永久规则 | 每条规则都在对应场景自动生效,无需人工提醒 |
| `settings.json` | pi 启动设置 | 默认 provider/model(ark-coding / glm-5.2)、theme、tuiMode、npm 包清单 | 换模型改这里或用 /model;包清单驱动 pi 启动时装载 npm 扩展 |
| `auth.json.template` / `model-hub.json.template` | 密钥占位模板 | setup.sh 仅在目标缺失时从模板生成,真实密钥文件**永不入库** | 新设备 clone 后填 key 即用;仓库泄露不泄密 |
| `trust.json.example` | 项目信任示例 | trust.json 由 setup.sh 按 $HOME 生成 | 决定哪些目录免信任弹窗 |

## 三、extensions/ —— 扩展(核心模块)

### 3.1 codegraph/(目录型,本地代码检索)

tree-sitter 符号/调用图索引 + SQLite,零模型零网络。五语言:Python / TypeScript / TSX / Go / Java。

| 工具/命令 | 作用 | 使用 |
|---|---|---|
| `code_find` | 找函数/类/方法定义,file:line + 签名;同层按 PageRank 排序(泛化词优先出枢纽文件) | 传符号名(精确/前缀/子串),替代多轮 rg |
| `code_trace` | 调用链追溯(谁调用 X / X 调用什么,含同文件边) | symbol + direction=callers/callees,depth 1-5 |
| `code_impact` | 变更影响面(受影响文件/符号/测试清单) | target 传文件路径或符号名 |
| `code_map` | 整仓浓缩地图(PageRank 排序 + token 预算填充) | token_budget 200..8000,默认 1500;陌生仓库一次看结构 |
| `/reindex` | 建库/增量更新(文件哈希对比只重解析改动) | 首次进仓库或改码后;库在 `.codegraph/`(建议 gitignore) |
| `/code doctor` | 体检:依赖加载/索引完整性/语言分布/陈旧度/.gitignore 建议 | 索引异常时 |

效果(实测):aider 151 文件冷索引 952ms、hono 355 文件 2.2s、cobra 36 文件 0.4s;83/83 单测绿;库损坏自动提示删除重建。依赖 6 个 npm 包,重装需 `.npmrc` 的 legacy-peer-deps(随仓库分发)。

### 3.2 chrome-dev/(目录型,网页调试)

连接 9222 调试端口的 Chrome,19 个 `chrome_*` 工具。典型链路:`chrome_list_pages -> chrome_navigate -> chrome_take_snapshot`(文本快照拿 uid)-> `chrome_list_console_messages` / `chrome_list_network_requests` / `chrome_evaluate_script`;交互用 `chrome_click` / `chrome_fill`。

效果:控制台报错、网络 4xx/5xx、部署后冒烟验证等场景**实测浏览器真实状态**而非凭代码推测;无截图能力(省 token);Chrome 空闲 15 分钟自动退出,不常驻。启动:`bash ~/.pi/agent/extensions/chrome-dev-launch.sh`。

### 3.3 model-hub/(目录型,provider 治理)

三职责:① 多 key provider 注册 #2/#3 实例轮换;② `after_provider_response` 捕 429 并记录 reset 时间(state.ts);③ provider/模型名归一化。配置在 `~/.pi/agent/model-hub.json`(多 key/端点)。

效果:同套餐多 key 自动轮换、429 后按重置时间避让;/model 菜单已回归 pi 原生(model-hub 不再接管)。

### 3.4 providers.ts(散装,中国套餐接入)

注册 ark-coding / ark-plan(火山方舟,Anthropic Messages)、qwen-token-plan(阿里)、commandcode(双端点:Claude 走 Anthropic,其余走 OpenAI Chat Completions)。鉴权:环境变量(写 ~/.bashrc)优先,缺失则 pi 交互输入存 auth.json;commandcode 模型目录 24h 本地缓存。

效果:新增模型只需编辑对应数组;三个套餐的 key 存 auth.json。

### 3.5 plan-mode/(目录型,只读规划模式)

`/plan` 或 Ctrl+Alt+P 切换:禁用内置写工具,bash 限制为只读白名单;从「Plan:」段抽编号步骤,执行期用 `[DONE:n]` 勾选,带进度组件。

效果:探索/分析阶段防误改;计划->执行两阶段工作流。

### 3.6 subagent/(目录型,子代理委派)

`subagent` 工具:为每次调用 spawn 独立 pi 进程(隔离上下文窗口),不污染主对话。模式 single / parallel / chain({previous} 占位传前序输出)。角色定义在 agents/。

效果:并行跑多任务(如「检测未完成任务」时 3 会话互不干扰);主会话只收结论。

### 3.7 其余散装扩展(行为守护类)

| 扩展 | 作用 | 效果 |
|---|---|---|
| `permission-gate.ts` | 危险 bash 命令(rm -rf/sudo/chmod 777)前弹确认 | 防误删 |
| `confirm-destructive.ts` | 会话破坏性操作(clear/switch/branch)前确认 | 防丢上下文 |
| `dirty-repo-guard.ts` | 有未提交改动时阻止会话切换 | 逼先 commit 再换上下文 |
| `protected-paths.ts` | 拦截对敏感路径的 write/edit | 防误改关键文件 |
| `git-checkpoint.ts` | 每轮 git stash 快照;/fork 时可选还原代码状态 | 分叉实验可回滚 |
| `git-merge-and-resolve.ts` | 每轮后 fetch+merge 上游;干净合并静默,冲突留现场 | 工作分支保持最新 |
| `auto-commit-on-exit.ts` | 退出时用最后一条助手消息生成 commit | 离场即有存档 |
| `handoff.ts` | 替代有损 compact:抽取关键上下文生成新会话首提示 | 长任务无压无损交接 |
| `usage-dashboard.ts` | `/usage`:各套餐**吞吐量口径**用量(网页面板是计费量口径,订阅请求计 0 费故永远显示很低) | 真实限流预警 |
| `timed-confirm.ts` | 带倒计时的确认/选择对话框示例 | 超时自动取消 |

### 3.8 tab-status(外部仓库部署)

来自 `~/pi-tab-status`(github.com/Zzz210s/pi-tab-status),setup.sh 末尾单独部署(必须在 extensions 重建之后),自带 29 个单测。作用:标签页状态展示。

## 四、patches/ —— pi 本体补丁

| 补丁 | 作用 | 效果 |
|---|---|---|
| `wheel-scroll-speed.sh` | 改 pi TUI 滚轮速度 | 每格 1 -> 3 行(PI_WHEEL_SCROLL_LINES 可调),修 tmux 内滚轮卡顿;自动探测 WSL/Windows 安装路径与两种打包形态;打不上时非零退出告警 |

pi update 会覆盖 dist,**更新后必须重跑**(setup.sh 自动做;曾因 heredoc 传参 bug 静默空转,已修复并由 verify.sh 兜底)。

## 五、prompts/ 与 agents/ —— 子代理配套

- `agents/`:planner(规划)/ reviewer(评审)/ scout(侦察)/ worker(通用执行)四个角色定义,供 subagent 按名调用。
- `prompts/`:implement.md(纯执行)、implement-and-review.md(执行+评审)、scout-and-plan.md(侦察+规划)三类任务模板。

## 六、skills/ —— 技能库(17 个)

brainstorming、dispatching-parallel-agents、executing-plans、finishing-a-development-branch、github-readme、receiving-code-review、requesting-code-review、subagent-driven-development、systematic-debugging、test-driven-development、ui-ux-pro-max、using-git-worktrees、using-superpowers、verification-before-completion、writing-plans、writing-skills。

机制:任务描述命中技能名时自动加载其 SKILL.md 指令。策略:`skills/` 是唯一真源,外部散装技能包一律屏蔽(移入 `~/.pi/agent/skills-disabled/`)。

## 七、specs/ —— 设计文档

model-hub(design+plan)、codegraph(design+plan+mvp1-plan+mvp2-plan)。每个功能先 spec 后实现,实测结论回写 spec(如 codegraph 三期实测数据均在 design 第 6 节)。

## 八、setup.sh / verify.sh —— 部署与体检

**setup.sh(幂等,顺序敏感)**:装 pi/gh -> 覆盖式部署 config/extensions/patches/prompts/agents/specs/skills(rm+cp 重建,故扩展依赖须重装,原生模块不可跨机复制)-> 密钥模板仅缺失时生成 -> `pi update --extensions`(npm 扩展包)-> 按架构下载 fd/rg -> 跑 patches -> 部署 config-cli(其内部链式克隆并部署 ai-route)-> 部署 pi-tab-status(必须在 extensions 重建后)。

**verify.sh(8 组 33 项)**:pi 本体 / wheel 补丁标记 / 扩展依赖逐个 require / 扩展单测 / settings 合法性与密钥在位 / 仓库-部署一致性(忽略 pi 自管的 lastChangelogVersion 与 tab-status 合法差异)/ pi list / ai-route 链(仓库在位 + detect 同源 + 命令在位)。全绿 = 更新后链路完好。

## 九、外部配套仓库与 npm 包

| 来源 | 内容 | 效果 |
|---|---|---|
| `ai-route`(~/ai-route,独立仓库) | 本地 AI API 中央路由:`ai-route status/json/env/proxy`;lib/detect.js 会话感知端点探测 | 所有 CLI 共享同一套路由;hook 的 detect 部署件与其同源 |
| `config-cli`(~/cli-config) | OpenCommit git hook(AI 自动生成中文 conventional commit,失败静默降级;引用 ai-route 的 detect.js) | 任何仓库 commit 信息自动生成;OCO_HOOK_DISABLE=1 逃生舱 |
| `pi-tab-status` | 标签页状态扩展 | 见 3.8 |
| npm:pi-mcp-adapter | MCP 网关(mcp/mcpScript 工具) | 批量 MCP 调用与脚本编排 |
| npm:pi-web-access | 网页访问(检测到 gh 时 GitHub 请求自动走 gh api) | 免匿名限流 |
| npm:pi-cache-optimizer | 缓存统计与 /cache-optimizer doctor/stats/fix | 配合 pi 0.84+ 原生 footer 缓存命中率 |

## 十、全局约束(写入 AGENTS.md 的永久规则)

1. 所有代码文件(含测试)<= 200 行,超出必须拆模块
2. 所有 AI 输出禁止 emoji
3. AI 文件不入业务仓库(gitignore + rm --cached)
4. 密钥文件永不入库,仓库存 *.template
5. pi 配置变更必须:改 config-pi -> setup.sh -> commit/push
6. pi update 后必须:setup.sh + verify.sh 全绿
