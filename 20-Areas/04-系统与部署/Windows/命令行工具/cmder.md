---
type: tutorial
tags: [Windows, Cmder, 命令行工具, 终端]
status: done
date: 2026-08-16
related: "[[git]]"
---

# Cmder

Cmder 是一款 Windows 平台的增强型命令行终端模拟器，基于 ConEmu，集成了 Clink（增强版 cmd），Full 版还内置 Git for Windows。便携式设计，解压即用，支持多标签页、丰富的颜色主题以及 Linux 常用命令（`ls`、`grep`、`curl`、`vim`、`ssh` 等）。

---

# 版本选择

| 版本 | 说明 |
| --- | --- |
| Mini | 不含 Git，体积小；已安装 Git 时可选 |
| Full | 内置 Git for Windows，自带大量 Unix/Linux 命令（`git`、`cat`、`vim`、`tar`、`ssh` 等），开箱即用 |

- 最新稳定版：`v1.3.25`（2024-05-31）
- 下载地址：<https://cmder.app/> 或 <https://github.com/cmderdev/cmder/releases>

---

# 安装

1. 下载压缩包（`.zip` / `.7z`）。
2. 解压到**全英文、无空格、无需管理员权限**的目录（避免 `C:\Program Files` 等）。
3. 运行 `Cmder.exe` 启动。

## 环境变量（可选）

- 新建系统变量 `CMDER_ROOT`，值为 Cmder 解压目录（如 `D:\tools\cmder`）。
- 将 `%CMDER_ROOT%` 加入系统 `PATH`，即可在任意位置执行 `cmder` 命令。
- 放入 `%CMDER_ROOT%\bin` 目录的可执行文件会自动注入系统 PATH。

## 注册右键菜单（可选）

以管理员身份运行：

```cmd
Cmder.exe /REGISTER ALL
```

取消注册：

```cmd
Cmder.exe /UNREGISTER ALL
```

---

# 使用

## 启动

- 双击 `Cmder.exe`，或命令行输入 `cmder` 启动。
- 可在 `设置 → 启动` 指定默认启动的终端（cmd / PowerShell / Git Bash 等）。

## 新建标签页 / 切换 Shell

- `Ctrl + T`：新建标签页（可选终端类型）。
- 一个窗口内可同时运行 cmd、PowerShell、Git Bash、WSL 等多个 Shell。

## 别名 alias

- 配置文件：`%CMDER_ROOT%\config\user_aliases.cmd`
- 在终端输入 `alias` 可查看已有别名。
- 添加别名后立即生效并持久保存。

---

# 快捷键

| 快捷键 | 功能 |
| --- | --- |
| `Ctrl + T` | 新建标签页 |
| `Ctrl + W` | 关闭当前标签页 |
| `Ctrl + Tab` | 切换标签页 |
| `Ctrl + 数字` | 切换到第 N 个标签页 |
| `Ctrl + R` | 历史命令搜索 |
| `Alt + Enter` | 全屏切换 |
| `Alt + Shift + 1` | 启动 cmd |
| `Alt + Shift + 2` | 启动 PowerShell |
| `Alt + Shift + 3` | 启动管理员权限 PowerShell |
| 鼠标选中文本 | 自动复制 |
| 右键 / `Ctrl + V` | 粘贴 |
| `Ctrl + 鼠标滚轮` | 缩放文字 |

---

# 集成 IDE / 终端

## VSCode

在 `settings.json` 中添加：

```json
"terminal.integrated.profiles.windows": {
  "Cmder": {
    "path": "${env:windir}\\System32\\cmd.exe",
    "args": ["/k", "${env:CMDER_ROOT}\\vendor\\init.bat"]
  }
},
"terminal.integrated.defaultProfile.windows": "Cmder"
```

## Windows Terminal

在 Windows Terminal 设置中添加新配置文件，将命令行可执行文件指向 `Cmder.exe`。

---

# 常见问题

- **中文乱码**：终端中执行 `set LC_ALL=zh-CN.UTF8`，或在设置中调整编码。
- **快捷键冲突**：部分快捷键可能与 VSCode 等应用冲突，在 Cmder 设置中调整。
