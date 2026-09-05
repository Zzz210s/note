---
type: knowledge
tags: [windows, 性能优化, 内存, 磁盘, debloat, 启动项]
status: done
date: 2026-09-05
related: "[[Windows禁用小组件]]"
---

# Windows 内存与磁盘优化记录(2026-09,ELEVEN237038)

> 适用:Win11 常驻内存紧、磁盘被占,想用 GitHub 开源工具做一次可审计的低风险优化。
> 实测背景:2026-09-05,Win11 25H2 build 26200.9168,Dell G15 5520,16G 内存(当时空闲仅 0.5G/3%),353 进程,D/E/F 为动态 VHDX 虚拟盘。
> 一句话本质:默认低风险组合 = Win11Debloat(删内置/关遥测)+ RemoveWindowsAI(去 25H2 AI 组件)+ DISM/cleanmgr + 启动项裁剪;激进项(服务级 tweaks、重制系统)一律不碰。

## 一、优化前基线

- 内存:16G 总,空闲 0.5G(3%);353 进程;uptime 3+ 天
- 大内存占用:qemu 4.2G 私有、java x2 ~2.7G、多 node、Edge 全家、Docker Desktop
- 磁盘:C: 952G NVMe 剩 252G(26%);D(400G)/E(70G)/F(30G) 是 C: 上的动态 VHDX 后备文件(Msft Virtual Disk)
- 启动项一堆:WallpaperEngine、微信、QQNT、Edge、PixPin、Ditto、夸克、CC Switch、Docker Desktop、DeskGo、AweSun

## 二、GitHub 调研结论(2026-09 实测星数)

筛选原则:2026 年内活跃、有开源许可证、星数实锤;黑盒二进制类一律过审再跑。

| 方向 | 选用 | 星数 | 理由 |
|---|---|---|---|
| 删内置/关遥测 | Raphire/Win11Debloat | 56.7k | PowerShell 逐项可审、自带注册表备份+还原点、GUI 预设全 |
| 去 AI 组件 | zoicware/RemoveWindowsAI | 13.0k | 25H2 专属,Copilot/Recall/AIFabric |
| 内存应急 | IgorMundstein/WinMemoryCleaner | 5.0k | Console 模式可脚本化,签名+sha256 可验 |
| 磁盘分析/卸载 | dundee/gdu、BCUninstaller | 6.0k/21.1k | gdu 秒级扫描;BCU 批量干净卸载(备用) |

未选:ChrisTitusTech/winutil、hellzerg/optimizer(服务级 tweaks 属激进档);Atlas-OS(重制系统,日常机不值);farag2/Sophia-Script(量太大);各类新内存清理器(<500 星,清工作集骗数字)。

## 三、执行过程与结果

### 1. Win11Debloat(保守集,exit 0)

`Win11Debloat.ps1 -CLI -Silent -CreateRestorePoint -RemoveApps -DisableTelemetry -DisableSuggestions -DisableEdgeAds -DisableLockscreenTips -DisableBing ...`

- 删除 84 个内置 appx(Clipchamp/Bing 全家/Cortana/AIHub/PC Manager/OfficeHub/OneNote UWP/Solitaire/StickyNotes/GetHelp 等)
- DiagTrack(遥测)Disabled;4 个 CEIP/遥测计划任务禁用
- 广告/建议/Edge 广告/锁屏提示/Store 搜索建议关闭
- 自建注册表备份 JSON + 系统还原点(可回退)

### 2. RemoveWindowsAI(保守子集)

`-Options DisableRegKeys,DisableCopilotPolicies,RemoveAppxPackages,RemoveRecallFeature,HideAIComponents,DisableRewrite,RemoveWindowsAITasks`

- AIFabric.CBS.1.6 appx 删除;Copilot/Recall 相关 appx 与注册表残留归零;11 条 Copilot 策略禁用
- Recall 可选功能本机原本就是 DisabledWithPayloadRemoved(前置状态)

### 3. DISM + cleanmgr

`Dism /Online /Cleanup-Image /StartComponentCleanup` + `cleanmgr /AUTOCLEAN`
→ C: 空闲 **252.0 -> 261.8 GB(+9.8G)**

### 4. VHDX 收缩(部分成功)

`Optimize-Volume D/E/F -ReTrim`:盘内 unmap 已标记,但**宿主 .vhdx 文件未缩**(在线方式局限)→ 见待办,需离线 `Optimize-VHD`,预计再回收 ~80-90G。

