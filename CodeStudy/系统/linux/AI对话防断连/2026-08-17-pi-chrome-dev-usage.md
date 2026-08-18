# pi chrome-dev 扩展使用指南

> 给 pi 全局拓展 Chrome DevTools 调试网页能力，**全程零截图**（文本快照驱动）。
> 设计文档：[2026-08-17-pi-chrome-dev-design.md](./2026-08-17-pi-chrome-dev-design.md)

## 组成

| 文件 | 作用 |
| --- | --- |
| `~/.pi/agent/extensions/chrome-dev.ts` | pi 扩展入口：注册 19 个 chrome_* 工具（全局，全项目通用，/reload 热重载） |
| `~/.pi/agent/extensions/chrome-dev/browser.ts` | 浏览器管理器：懒连接单例、断线重连、console/网络缓冲、文本快照 |
| `~/.pi/agent/extensions/chrome-dev/lazy.ts` | 懒加载单例工具 |
| `~/.pi/agent/extensions/chrome-dev-launch.sh` | Chrome 启动 helper（带 remote-debugging-port，自动检测复用） |

## 使用

### 1. 启动带调试端口的 Chrome（一次性）

```bash
bash ~/.pi/agent/extensions/chrome-dev-launch.sh
```

- 已有 9222 端口在跑 → 直接复用
- 无 DISPLAY（服务器）→ 自动 `--headless=new`
- 端口/PROFILE 可用 `CHROME_DEV_PORT`/`CHROME_DEV_PROFILE` 覆盖

### 2. pi 内直接用

启动 pi（扩展自动加载），对模型说：

```
帮我调试 xxx 页面：看看控制台报错和网络请求
```

模型会自动调用 `chrome_list_pages` / `chrome_navigate` / `chrome_take_snapshot` / `chrome_list_console_messages` / `chrome_list_network_requests` 等工具。

### 工具清单（19 个，全部非截图）

- **页面**：chrome_list_pages / select_page / new_page / close_page
- **导航**：chrome_navigate / wait_for
- **检查**：chrome_take_snapshot（文本快照，含元素 uid）
- **调试**：chrome_evaluate_script / list_console_messages / list_network_requests / get_network_request
- **输入**：chrome_click / fill / fill_form / press_key / hover / handle_dialog
- **模拟**：chrome_emulate / resize_page

**无任何截图/录屏工具**——页面状态通过 take_snapshot 的文本快照传达（借鉴 playwright-mcp 理念：结构化快照替代截图，省 token 且确定性强）。

### 典型调试流

```
chrome_list_pages → chrome_select_page → chrome_navigate
→ chrome_take_snapshot（拿文本结构+uid）
→ chrome_list_console_messages（报错）
→ chrome_list_network_requests → chrome_get_network_request（404/慢请求详情）
→ chrome_evaluate_script（验证假设/取数据）
→ chrome_click/fill（如需交互复现）
```

## 配置

- `CHROME_DEV_BROWSER_URL`（默认 `http://127.0.0.1:9222`）：扩展连接的 Chrome 调试地址

## 停用

```bash
mv ~/.pi/agent/extensions/chrome-dev.ts ~/.pi/agent/extensions/chrome-dev.ts.disabled
# pi 内 /reload 或重启
```

## 验证记录（2026-08-17）

- Chrome 151 headless + puppeteer-core 24.x：连接/导航/快照/evaluate/console/network 全通
- 实测坑（已修）：新版 puppeteer `Target.targetId` 为内部字段 `_targetId`（已 fallback 链兼容）；`page.evaluate` 无 timeout 参数（改 Promise.race 外层控时）
