---
type: troubleshooting
tags: [windows, 跨设备, crossdevice, 手机连接, 网络发现, mDNS, 网络配置文件, 计划任务, throne, sing-box]
status: done
date: 2026-10-02
related: "[[Windows任务栏自动隐藏失效修复-2026-09]]"
---

# 记录:CrossDevice Files 报「手机处于脱机状态」修复

> 症状:文件资源管理器左侧「跨设备」显示 **Zzz210s 处于脱机状态** —— 提示"请确保你的移动设备已打开并连接到与电脑相同的 Wi-Fi 网络"。手机本身正常(蓝牙已配对、同网段),**是 Windows 侧的问题**;而且"之前出现过",会复发。
> 结论:**根因是 Windows 把 WLAN 判定为「公用网络」** —— 公用网络上 mDNS/网络发现被禁用,跨设备的局域网发现因此失败。已修复,并加了常驻守卫防止复发。

## 一、症状与影响面

| 项 | 内容 |
|---|---|
| 报错位置 | 文件资源管理器 → 「跨设备」(CrossDevice Files) |
| 报错文案 | `<设备名> 处于脱机状态。请确保你的移动设备已打开并连接到与电脑相同的 Wi-Fi 网络` |
| 手机侧状态 | **正常** —— 蓝牙配对 OK(设备名「210的呼噜声」)、与电脑同网段(`10.29.0.0/17`) |
| 特征 | **间歇性、会复发**(不是一次性故障) |

## 二、排查过程(证据链)

按「先定位根因,再动手」的顺序做,关键证据如下。

### 1. 组件边界逐层检查

| 组件 | 检查结果 |
|---|---|
| CrossDevice 进程 | `CrossDeviceService` / `PhoneExperienceHost` / `CrossDeviceFilesHost` 都在跑;`MicrosoftWindows.CrossDevice v1.26072.116.0` 状态 Ok |
| 蓝牙配对 | 手机已配对(OK) |
| 事件日志 | 近 24 小时**无** CrossDevice/PhoneExperience 相关错误 |
| 防火墙 | **没有任何** CrossDevice 相关规则 |
| **网络配置文件** | **WLAN = Public(公用)** ← **决定性证据** |
| CrossDevice 的连接 | 走代理(`198.18.0.64:443`,即 Throne TUN 的 fake-IP) |

### 2. 对照已知原因(官方 + 社区)

- **微软官方**:文件共享与设备发现**只在「专用网络」上工作**;Nearby Sharing 同样要求 Private
- **技术分析**(讲"连接至 Windows"协议握手的那篇):① **虚拟网卡(VPN/Docker)抢占广播路由** ② **「公用/专用」直接决定 mDNS 发现协议的生死** —— 两条都命中本机情况

### 3. 根因

> **Windows 把 WLAN 判为「公用网络」→ mDNS/网络发现被禁用 → CrossDevice 的局域网发现失败 → 报"脱机"。**
> 复发原因:Windows 会在**驱动更新 / 网络重置 / 换网络**后把 Wi-Fi **重新判回「公用」**,所以同一个 bug 反复出现。

## 三、修复(实测有效)

| 项 | 改动前 | 改动后 |
|---|---|---|
| **WLAN 网络配置文件** | 公用 | **专用** |
| 文件与打印机共享(防火墙) | 0 条规则启用 | **10 条启用** |
| 网络发现(防火墙) | 22 条 | 22 条(本就启用) |
| SSDPSRV / upnphost | Running / Stopped | Running / **Running** |
| CrossDevice 栈 | — | 重启一次,让发现重跑 |

**验证**:用户确认「连接成功」;文件资源管理器的「跨设备」不再报脱机。

**手动复现/自查命令**:

```powershell
# 看当前网络配置文件(公用 = 会出问题)
Get-NetConnectionProfile | Select-Object InterfaceAlias, NetworkCategory

# 改回专用(需管理员)
Set-NetConnectionProfile -InterfaceAlias WLAN -NetworkCategory Private

# 确认发现/共享的防火墙规则是否打开(按组 ID,显示名是本地化的)
Get-NetFirewallRule -Group '@FirewallAPI.dll,-32752' | Where-Object Enabled -eq 'True' | Measure-Object
Get-NetFirewallRule -Group '@FirewallAPI.dll,-28502' | Where-Object Enabled -eq 'True' | Measure-Object
```

