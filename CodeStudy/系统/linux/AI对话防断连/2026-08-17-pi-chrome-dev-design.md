# pi chrome-dev 调试扩展设计

**日期**：2026-08-17
**位置**：`~/.pi/agent/extensions/chrome-dev.ts`（pi 全局扩展，自动发现，全项目通用）
**依赖**：`puppeteer-core`（连接已有 Chrome，不下载 Chromium）、typebox（pi 内置）
**状态**：已实现并验证（2026-08-17）

## 1. 目标

给 pi 全局拓展「Chrome DevTools 调试网页」能力：pi 可控制并检查实时 Chrome，做导航/输入/网络监控/控制台日志/性能分析/JS 执行，**全程零截图**（页面状态用文本可访问性快照传达给 LLM，不返回任何图片字节）。

### 确认决策

- **方案 B**：自建精简 pi 扩展（非 fork chrome-devtools-mcp），源头只注册非截图工具。
- **连接模式**：默认 connect 已有 Chrome（`--remote-debugging-port=9222`），复用登录态，不下载 Chromium；launch 作为可选 fallback。
- **快照驱动**：借鉴 playwright-mcp，页面状态用**文本/可访问性快照**，绕过截图。
- **零遥测**：不接 Google usage statistics / CrUX。

### 不做（YAGNI）

截图（take_screenshot）、录屏（screencast）、Lighthouse 审计、堆快照内存分析、自动下载 Chromium、独立 MCP server 进程（直接用 pi 扩展 registerTool，更轻更全局）。

## 2. 技术选型

| 层 | 选择 | 理由 |
|---|---|---|
| 形态 | **pi 扩展**（`pi.registerTool`） | 比 stdio MCP server 更轻：无独立进程、全局自动发现、热重载（`/reload`）、天然全项目通用 |
| 浏览器自动化 | `puppeteer-core` + CDP | 与 pi 同为 Node/TS；core 版不下浏览器，连已有 Chrome |
| 连接 | `puppeteer.connect({ browserURL })` 到 `http://127.0.0.1:9222` | 复用登录态；省 Chromium 下载 |
| 页面状态传达 | 文本/可访问性快照（`page.accessibility.snapshot()` + DOM 文本摘要） | 绕过截图，token 友好 |
| schema | typebox `Type.Object`（pi 内置） | 与 pi 扩展规范一致 |
| 遥测 | 硬编码关闭 | 隐私 |

## 3. 架构

```
pi (LLM) ──registerTool──> chrome-dev.ts 扩展
                                │ puppeteer-core .connect(browserURL)
                                ▼
                     Chrome (remote-debugging-port=9222, 已有登录态)
                                │ CDP over WebSocket
                                ▼
                          目标网页（多 tab/page）
```

扩展维护一个**连接单例**：首次工具调用时 connect（懒连接），后续复用；连接断开自动重连。多 page 通过 `browser.pages()` + `pageId` 路由。

### 配置

- Chrome 前置：用户以 `--remote-debugging-port=9222 --user-data-dir=...` 启动 Chrome（提供 helper 脚本 `~/.pi/agent/extensions/chrome-dev-launch.sh` 拉起带调试端口的 Chrome）。
- 扩展配置：`BROWSER_URL` 环境变量覆盖（默认 `http://127.0.0.1:9222`）。

## 4. 工具集（MVP，全部非截图）

| 类别 | 工具 | 说明 |
|---|---|---|
| 连接/页面 | `list_pages` | 列出所有 tab（title/url），返回 pageId |
| | `select_page` | 切换当前活动 page（by pageId） |
| | `new_page` / `close_page` | 新建/关闭 tab |
| 导航 | `navigate` | 跳转 URL，等 load |
| | `wait_for` | 等待选择器/超时 |
| 检查 | `take_snapshot` | **文本快照**：可访问性树 + 可见 DOM 文本摘要（替代截图），含元素 uid 供 click/fill 引用 |
| 调试 | `evaluate_script` | 在页执行 JS，返回结果 |
| | `list_console_messages` | 控制台日志（含 source、level、stack） |
| | `list_network_requests` | 网络请求列表（url/method/status/资源类型） |
| | `get_network_request` | 单个请求详情（headers/body/response） |
| 输入 | `click` / `fill` / `fill_form` / `press_key` / `hover` / `handle_dialog` | 用 snapshot 返回的 uid 或选择器定位 |
| 模拟 | `emulate`（设备/视口）/ `resize_page` | |

**明确不注册**：take_screenshot、screencast_start/stop、任何返回 image 的能力。pi 工具列表里不存在这些。

## 5. 错误处理与安全

- 未连接 Chrome -> 工具返回清晰错误 + 提示运行 chrome-dev-launch.sh
- uid 失效（页面已变）-> 提示重新 take_snapshot
- evaluate_script 超时默认 5s，防卡死
- 连接断开 -> 下次调用自动重连
- 不做截图 = 无法泄露页面视觉内容给 LLM（隐私边界友好）

## 6. 开发顺序

1. 脚手架：扩展骨架 + 连接单例（懒 connect + 重连）+ `list_pages` 工具
2. 导航 + 文本快照（navigate/take_snapshot/select_page/new_page/close_page/wait_for）
3. 调试工具（evaluate_script/console/network）
4. 输入 + 模拟（click/fill/press_key/emulate）
5. Chrome 启动 helper 脚本 + 文档（README/用法）
6. 验证：pi 内实测「调试某网页控制台报错 + 网络 404 + 性能瓶颈」，确认零截图

## 7. 参考（调研结论摘要）

- **chrome-devtools-mcp**（Google，49k★）：复用其 launch/connect 双模式、工具分类、文本快照；避开 take_screenshot/screencast/遥测/CrUX。
- **playwright-mcp**（Microsoft，36k★）：复用其「可访问性快照绕过截图」核心理念、--caps 按需能力；避开 vision 能力。
- **browser-use**（Python）：定位为 agent 本身而非给 agent 加工具，栈不契合，不采用。
