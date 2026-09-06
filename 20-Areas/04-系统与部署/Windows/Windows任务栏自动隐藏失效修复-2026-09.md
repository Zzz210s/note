---
type: troubleshooting
tags: [windows, 任务栏, 自动隐藏, explorer, 系统修复]
status: done
date: 2026-09-06
related: "[[Windows内存与磁盘优化记录-2026-09]]"
---

# Windows 11 任务栏自动隐藏失效修复记录(25H2)

> 适用:设置里开了"自动隐藏任务栏",任务栏却不隐藏;或隐藏功能时好时坏。
> 实测背景:2026-09-06,Win11 25H2 build 26200.9168,单显示器 1536x864;机器常驻 QQ/微信/Wallpaper Engine/Ditto/PixPin 等第三方。
> 一句话本质:设置值与 explorer 内部状态脱节时,直接改注册表 + 重启 explorer 无法重置;**必须在设置 UI 里把开关关掉再打开一次**(或注销/重启),让任务栏状态机复位。

## 一、现象

个性化 -> 任务栏 -> 任务栏行为 -> 已勾选"自动隐藏任务栏",但任务栏一直显示,不随鼠标离开底部而收起。

## 二、排查结论(证据链)

| 检查 | 结果 | 结论 |
|---|---|---|
| 注册表 `HKCU\...\Explorer\StuckRects3` Settings byte[8] | =3(自动隐藏开) | 设置已正确写入 |
| `SHAppBarMessage(ABM_GETSTATE)` 询问 explorer | =ABS_AUTOHIDE(0x1) | explorer 自己也认为"自动隐藏已开启" |
| 重启 explorer | 无效 | 不是 explorer 进程状态问题 |
| 停掉全部第三方常驻(QQ/微信/WE/Ditto/PixPin) | 无效 | 不是第三方抢占 |
| 注册表直接 toggle(2->3)+ 重启 explorer | 无效 | 改注册表通道无法唤醒隐藏逻辑 |
| **设置 UI 里手动 关 -> 开 一次** | **立即生效** | 官方通道通知 explorer 重置状态机 |

根因:explorer 任务栏(XAML)内部状态机卡死——设置已开、explorer 也认为已开,但不执行隐藏动作。直接改注册表/重启 explorer 都绕过了 explorer 自己的通知通道,只有设置 App 的开关(走正常通知)能复位。同类状态机卡死常见诱因:睡眠唤醒、显示器热插拔/虚拟显示器、系统更新后。

## 三、修复步骤(核心)

1. `Win+I` -> 个性化 -> 任务栏 -> 展开"任务栏行为"
2. 把"自动隐藏任务栏"**关闭,等 2 秒,再打开**
3. 立即生效,无需重启

若上述无效(状态卡得深),按序尝试:
- 注销再登录(彻底重置 shell)
- 重启系统
- 检查系统更新(25H2 有相关已知 bug,部分已随累积更新修复)
- 干净启动排查第三方(msconfig),重点:消息类(QQ/微信)、剪贴板、Dock、Wallpaper Engine 类

## 四、验证方法(重要教训)

**坑:`IsWindowVisible(Shell_TrayWnd)` 对自动隐藏的任务栏恒为 TRUE** —— auto-hide 的任务栏不是"隐藏窗口",而是**滑出屏幕外**(只留 ~2px 触发线)。用窗口可见性 API 判断会得出"一直可见"的错误结论(本次排查初期即被误导)。

**正确检测:GetWindowRect 对比屏幕高度**。屏幕高 864 时,隐藏态任务栏 rect top≈862,屏内可见部分 ≤2px;鼠标移到底部弹出时可见 48px。完整闭环验证脚本(见附录)。

## 五、附录:验证脚本(核心逻辑)

```powershell
# 鼠标移到底部 -> 应弹出;移到中央 -> 应隐藏。检测任务栏在屏内可见像素。
# 关键:GetWindowRect + 屏幕高对比,勿用 IsWindowVisible
Add-Type @"
using System; using System.Runtime.InteropServices;
public class TB {
  [DllImport("user32.dll")] public static extern IntPtr FindWindow(string c, string n);
  [DllImport("user32.dll")] public static extern bool GetWindowRect(IntPtr h, out RECT r);
  [DllImport("user32.dll")] public static extern bool SetCursorPos(int x, int y);
  [DllImport("user32.dll")] public static extern int GetSystemMetrics(int i);
  [StructLayout(LayoutKind.Sequential)] public struct RECT { public int Left, Top, Right, Bottom; }
}
"@
$h = [TB]::FindWindow('Shell_TrayWnd', $null)
$scrH = [TB]::GetSystemMetrics(1); $scrW = [TB]::GetSystemMetrics(0)
# 鼠标到底部 -> 应弹出
[TB]::SetCursorPos([int]($scrW/2), $scrH - 2); Start-Sleep 2
$r = New-Object TB+RECT; [TB]::GetWindowRect($h, [ref]$r) | Out-Null
Write-Output ("bottom hover visible px: " + ($r.Bottom - [Math]::Max($r.Top,0)))
# 鼠标到中央 -> 应隐藏
[TB]::SetCursorPos([int]($scrW/2), [int]($scrH/2)); Start-Sleep 3
[TB]::GetWindowRect($h, [ref]$r) | Out-Null
$vis = [Math]::Max(0, [Math]::Min($r.Bottom, $scrH) - [Math]::Max($r.Top, 0))
Write-Output ("center visible px: " + $vis + " (<=2 = hidden OK)")
```

## 六、备查

- 自动隐藏开关注册表位置:`HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\StuckRects3` 的 `Settings` 二进制,**byte[8]**:3=自动隐藏开 / 2=关;byte[12]:任务栏位置(0左 1上 2右 3下)。改后需重启 explorer,但见上:状态机卡住时改注册表无效,要走设置 UI。
- 已知相关 bug(25H2,社区反馈):auto-hide 触发区被最大化窗口遮挡(DWM z-order,部分 build);任务栏高度异常(切换主显示器后 61px 卡住,ExplorerPatcher 相关 issue)。如遇触发区被遮而非不隐藏,属另一 bug。
- 本机该问题已通过设置 UI toggle 修复,闭环验证通过(底部弹出 48px / 中央隐藏 2px)。

## 相关与复习

- [[Windows内存与磁盘优化记录-2026-09]] —— 同批系统维护;注意优化工具(Win11Debloat 类)别误关任务栏/explorer 相关项
- 排查中停掉的第三方(QQ/微信/Ditto/PixPin/Wallpaper Engine)已恢复;Wallpaper Engine 需从 Steam 手动启动
