---
type: tutorial
tags: [windows, 右键菜单, cmder, windows-terminal, 注册表, 资源管理器]
status: done
date: 2026-09-05
related: "[[Cmder]]"
---

# Windows 右键菜单:Cmder 与终端(紧靠,终端下跑 cmder 环境)

> 适用:想让资源管理器右键(文件夹空白处 / 文件夹图标上)出现"在 Cmder 中打开"与"在终端中打开"两项、彼此紧靠;其中"在 Cmder 中打开"实际打开的是 **Windows Terminal 里的 cmder 环境**(git bash 加载 cmder 初始化),而非独立 cmder(ConEmu)窗口。
> 实测背景:2026-09-05,Win11 25H2 build 26200.9168;cmder 1.3.25(scoop 安装);Windows Terminal 1.24(系统自带)。
> 一句话本质:注册表 shell 扩展(Win11 只出现在"显示更多选项"旧菜单)+ 复用 Windows Terminal 已有 profile(`wt -p <guid> -d "%V\."`)。

## 一、最终效果

右键文件夹空白处(或文件夹图标)->"显示更多选项"(或 Shift+F10)-> 菜单底部两项紧靠:

| 菜单项 | 打开内容 | 命令 |
|---|---|---|
| 在 Cmder 中打开 | Windows Terminal 的 Cmder profile(git bash + cmder 初始化),落在当前目录 | `wt.exe -p "{Cmder profile 的 guid}" -d "%V\."` |
| 在终端中打开 | Windows Terminal 默认 profile(Windows PowerShell),落在当前目录 | `wt.exe -d "%V\."` |

两个都是 Windows Terminal 窗口,外观统一,目录跟随右键位置。

## 二、原理与关键认知

1. **Win11 有两套右键菜单**:默认现代菜单 + "显示更多选项"旧菜单。注册表 shell 扩展**只进旧菜单**(现代一级菜单要第三方 IExplorerCommand 扩展,注册表做不到)。想常用就按 Shift+F10,或习惯多点一下"显示更多选项"。
2. **两个注册点**(视需求都加):
   - `HKCU\Software\Classes\Directory\shell` —— 右键文件夹图标时显示
   - `HKCU\Software\Classes\Directory\Background\shell` —— 右键文件夹空白处时显示
   - 用 **HKCU**:免提权、只影响当前用户、可逆(ContextMenuManager 等工具也能管理)。
3. **排序**:同一注册点下的项按键名二进制排序(大写字母在小写前)。要让两项"紧靠",键名用共同前缀即可,本例用 `zzOpenInCmder` / `zzOpenInTerminal`,排在该区段末尾且相邻。
4. **显示名**:键的"(默认)"值即菜单显示文本,直接用中文。
5. **不新建 WT profile**:直接 `-p <guid>` 引用 settings.json 里已有的 profile(`%LOCALAPPDATA%\Packages\Microsoft.WindowsTerminal_8wekyb3d8bbwe\LocalState\settings.json` 的 `profiles.list` 中的 guid);`-d` 目录参数会覆盖 profile 自带的 startingDirectory。

## 三、配置步骤

### 1. 准备:查 cmder 路径与 WT profile guid

```powershell
# cmder(本例 scoop 安装)
Get-Command cmder.exe | Select-Object Source   # -> C:\Users\23652\scoop\apps\cmder\current\Cmder.exe
# 若 cmder 走 Windows Terminal:找到要复用的 profile 的 guid
# 记事本打开 %LOCALAPPDATA%\Packages\Microsoft.WindowsTerminal_8wekyb3d8bbwe\LocalState\settings.json
# profiles.list 里 name 为 "Cmder · Claude" 之类的那项的 guid,如 {8ac0556a-dfaa-4100-bf4d-b80dea441451}
```

### 2. 写入注册表(PowerShell 交互窗口直接粘贴运行)

按需改三处:`$wt`(wt.exe 路径)、`$profileGuid`(你的 Cmder profile guid)、`$cmderIcon`。