## 四、持久化守卫(防复发)

**任务 `CrossDeviceNetGuard`**(以 SYSTEM / 最高权限运行)

| 项 | 值 |
|---|---|
| 触发器 | **登录时** + **每 15 分钟** |
| 动作 | `powershell.exe -NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass -File C:\ProgramData\crossdevice-guard.ps1` |
| 脚本 | `C:\ProgramData\crossdevice-guard.ps1` |
| 日志 | `C:\ProgramData\crossdevice-guard.log` |

脚本做两件事:① WLAN 若被改回「公用」→ 改回**专用**;② 把发现/共享的防火墙规则重新打开。

**实测**:手动触发一次 → 返回码 **0**,日志记录 `no change needed (WLAN already Private, rules enabled)`。

> **注意**:以 SYSTEM 身份注册的计划任务,**在非管理员上下文里用 `Get-ScheduledTask` 可能查不到**(会显示"任务不存在")。核对时要用**管理员**终端,否则会误判成"任务丢了"。

## 五、顺带修复:Throne 的进程直连规则对 MSIX 应用不生效

排查中发现另一个独立问题:此前为 PhoneLink 进程加的**直连规则没有命中** —— 日志显示 `CrossDeviceService` / `PhoneExperienceHost` 的流量**仍走代理**,而**卡巴斯基的同类规则是生效的**:

```
router: found process path: C:\Program Files\WindowsApps\MicrosoftWindows.CrossDevice_...\CrossDeviceService.exe
  → outbound/vless[proxy]          ← 规则没生效
router: found process path: C:\Program Files (x86)\Kaspersky Lab\Kaspersky 21.26\avp.exe
  → outbound/direct[direct]        ← 规则生效
```

**差异**:这两个进程运行在 `C:\Program Files\WindowsApps\...`(**MSIX 打包应用**),`process_name`(可执行文件名)匹配不上。

**修法**:改用 **`process_path` 通配** —— 在 Throne 的 `route_rules` 里新增一条(排在代理规则之前):

```
name: PhoneLink paths -> direct
outbound_id: -2 (direct)
process_path_json: ["*\\CrossDeviceService.exe", "*\\CrossDeviceFilesHost.exe",
                    "*\\CrossDeviceResume.exe", "*\\PhoneExperienceHost.exe",
                    "*\\YourPhoneAppProxyHost.exe"]
```

**效果(实测)**:CrossDevice/YourPhone 的 8 条连接中 **6 条转为直连**(含关键的 `dcg.microsoft.com`、`signalr` relay),此前是 **0 条**。

**教训**:在 Windows 上给 **MSIX/UWP 打包应用**做进程级分流,用 `process_path` 通配比 `process_name` 可靠。

## 六、本机上与 CrossDevice 相关的另一个守卫(注意别混淆)

