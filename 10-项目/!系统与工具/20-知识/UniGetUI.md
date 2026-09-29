---
type: tutorial
tags: [windows, 包管理器, unigetui, scoop, chocolatey, winget, 软件管理, PATH]
status: done
date: 2026-09-29
related: "[[cmder]]"
---

# UniGetUI:三套包管理器的职责划分与配置(教程)

> 适用:机器上同时装了 scoop / Chocolatey / winget,想让它们**各管一摊**、由一个 GUI 统一管应用。
> 实测背景:2026-09-28/29,Win11 25H2 build 26200.9168;UniGetUI 2026.3.0(build 107)、scoop、Chocolatey 2.7.0、winget 1.29.380。
> 一句话本质:**应用走 Chocolatey(经 UniGetUI 的 GUI),SDK 走 scoop CLI,winget 弃用**(保留在系统里但不使用)。

## 一、职责划分(最终形态)

| 管理器 | 管什么 | 怎么用 | 本例条目 |
|---|---|---|---|
| **scoop** | **仅 SDK 与开发 CLI** | 命令行(`scoop install` / `scoop-search`) | python、make、cacert、temurin21-jdk、bat、fd、jq、ripgrep、gh、helix、dark、shellcheck、wget、7zip、pwsh、scoop-search、latex |
| **Chocolatey** | **普通应用** | **只经 UniGetUI 的界面**(不直接敲 choco) | Cmder、pandoc、wireshark |
| **winget** | 不使用 | —— | 保留在系统(App Installer 不可卸),后端已在 UniGetUI 中关闭 |

判据:语言运行时/编译器/构建工具/命令行开发工具 → scoop;GUI 应用与文档类软件 → choco。这样两棵安装树彻底分开:scoop 在 `~\scoop`,choco 把应用装到各自的标准位置(`C:\tools\...`、`C:\Program Files\...`、`%LOCALAPPDATA%\...`)。

## 二、UniGetUI 的配置机制(重要)

