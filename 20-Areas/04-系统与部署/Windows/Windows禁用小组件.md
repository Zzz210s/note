---
type: knowledge
tags: [windows, 小组件, widgets, webexperiencepack, 性能优化]
status: done
date: 2026-09-04
related: "[[UAC-管理员软件免弹窗]]"
---

# Windows 11 禁用小组件(Widgets)教程

> 适用:Win11 任务栏小组件后台常驻(Widgets.exe + 一堆 msedgewebview2 子进程),想彻底禁用腾资源。
> 实测背景:2026-09-04,Windows 11 build 26200(ELEVEN237038),小组件及其 webview2 共约 6~7 个进程;进程清理优化时一并处理。

## 一、为什么禁

小组件不只是任务栏一个图标:它常驻 `Widgets.exe`,并拉起多个 `msedgewebview2.exe` 渲染进程(实测本机 12 个 webview2 里 6 个属于小组件 + 搜索 UI)。对不需要小组件新闻/天气/股票的人,纯属白耗内存和进程数。

## 二、方案对比

| 方案 | 做法 | 效果 | 局限 |
|---|---|---|---|
| A. 常规 | 设置关闭按钮 + HKLM 策略键 | 隐藏按钮、禁 Win+W | **Windows 26200 构建对 TaskbarDa / Dsh 键有写保护**——即使管理员提权 + FullControl ACL,reg.exe / .NET 一律"拒绝访问"(见下) |
| B. 卸载应用包(推荐) | 移除 Web Experience Pack | 组件整个消失,进程无法再拉起 | 大版本功能更新可能自动重装 |

**结论:直接走方案 B**,绕开注册表写保护,且更彻底。

## 三、方案 B 执行(需要管理员)

1. 管理员 PowerShell:开始菜单搜 PowerShell -> 右键 -> 以管理员身份运行 -> UAC 点"是"
2. 卸载小组件应用包:

```powershell
Get-AppxPackage *WebExperience* | ForEach-Object { Remove-AppxPackage $_.PackageFullName }
```

3. 立即清掉现存进程(可选,卸载后 Widgets 通常已退出):

```powershell
Stop-Process -Name Widgets -Force -ErrorAction SilentlyContinue
```

## 四、验证

```powershell
(Get-AppxPackage *WebExperience*).Count   # 0 = 已卸载
Get-Process Widgets -ErrorAction SilentlyContinue   # 无输出 = 未运行
```

实测:webview2 进程 12 -> 6(余下的属于 Windows 搜索 SearchHost 等,正常)。

## 五、恢复

- 去 Microsoft Store 搜索并安装 **"Windows Web Experience Pack"** 即恢复
- 若某次大版本更新后又出现,重复方案 B 即可

## 六、踩坑记录:26200 注册表写保护

初版想用常规注册表方案,发现 `HKCU\...\Explorer\Advanced` 的 `TaskbarDa` 与 `HKLM\SOFTWARE\Policies\Microsoft\Dsh` 的 `AllowNewsAndInterests` 写不进去:

- 进程确已提权(`whoami /groups` 显示 High Mandatory Level S-1-16-12288)
- ACL 正常(当前用户 FullControl Allow)
- 但 `Set-ItemProperty`、.NET `RegistryKey.SetValue`、`reg.exe add` 全部报"拒绝访问"(UnauthorizedAccessException)
- 该键甚至被写保护到值读出来已是目标值(TaskbarDa 本就是 0),但策略键 Dsh 无法创建

判断:新 Windows 构建对任务栏相关策略键有系统级写保护(类似受管注册表),普通提权也不放行。**别在这上面耗时间,卸载应用包才是正解。**
