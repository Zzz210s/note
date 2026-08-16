# AI 对话防断连方案（tmux 自动包裹 + 终端调优）

## 目标

在远程服务器上运行 AI 对话类 CLI（`pi` / `claude` / `opencode`）时，同时满足三点：

1. **防中断** —— SSH 掉线、VS Code 窗口关闭、本地网络抖动，都不打断正在进行的 AI 对话。
2. **不卡顿** —— 对话界面颜色正常、无花屏；按 `ESC`、`Ctrl+Enter`、`Shift+Enter` 无延迟、不被吞键。
3. **鼠标滚轮翻历史 + 选择复制粘贴** —— 用 pi 的 fullscreen TUI 模式：滚轮滚动对话记录、拖选即复制；tmux 不劫持鼠标。

## 原理

把交互式 AI 命令自动包进一个「每项目一个」的持久 tmux 会话：

- 命令在 tmux 会话里运行，SSH 断了只是「离开」会话，进程继续跑；
- 重新登录后，在同一目录再敲一次命令（如 `pi`），会自动 attach 回原会话，续上刚才的对话；
- 会话名按项目目录推导（`<工具>-<目录名>-<cksum4>`），不同项目互不干扰；
- 已存在同名会话时只 attach、绝不重复启动，避免一个项目跑出多个进程。

终端体验由 `.tmux.conf` 统一调优（真彩色、`escape-time`、`extended-keys`、OSC52 剪贴板）：鼠标由 tmux-scroll-toggle 管理（默认滚动模式滚轮翻历史）——pi 的 fullscreen 模式用自己的滚轮滚动对话记录、拖选复制，tmux 透传不拦截（见下文「浏览上下文」）。

## 组成

| 文件 | 作用 |
| --- | --- |
| `.tmux.conf` | tmux 终端调优：真彩色、回滚缓冲、按键延迟、鼠标不劫持（原生选区/复制）、键盘翻历史、OSC52 剪贴板、崩溃恢复 |
| `pi-tmux.sh` | 包裹 `pi`：自动进持久 tmux 会话 |
| `claude-tmux.sh` | 包裹 `claude`：自动进持久 tmux 会话 + 内存/OOM 守卫 |
| `opencode-tmux.sh` | 包裹 `opencode`：自动进持久 tmux 会话 + `Ctrl+C` 后一键续会话 |
| `tmux-cleanup.sh` | 定时回收「已 detach 且空闲超时」的会话，释放内存（cron 运行） |

配套系统层（可选，推荐）：

- 加 swap（防内存不足触发 OOM 杀掉会话进程）；
- sshd 保活（`ClientAliveInterval` 降低掉线频率）；
- 客户端 SSH 心跳（`ServerAliveInterval`）。

## 部署

### 1. 安装 tmux 与插件

```bash
sudo apt update && sudo apt install -y tmux

# TPM + resurrect + continuum（用于「重启后恢复会话」）
git clone https://github.com/tmux-plugins/tpm ~/.tmux/plugins/tpm
```

首次进入 tmux 后按 `prefix + I`（默认 `Ctrl+b` 然后 `I`）安装 `.tmux.conf` 里声明的插件。

### 2. 放置配置文件

```bash
cp .tmux.conf ~/.tmux.conf
cp pi-tmux.sh ~/.pi-tmux.sh
cp claude-tmux.sh ~/.claude-tmux.sh
cp opencode-tmux.sh ~/.opencode-tmux.sh
mkdir -p ~/claude-anti-drop
cp tmux-cleanup.sh ~/claude-anti-drop/tmux-cleanup.sh
```

### 3. 让包裹脚本生效（`~/.bashrc` 末尾追加）

```bash
[ -f ~/.claude-tmux.sh ] && . ~/.claude-tmux.sh
[ -f ~/.opencode-tmux.sh ] && . ~/.opencode-tmux.sh
[ -f ~/.pi-tmux.sh ] && . ~/.pi-tmux.sh
```

重新开一个 shell（或 `source ~/.bashrc`）后生效。

### 4. 定时清理空闲会话（可选）

```bash
crontab -e
# 每小时运行一次
0 * * * * /bin/bash /home/$USER/claude-anti-drop/tmux-cleanup.sh
```

### 5. 系统层加固（可选）