**设置就是文件**:`%LOCALAPPDATA%\UniGetUI\Configuration\` 下,一个设置一个文件,名字就是设置键名。

| 类型 | 磁盘表示 |
|---|---|
| 布尔 | **文件存在 = true**(内容被忽略);删除文件 = false |
| 数值/字符串 | 文件**内容**即值(纯文本) |
| 字典/列表 | 文件内容为 **JSON**(字典是对象,列表是数组) |

所以可以**离线预置**设置,不必进 GUI 点(改前先整目录备份)。

### 关闭 winget 后端

```
文件:%LOCALAPPDATA%\UniGetUI\Configuration\DisabledManagers
内容:{"Winget": true}
```

键名 `DisabledManagers` 与语义(取管理器 `Name` 做键、布尔做值)来自源码 `PackageManager.cs` 的 `IsEnabled()`;键名在**本机已安装的 `UniGetUI.exe` 字符串**里逐个核对过存在,所以不怕版本差异。

### 本次写入的优化项

| 键名 | 值 | 作用 |
|---|---|---|
| `DisabledManagers` | `{"Winget": true}` | 关闭 winget 后端 |
| `DisableTelemetry` | 启用 | 关闭遥测上报 |
| `DisableLangAutoUpdater` | 启用 | 不再后台自动更新语言包 |
| `IgnoreUpdatesNotApplicable` | 启用 | 更新列表不再显示"不适用"条目 |
| `RedactUsernameInLog` | 启用 | 日志中隐去用户名 |
| `ParallelOperationCount` | `4` | 并行操作数(批量装/升更快) |
| `UpdatesCheckInterval` | `21600` | 更新检查间隔 6 小时(**单位是秒**) |

配置目录备份:`%LOCALAPPDATA%\UniGetUI\Configuration.bak-<时间戳>`(整目录复制即可回滚)。

**choco 后端不依赖 PATH**:UniGetUI 源码里内置了 `C:\ProgramData\chocolatey\bin\choco.exe` 这个默认路径,所以即使 `choco` 不在 PATH 里,它也能发现 Chocolatey 后端。

## 三、日常操作方式

| 想做什么 | 怎么做 |
|---|---|
| 装 / 升级 / 卸载普通应用 | 打开 **UniGetUI**(它走 choco 后端) |
| 装 / 升级语言运行时、编译器、CLI 工具 | `scoop install <名字>` / `scoop update *`(搜索用 `scoop-search <关键词>`) |
| 需要 winget 清单里的东西 | 先想清楚是否真需要;当前策略是**不用** |

## 四、实测踩过的坑

### 1. choco 走代理时下载极慢,而且**不打印进度**

实测 ~**50 KB/s**,一个 94MB 的包要 20 分钟;界面上只停在 `Downloading package from source 'https://community.chocolatey.org/api/v2/'` 一动不动,看起来像死锁,其实在下载。

**定位方法**(卡住时先证明它在动,而不是猜):
- 采样下载暂存目录的大小:`%TEMP%\chocolatey`(`ChocolateyScratch\<包名>`)
- 把子命令的输出重定向到文件再 `tail`:`& choco install <包> -y --no-progress *>&1 | Out-File x.log`

### 2. `.chocolateyPending` 文件锁 → "安装失败"但应用其实装好了

现象:choco 报 `wireshark not installed. An error occurred during installation: 文件 .chocolateyPending 正由另一进程使用`,但 `C:\Program Files\Wireshark\Wireshark.exe` 已存在、注册表也有卸载项。

原因:上一次 choco 进程残留(未退出)占着包目录锁;真正失败的是**记录阶段**,不是厂商安装器。

**修法**(从缓存重注册,**不重跑厂商安装器**):

```powershell
choco install <包> --force --skip-automation-scripts -y --no-progress
```

### 3. 先清残留进程再做任何 choco 操作

`Get-Process choco | Stop-Process -Force` —— 否则新命令会卡住或被锁。

### 4. choco 的安装位置是固定的,不跟自定义盘目录规则走

例:Cmder 装在 `C:\tools\Cmder`,pandoc 在 `%LOCALAPPDATA%\Pandoc`。这是包脚本决定的,**不要**指望它落到 D:/E: 的自定义目录。因此替换后要**重新核对依赖路径的东西**(例如右键菜单、编辑器 PATH)。

### 5. 同一软件被两个管理器装上 = PATH 打架

`scoop` 与 `choco` 都会往 PATH 写自己的 shim/目录。同一软件装两份(`miktex`/`latex` 各一份)时,`Get-Command <命令>` 指向谁取决于 PATH 顺序。**迁移时务必先装新的、验证可用,再卸旧的**;装完用下面的清单核验落点。

## 五、验证清单(命令)

```powershell
# 三套管理器各自的状态
scoop list                                  # SDK 与开发 CLI
choco list                                  # 普通应用
Get-Command cmder, pandoc, miktex, latex    # 关键可执行文件当前解析到哪(防 PATH 打架)
Get-Service *docker* | Select Name,StartType  # 顺带确认 Docker 仍为手动启动

# UniGetUI 侧
Get-Content "$env:LOCALAPPDATA\UniGetUI\Configuration\DisabledManagers"   # 应为 {"Winget": true}
```

## 六、本次迁移记录(2026-09-28/29)

- **移出 scoop → choco**:cmder(→`C:\tools\Cmder`)、pandoc(→`%LOCALAPPDATA%\Pandoc`)、wireshark(→`C:\Program Files\Wireshark`),装好验证后已 `scoop uninstall` 旧的
- **MiKTeX 去重**:choco 的 `miktex`/`miktex.install` 是装 wireshark 时的依赖,与 scoop 的 `latex`(MiKTeX 25.12,更新)重复 → 已 `choco uninstall` 掉 choco 那份,命令统一解析到 scoop 版
- **顺带修复**:`temurin21-jdk`(JDK 21)之前被移除,导致 VS Code 的 `java.import.gradle.java.home` 指向失效路径(即 [[记录-VS Code-Java与Gradle版本兼容修复]] 的修复失效)→ 已 `scoop install temurin21-jdk` 恢复
- **产物清理**:choco 下载暂存 477MB 已删;scoop 缓存 683MB **保留**(重装时能秒装,不急着回收)

## 七、回滚方式

| 改动 | 回滚 |
|---|---|
| UniGetUI 设置 | 用 `Configuration.bak-<时间戳>` 覆盖回 `Configuration\` |
| 关掉的 winget 后端 | 删掉 `Configuration\DisabledManagers` 文件(或改成 `{"Winget": false}`) |
| 移出的 3 个应用 | `scoop install cmder pandoc wireshark`(choco 那份可用 UniGetUI 卸载) |