任务 **`CrossDeviceGuard`**(2026-09-03 建立,用户权限)在 `C:\Users\23652\guard-crossdevice\`,治的是**另一个症状**:

- 监控 `CrossDeviceService` 的 **CPU 占用**,若持续 >30%(空转重试循环)就 `taskkill`
- 与本文的守卫**不冲突**(一个管网络配置文件,一个管进程空转)
- **已知缺陷**:该任务最近一次执行结果是 `2147946720`(= "操作员或管理员拒绝了请求")—— 以普通权限调 `taskkill` 会被拒,因此**大部分时候没生效**;若要它真正工作,需要把任务改为**最高权限**

## 九、复发与第二次修复(2026-10-02 深夜)

修好约 1 小时后**再次出现同样的"脱机"**。这次按调试规范逐项排除,结论是:**根因不同**。

### 排除过程(上次修的三个层面全部正常)

| 检查 | 结果 |
|---|---|
| WLAN 网络配置文件 | **仍是「专用」** —— 上次的根因没有复发 |
| 守卫任务 | 跑过(返回码 0),日志"无需改动" |
| 防火墙 发现/共享规则 | 10 条已启用 |
| 局域网连通性 | **能 ping 通手机**(`10.29.22.100` 可达,随机 MAC = 手机) |
| 代理分流 | 日志显示 15/21 条直连 |
| 事件日志 | 无错误 |

### 关键判据纠正(重要)

**不能用 `Get-NetTCPConnection` 判断是否走了代理** —— 开了 **fakeDNS** 时,应用连接的目标**本身就是 fake-IP**(`198.18.x.x`),无论最终走直连还是代理,socket 里看到的都是 fake-IP。

**唯一可靠的判据是代理(Throne)的日志** —— 按连接的 connID 关联"found process path"与"outbound/..."两行,才能看出真实路由。我最初就是被 socket 表象误导,得出了"全部走代理"的错误结论。

### 第二个失败模式:服务空转 + 守卫失效

- `CrossDeviceService` 实测 **CPU 累计 100+ 秒、瞬时可达 200%+ 单核**(重启后突发),即已知的**空转重试循环**
- 本机上**早就有**一个守卫 `CrossDeviceGuard`(2026-09-03 由另一次会话建立,位于 `C:\Users\23652\guard-crossdevice\`)专门治这个症状
- **但它从未生效**:任务以**普通权限**运行,`taskkill` 被系统拒绝,任务结果一直是 `2147946720`(操作员或管理员拒绝了请求)

### 第二次修复(A + B)

**A. 把守卫提到最高权限**

| 项 | 修复前 | 修复后 |
|---|---|---|
| `CrossDeviceGuard` 的 runlevel | Limited | **Highest** |
| 上次执行结果 | `2147946720`(权限被拒) | **`0`(成功)** |
| 频率 | 每 3 分钟 | 不变 |

**B. 局域网 + 微软 relay 全走直连**(两条规则,排在代理兜底规则之前)

| 顺序 | 规则 | 内容 |
|---|---|---|
| 1 | `LAN private -> direct` | `ip_is_private = 1` —— 整个局域网(含手机)直连 |
| 2 | `Microsoft relay -> direct` | `relay.communication.microsoft.com`、`dcg.microsoft.com`、`graph.microsoft.com`、`service.signalr.net`、`trafficmanager.net` |

**结果**:连接恢复 ;代理日志显示 CrossDevice 的 9 条连接中 **7 条直连**。

### 教训(这类问题的排查顺序)

在 **TUN 代理环境**下遇到"手机上显示脱机 / 局域网设备发现失败",按此顺序查:

1. **网络配置文件**是不是被 Windows 判成了「公用」(公用会禁用 mDNS 发现)
2. **进程级分流是否真的命中** —— 用**代理日志**判断,不要看 socket(见上面的判据纠正);另外 **MSIX/UWP 打包应用**要用 `process_path` 通配而不是 `process_name`
3. **服务是否空转**(CPU 异常高)—— 空转会同时导致"脱机/超时",需要一个**有足够权限**的守卫来重启它
4. 最后才是**手机侧**(蓝牙配对、同网段、App 授权)

## 七、一句话总结

**「手机脱机」不是手机的问题,是 Windows 把 Wi-Fi 判成了「公用网络」** —— 公用网络上 mDNS/网络发现被禁用,跨设备就找不到手机。改成**专用**即可;由于 Windows 会自己改回去,加了个每 15 分钟自查的守卫任务。另外给 MSIX 打包应用做代理分流要用 `process_path` 而不是 `process_name`。

## 八、来源

- 微软官方:文件共享与设备发现只在专用网络上工作 / Nearby Sharing 要求 Private:https://support.microsoft.com/en-us/windows/experience/connectivity-networking/fix-problems-with-nearby-sharing-in-windows
- 「连接至 Windows」握手失败的底层分析(虚拟网卡抢占广播路由、公用/专用决定 mDNS 生死):https://tsight.io/articles/14516218
- VPN/代理环境下局域网设备失效的路由层解析:https://tsight.io/articles/16490261
- 网络发现与文件共享需要"专用网络"(含把公用改为专用的步骤):https://blog.usro.net/zh/2025/04/fix-windows-11-network-file-sharing-issues/