```bash
# swap（防 OOM）
sudo fallocate -l 8G /swapfile && sudo chmod 600 /swapfile \
  && sudo mkswap /swapfile && sudo swapon /swapfile \
  && echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab

# sshd 保活
echo -e 'ClientAliveInterval 30\nClientAliveCountMax 3' \
  | sudo tee /etc/ssh/sshd_config.d/99-keepalive.conf
sudo systemctl reload ssh
```

## 验证

```bash
# 1) 脚本语法
bash -n ~/.pi-tmux.sh ~/.claude-tmux.sh ~/.opencode-tmux.sh

# 2) 在项目目录敲 pi / claude，应进入 tmux（echo $TMUX 非空）；
#    另一个终端再敲一次同一命令，应 attach 回同一会话，而非新开进程。

# 3) 鼠标：图形终端里划选文本应为原生选区/复制（tmux 不拦截）。

# 3b) 键盘翻历史：Ctrl+b [ 进入 copy 模式，PageUp/PageDown 翻页，q 退出回实时画面。

# 4) 按键：在 TUI 里按 ESC / Ctrl+Enter，应无延迟、不吞键。

# 5) 崩溃恢复（可选）：重启 tmux 服务后，resurrect/continuum 恢复会话。
```

## 浏览上下文（滚轮 + 键盘）

**首选：pi 的 fullscreen TUI 模式**。在 pi 里输入 `/settings`，把 **TUI mode** 设为 `fullscreen`（立即生效，并作为默认），或设置 `tuiMode: "fullscreen"`。此模式下 pi 自己接管视口：

| 操作 | 方式 |
| --- | --- |
| 滚轮滚动对话记录 | 鼠标滚轮 / 触控板 |
| 选择文本并复制 | 鼠标拖选（自动复制到剪贴板） |
| 翻页 | `PageUp` / `PageDown` |
| 到顶部 / 到底部 | `Home` / `End` |
| 搜索记录 | `Ctrl+Shift+F` |
| 上/下一条消息 | `Ctrl+Shift+↑` / `Ctrl+Shift+↓` |

> fullscreen 模式下滚轮事件直达 pi（tmux 不拦截），拖选由 pi 处理，与 `mouse off` 的原生选区互不冲突。

**claude / opencode 等无自带滚轮的 TUI：用 `tmux-scroll-toggle` 插件**（本地插件 `~/.tmux/plugins/tmux-scroll-toggle/`）。默认 `mouse on`（滚动模式）：滚轮翻历史、拖拽选中文字并复制、松开不跳输入框、`Ctrl+C` 复制；`Ctrl+b m` 切到「选区模式」（原生选区/复制）。

| 操作 | 方式 |
| --- | --- |
| 切换 选区/滚动 模式 | `Ctrl+b` `m` |
| 滚动模式(默认)：滚轮翻历史 | 滚轮 → copy-mode，滚到底自动退出 |
| 滚动模式：拖拽选中 | 选中文字高亮并复制，松开不跳输入行 |
| 滚动模式：复制选中文字 | `Ctrl+C` |
| 退出选中状态回输入 | `q` / `Esc` |
| 选区模式：原生选区/复制 | `Ctrl+b m` 切过去后直接用 |
| 兜底：tmux copy 模式 | `Ctrl+b` `[`，vim 键位 `j`/`k`/`g`/`G`/`?`/`/`，`q` 退出 |

## 回滚

```bash
# 注释 ~/.bashrc 里的 3 行 source，重新开 shell 即回到裸命令。
# 删掉配置文件：
rm -f ~/.tmux.conf ~/.pi-tmux.sh ~/.claude-tmux.sh ~/.opencode-tmux.sh
```

## 说明

- 三个包裹脚本只拦截「交互式」入口；`pi -p`、`claude -p`、`opencode run` 等非交互子命令原样透传，不影响脚本化/流水线调用。
- `claude-tmux.sh` 内含内存守卫：并行实例数 ≥ 上限、或可用内存（RAM+swap）低于阈值时拒绝新开实例，防止 OOM 断连；可用 `CLAUDE_FORCE=1` 单次绕过。
- 该方案保证的是「进程不因掉线而死」，恢复后靠工具自带的续会话能力（如 `--resume` / `--continue`）接上历史，不是内存级进程快照。
- 上下文回看首选 pi fullscreen 模式（滚轮翻记录 + 拖选复制）；claude/opencode 等无自带滚轮的 TUI 用 `tmux-scroll-toggle` 插件（默认滚动模式滚轮翻历史，`Ctrl+b m` 切选区模式）；两者都不满足时用 tmux copy 模式（`Ctrl+b [`）回看。
