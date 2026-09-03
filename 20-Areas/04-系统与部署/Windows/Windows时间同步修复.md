# Windows 时间同步修复(w32time)

> 适用:系统时间与真实时间偏差(本机实测曾慢 21 分钟,根因 w32time 服务停止)。
> 时间源建议用国内 NTP(aliyun/tencent),`time.windows.com` 在中国大陆常不可达。

## 一、诊断

```powershell
# 1) 本地时间 vs 网络真实时间(HTTP Date 头是权威 UTC)
date            # 本地
curl -sSI https://registry.npmjs.org/ | findstr /i date   # 真实时间(GMT)

# 2) 时间服务状态(Stopped = 根因)
Get-Service w32time
w32tm /query /status
```

- 偏差量化:本地时间与 Date 头的 UTC+8 换算后对比
- `w32tm /query /status` 显示 `Leap 指示符: 3(未同步)` = 从未同步成功

## 二、修复(管理员 PowerShell)

> 普通进程无法配置时间服务(即使账户在 Administrators 组也受 UAC 令牌过滤)。
> 必须:开始菜单搜 PowerShell -> 右键 -> **以管理员身份运行** -> UAC 弹窗点"是"。
> 验证已提权:`net session`(报错=未提权)。

```powershell
# 1) 启动时间服务
net start w32time

# 2) 配置国内 NTP 源(逐条粘贴,长命令易被 PSReadLine 折行断成两截)
w32tm /config /manualpeerlist:"ntp.aliyun.com,0x1"
w32tm /config /syncfromflags:manual /update

# 3) 立即同步
w32tm /resync

# 4) 设开机自启(注意 start= 后有空格)
sc config w32time start= auto
```

## 三、验证

```powershell
w32tm /query /status
```

同步成功标志:
- `源: ntp.aliyun.com,0x1`
- `层次: 3`(或 2),`Leap 指示符: 0`(无警告)
- 偏差 < 1 秒

## 四、踩坑记录

| 坑 | 现象 | 原因 |
|---|---|---|
| 提权无效 | `Set-Service` 报拒绝访问 | 账户在管理员组但进程未过 UAC(需右键以管理员运行 + 弹窗点"是") |
| 长命令断行 | config 命令折成两截各自报错 | PowerShell 粘贴长行被 PSReadLine 换行;拆短命令逐条贴 |
| resync 无数据 | "没有可用的时间数据" | NTP 源未配置成功,先完成 config 两步再 resync |
| 多行粘贴混乱 | 把错误信息文本也贴进去当命令执行 | 一次只贴一条命令,不贴任何非命令文本 |
