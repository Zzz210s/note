---
type: log
tags: [windows, UAC, 计划任务, nekobox, 开机自启]
status: done
date: 2026-09-03
related: "[[UAC-管理员软件免弹窗]]"
---

# 记录-nekobox 免 UAC 弹窗改造

> 事件:nekobox 每次开机自启都弹 UAC"是否允许更改"。改造为计划任务最高权限静默启动,已落地待下次重启验证。
> 方法原理见笔记 [[UAC-管理员软件免弹窗]](方案 A),本篇只记事件与踩坑。

## 一、现象与排查

- 症状:开机(约 16:43)弹 UAC;nekobox 一直在托盘运行,不能随便重启测试。
- `sigcheck -m` 结论:`nekobox.exe` **无签名、无 requestedExecutionLevel**(默认 asInvoker)。
  → 弹窗不是启动器要求提权,而是它开 TUN 需要管理员,普通启动后**内部自我提权重启**。
  → 对策 = 方案 A"开局即提权":用计划任务(最高权限)在登录时直接拉起,让它一出生就是管理员,不再自我重启。
- 自启现状:HKCU Run 键 `nekobox = "E:\1-nekobox\nekoray\nekobox.exe" -tray`;全局配置在 `config/groups/nekobox.json`(键 `vpn_internal_tun: true`、`start_minimal: true`),无 autoStart 字段 → 自启状态只以 Run 键存在。

## 二、落地内容

| 项 | 值 |
|---|---|
| 计划任务 | `NekoBox-Elevated`(AtLogOn user=23652 / Interactive / **Highest** / IgnoreNew / ExecutionTimeLimit=0 不限) |
| 动作 | `E:\1-nekobox\nekoray\nekobox.exe -tray` |
| Run 键 | 已删(备份 `C:\Users\23652\nekobox-uac\run-key-backup.txt`) |
| 文件 | `C:\Users\23652\nekobox-uac\setup-nekobox.ps1`(幂等可重跑)/ `start-nekobox.vbs`(手动静默启动) |

## 三、踩坑(通用,值得记住)

1. **提权注册是最后一次 UAC**:RunLevel Highest 的任务必须由管理员会话创建(普通会话报拒绝访问)。共点了 4 次 UAC 才弄对,后 3 次都是脚本自身 bug。
2. **Windows PowerShell 5.1 脚本必须存 UTF-8 带 BOM**:无 BOM 时按 ANSI/GBK 解析,中文注释/字符串字节错位 → 报"字符串缺少终止符 / try 缺少 catch",且 `-File` 直接 exit 1、看不到原因(加 try/catch 日志也没用,因为**根本没解析成功**)。
3. **`& {}` 子块里 `$MyInvocation.MyCommand.Path` 为空** → 脚本目录要在顶层取一次再传入。
4. **驻留型程序的计划任务要把 ExecutionTimeLimit 设 0**:默认 72h 会把 TUN 进程掐掉。
5. `schtasks /run` 手动触发测试会再拉一个实例(TUN 会双开),nekobox 正在运行时**别测**;等重启验证最稳。

## 四、恢复 / 复发处理

- 恢复原状:`reg add "HKCU\...\Run" /v nekobox /d "\"E:\1-nekobox\nekoray\nekobox.exe\" -tray"` + `schtasks /delete /tn NekoBox-Elevated /f`
- 若在 nekobox 设置里重新勾了"开机自启"(它重写 Run 键指向裸 exe)→ 弹窗回归;重跑一次 setup-nekobox.ps1 即可(需一次 UAC)。
- 手动静默启动:双击 `C:\Users\23652\nekobox-uac\start-nekobox.vbs`。

## 五、验证状态

- 任务参数全部核对无误(Execute/Highest/LogonType=Interactive/触发器 user=ELEVEN237038\23652/IgnoreNew/TimeLimit=PT0S)。
- 尚未实际触发(LastRun=从未);等下次重启登录时验证是否无 UAC 弹窗且 TUN 正常。