```powershell
$wt          = 'C:\Users\23652\AppData\Local\Microsoft\WindowsApps\wt.exe'
$profileGuid = '{8ac0556a-dfaa-4100-bf4d-b80dea441451}'   # 你的 Cmder profile
$cmderIcon   = 'C:\Users\23652\scoop\apps\cmder\current\Cmder.exe'
$targets = 'Directory\shell','Directory\Background\shell'
foreach ($t in $targets) {
  $b = "HKCU:\Software\Classes\$t"
  # 在 Cmder 中打开
  New-Item -Path "$b\zzOpenInCmder\command" -Force | Out-Null
  Set-ItemProperty -Path "$b\zzOpenInCmder" -Name '(default)' -Value '在 Cmder 中打开'
  Set-ItemProperty -Path "$b\zzOpenInCmder" -Name 'Icon' -Value $cmderIcon
  Set-ItemProperty -Path "$b\zzOpenInCmder\command" -Name '(default)' -Value ('"{0}" -p "{1}" -d "%V\."' -f $wt, $profileGuid)
  # 在终端中打开
  New-Item -Path "$b\zzOpenInTerminal\command" -Force | Out-Null
  Set-ItemProperty -Path "$b\zzOpenInTerminal" -Name '(default)' -Value '在终端中打开'
  Set-ItemProperty -Path "$b\zzOpenInTerminal\command" -Name '(default)' -Value ('"{0}" -d "%V\."' -f $wt)
}
```

> 提示:把上面存成 .ps1 文件再跑的话,含中文需存 **UTF-8 带 BOM**,否则 PS5.1 会按 GBK 读导致乱码;直接粘贴到 PowerShell 窗口无此问题。

### 3. 验证

- `reg query "HKCU\Software\Classes\Directory\Background\shell\zzOpenInCmder\command" /ve` 应看到命令以 `%V\.` 结尾
- 打开任意文件夹右键:普通目录、**盘根目录(F:\)**、含空格目录都点一遍两项,确认能开且目录正确

## 四、坑(实测)

1. **`"%V"` 尾部反斜杠转义 bug**:目录以 `\` 结尾(如盘根 `F:\`)时,命令 `-d "F:\"` 末尾的 `\` 会转义闭合引号,wt 收到畸形路径,报 `0x8007010b`(无法访问启动目录 "F:\"")。**解法:写成 `"%V\."`**(`F:\.` 语义等同 F:\,反斜杠不再贴引号)。非根目录不触发,所以只在盘根右键时才暴露。
2. **Win11 现代菜单看不到这些项**:它们是经典注册表项,只出现在"显示更多选项"/Shift+F10。想进现代一级菜单需额外扩展(如 Nilesoft Shell),本方案不引入。
3. **改完右键没出现**:explorer 缓存,重启资源管理器(或注销)即可。
4. **顺序跑偏**:其他工具也会往同一父键写项;想让两项保持紧靠,键名公共前缀别动;若想整体置顶/置底,改前缀字母段即可(二进制序,大写在前)。
5. **wt 已开着的窗口**:从右键调 wt 默认在当前 WT 窗口新开标签;要独立窗口,WT 设置 -> 启动 -> "新实例行为" 改"新窗口"。

## 五、撤销

```powershell
foreach ($t in 'Directory\shell','Directory\Background\shell') {
  Remove-Item -Recurse -Force "HKCU:\Software\Classes\$t\zzOpenInCmder"
  Remove-Item -Recurse -Force "HKCU:\Software\Classes\$t\zzOpenInTerminal"
}
```

## 相关与复习

- [[Cmder]] —— cmder 的安装/环境变量/注册说明(命令行工具目录)
- [[Windows禁用小组件]] —— 同类资源管理器/系统定制主题
- [[Windows内存与磁盘优化记录-2026-09]] —— 同批机器维护;注意别让优化把 wt/cmder 的启动项误伤