### 5. WinMemoryCleaner(温和档)

`WinMemoryCleaner.exe /StandbyListLowPriority /CombinedPageList /ModifiedPageList /ModifiedFileCache /RegistryCache /SystemFileCache`
不碰 WorkingSet,避免卡 qemu/java。

### 6. 启动项裁剪(第 2 轮)

用 StartupApproved 禁用标志(任务管理器可见、可逆),非删除:
- Docker Desktop(HKCU)-> 禁用,改按需启动(手动点开,com.docker.service Manual 会自动跟起)
- AweSun(HKLM)-> 禁用(SunloginService 本就 Manual/Stopped)
- Edge 自启:删 Run 项不够(Edge 会自己加回),补策略级封堵 `HKCU\Software\Policies\Microsoft\Edge`:`StartupBoostEnabled=0` + `BackgroundModeEnabled=0`
- 夸克网盘:预检发现早已是禁用态(启动项标志+调度任务都 Disabled),无需处理

## 四、坑与最佳实践(本机实测)

- **ps1 脚本 UTF-8 无 BOM 会被 PS5.1 按 GBK 误读**,大面积 ParserError → 用 `[IO.File]::WriteAllText(..., New-Object Text.UTF8Encoding($true))` 存 BOM 再跑
- **`powershell -File x.ps1 -Options a,b,c` 不拆数组**:逗号串当整体传,ValidateSet 直接拒;空格多值也只绑第一个,后续裸串绑到下一个参数 → 绕法:外层提权脚本内直接 `& x.ps1 -Options @(...)`(原生数组绑定)
- **bash 传参给 powershell 内联命令,`$` 会被 shell 吞** → 一律写成 .ps1 文件再 `-File` 执行
- 在线 ReTrim 不缩宿主 VHDX 文件,要缩必须卸载卷后离线 Optimize-VHD(Hyper-V 模块)
- rwai.ps1 结尾 `exit` 会连带杀掉外层提权 wrapper(验证段没跑),结果要独立验证
- Win11Debloat 是**多文件项目**(引用 Scripts/Regfiles/Config),单文件下载会跑挂,要整仓浅克隆

## 五、待办 / 待定(重启后收尾)

- [ ] 重启:应用全部改动(explorer 界面项)+ 清 3 天 uptime 的内存积压;重启后复测内存/进程数
- [ ] 决策:VHDX 离线压缩(需短暂断开 D/E/F,关掉用盘的程序),潜在回收 ~80-90G
- [ ] 观察:WSearch 当前 Disabled,若开始菜单搜索明显变慢需恢复
- [ ] 工具目录去留:`%TEMP%\opt\`(gdu/WinMemoryCleaner 便携版可留作日后用)

## 六、可复用命令速查

```powershell
# 看端口排除区间(报 WSAEACCES / bind 失败先查这个)
netsh interface ipv4 show excludedportrange protocol=tcp
# StartupApproved 禁用启动项(3=禁用标志,可逆)
Set-ItemProperty 'HKCU:\...\Explorer\StartupApproved\Run' -Name 'Xxx' -Value ([byte[]](3,0,0,0,0,0,0,0,0,0,0,0)) -Type Binary
# Edge 策略级禁自启
New-Item 'HKCU:\Software\Policies\Microsoft\Edge' -Force | Out-Null
Set-ItemProperty 'HKCU:\Software\Policies\Microsoft\Edge' -Name 'StartupBoostEnabled' -Value 0 -Type DWord
# 在线 VHDX unmap(不缩宿主文件)
Optimize-Volume D -ReTrim
```

## 同批次其它处理(非本次主题,速记)

nekobox 便携版(E:\1-nekobox\nekoray)core 启动失败:`initialize inbound mixed: bind 127.0.0.1:7890 ... access permissions`。根因非端口占用,是 **winnat/WSL2 动态排除区间 7821-8020 覆盖 7890**(实测 7890/7891 bind 均失败)。修法:`config/groups/nekobox.json` 的 `inbound_socks_port` 7890 -> 2080(区间外,实测可 bind);注意 nekobox 运行时退出会覆写配置,要先完全退出再改文件。备份留在 `nekobox.json.bak-7890-excl`。

## 相关与复习

- [[Windows禁用小组件]] —— 同类"后台进程清理"主题
- [[UAC-管理员软件免弹窗]] —— 提权(UAC)执行的配套经验
