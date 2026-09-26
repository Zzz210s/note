---
type: concept
tags: [Linux, 图形界面, Wayland, X11, 显示服务器, WSLg, 概念辨析]
status: done
date: 2026-09-26
related: "[[CLI,TUI,GUI三种界面的区别]]"
---

# Wayland

> Linux 桌面上换了十年的那一层:以前是 X11(准确说是 Xorg),现在越来越多发行版默认 Wayland。
> 它换来什么、代价是什么?最直观的检查点是你手里的工具 —— **截图、录屏、全局快捷键、远程桌面**
> 这四类在 Wayland 下几乎都要换一套,原因不在工具写得差,而在协议本身的分工变了。
> **本文的固定写法**:每个概念按「**为解决什么痛点而生 / 一句话定义 / 大白话注解**」三段给出,再展开细节。
> 关联阅读:[CLI,TUI,GUI三种界面的区别](<CLI,TUI,GUI三种界面的区别.md>)、课程
> [0010 · Wayland](../lessons/0010-Wayland.html)。

---

## 一句话速览

| 名称 | 一句话定义 | 大白话注解 |
| --- | --- | --- |
| **Wayland** | **合成器与客户端之间的协议**:合成器把输入事件发给客户端,客户端把渲染好的**缓冲区**交回来 | 一份"谁负责画、谁负责显示"的分工约定,不是一个程序 |
| **合成器(compositor)** | 在 Wayland 里**它就是显示服务器**:管输入、管窗口、把各窗口的缓冲合成一屏 | 既是导演又是放映员 |
| **X11 / Xorg** | 上一代的显示服务器:X 服务端管输入、管前缓冲与显示,客户端通过它画、也通过它收事件 | 中间多站了一个人 |
| **Xwayland** | 让只认 X11 的老程序跑在 Wayland 合成器里的兼容层 | 给老程序配的翻译 |
| **xdg-desktop-portal** | 桌面能力的"申请窗口":截图、录屏、全局快捷键、远程桌面都要经过它 | 想动别人的窗口,先递申请 |

**一句话判定**:问「**谁在画窗口内容、谁在管输入与显示**」——X11 里客户端把渲染请求交给 X 服务端、
由它管前缓冲;Wayland 里客户端自己画进缓冲区,合成器只负责合成与显示,并直接收发输入。

---

## 一、两个词各指什么

### X11:客户端画、服务端管,但中间多了一层

> **为解决什么痛点而生**:上世纪八十年代,一台机器要跑图形程序,得有人统一管显示硬件、键盘鼠标,
> 还得让程序能**跨网络**把画面送到另一台机器上。于是有了"显示服务器 + 客户端"这套架构。
> **一句话定义**:X11 里,**X 服务端**掌管输入设备、前缓冲与显示模式;客户端把渲染请求发回服务端,
> 服务端再落到硬件([Wayland: Architecture](https://wayland.freedesktop.org/architecture.html))。
> **大白话注解**:你在窗口里看到的每个像素,都要经过服务端这一站;它还要替客户端判断"这次点击该给谁"。
> 麻烦在于:**合成器把窗口缩放、旋转之后,X 服务端并不知道**,它算出来的窗口位置是旧的
> ([同上](https://wayland.freedesktop.org/architecture.html))。

### Wayland:客户端自己画,合成器当显示服务器

> **为解决什么痛点而生**:X 服务端变成了"中间人"—— 内核已经有了 KMS、evdev,库也有了 mesa、cairo、Qt,
> 服务端既不懂场景变换,又替所有人管前缓冲,于是每一帧都多几次上下文切换。
> **一句话定义**:Wayland 是**合成器与客户端之间的协议**:合成器直接接管 KMS 与输入设备,
> 客户端自己渲染进**共享的显存缓冲区**,只把"哪块区域更新了"告诉合成器,由合成器合成后直接排一次翻页
> ([Wayland: Architecture](https://wayland.freedesktop.org/architecture.html))。
> **大白话注解**:谁的程序谁自己画,画完把成品交上去;输入事件由合成器直接发给你 ——
> 它知道每个窗口被怎么摆过,所以坐标换算得对。官方 FAQ 的原话最清楚:「合成器把输入事件发给客户端,
> 客户端在本地渲染,再把显存缓冲区与更新信息交回合合成器」
> ([Wayland FAQ](https://wayland.freedesktop.org/faq.html))。

### 一个常被忽略的差别:Wayland 只是个协议

Arch Wiki 的第一句话就点明了:「**Wayland 只是协议,不像 Xorg 那样有一个统一的"显示服务器"可以装**;
要用它,你只需要一个兼容的显示驱动和一个实现 Wayland 协议的合成器或桌面环境」
([Arch Wiki: Wayland](https://wiki.archlinux.org/title/Wayland))。
这就是"换到 Wayland"在不同发行版体感不同的原因:GNOME 用 Mutter、KDE 用 KWin、
wlroots 系(Sway / Hyprland / labwc)各自一套,**截图这类能力的实现跟着合成器走**。

---

## 二、对比表

| 维度 | X11(Xorg) | Wayland |
| --- | --- | --- |
| 谁画窗口内容 | 客户端把渲染请求交给 X 服务端,由它驱动硬件;也支持客户端直接渲染到共享缓冲 | 客户端自己画进缓冲区,把缓冲区交给合成器 |
| 谁管前缓冲与显示模式 | X 服务端 | 合成器(合成后直接排页翻转) |
| 谁能准确判断"这次点击给哪个窗口" | X 服务端,但它不知道合成器施加的缩放 / 旋转 | 合成器:它自己维护场景树,会做逆变换 |
| 网络透明 | 原生支持(X 协议能跑在网络之上,`DISPLAY=主机:0`) | **不支持**:官方 FAQ 明确说远程渲染不在协议范围内 |
| 客户端能读别人的画面吗 | 能 —— 通用截图 / 抓屏工具就建立在这条上 | 默认不能:缓冲区是私有的,要经合成器或门户 |
| 全局快捷键 / 键盘抓取 | 客户端可以直接抓 | 要经 `xdg-desktop-portal` 的 GlobalShortcuts |
| 谁来兼容老程序 | 本身就是 X11 | 靠 **Xwayland** |

关于网络那一行,原文只有一句但很硬:「**Is Wayland network transparent / does it support remote rendering? No,
that is outside the scope of Wayland**」([Wayland FAQ](https://wayland.freedesktop.org/faq.html))。
这不是没做,而是刻意不做 —— 作者说正是不去做这件事,Wayland 才可能这么简单。

---

## 三、这四类工具为什么会"坏掉"

这是用户最容易踩到的部分。不是工具写错了,是**它依赖的那条通路在 Wayland 里被换掉了**。

| 能力 | X11 下的常规做法 | Wayland 下为什么不行 / 怎么换 |
| --- | --- | --- |
| **截图** | 通用工具直接向服务端要整屏像素(`xwd`、`import`、`maim`、`scrot` 都是这条路) | 客户端读不到别的程序的缓冲区,于是工具按合成器分家:wlroots 系用 `grim`,GNOME 用自带 / 需 GDBus,Plasma 用 Spectacle([Arch Wiki: Screen capture](https://wiki.archlinux.org/title/Screen_capture)) |
| **录屏 / 屏幕共享** | 一个程序抓屏 + 编码就行 | 要经 **ScreenCast 门户**拿一条流(底层常是 PipeWire),再交给编码器;浏览器里的共享也走这条([XDG Desktop Portal: ScreenCast](https://flatpak.github.io/xdg-desktop-portal/docs/doc-org.freedesktop.portal.ScreenCast.html)) |
| **全局快捷键** | 客户端直接抓键盘(grab) | 抓不到别人的输入,要经 **GlobalShortcuts 门户**向桌面申请组合键([XDG Desktop Portal: Global Shortcuts](https://flatpak.github.io/xdg-desktop-portal/docs/doc-org.freedesktop.portal.GlobalShortcuts.html)) |
| **远程桌面** | X 协议自带网络透明,`ssh -X` 就能"把窗口送过来" | 协议层没有远程这一说;要么合成器自己实现 RDP / VNC(如 [wayvnc](https://github.com/any1/wayvnc)),要么走 **RemoteDesktop 门户**([XDG Desktop Portal: RemoteDesktop](https://flatpak.github.io/xdg-desktop-portal/docs/doc-org.freedesktop.portal.RemoteDesktop.html)) |

一句话:**Wayland 把"谁有权看别人的画面、谁有权收别人的按键"这件事交给了合成器与门户**。
少了任意抓取的自由,换来的是"任何程序都能偷偷录屏 / 记键盘"这条老路被堵上。

---

## 四、本机实例:WSLg 就是一个活的 Wayland 实现(2026-09-26 实测)

在 Windows 上跑 Linux 图形程序靠 WSLg([microsoft/wslg](https://github.com/microsoft/wslg) ·
[Microsoft Learn: Run Linux GUI apps with WSL](https://learn.microsoft.com/en-us/windows/wsl/tutorials/gui-apps))。它不是魔改 X11,而是**在 WSL 里跑一个 Wayland 合成器,再把画面用 RDP 送回 Windows**。
本机 `ls /mnt/wslg` 与合成器日志(原样照抄):

```bash
$ wsl.exe -e bash -lc "ls /mnt/wslg"
distro  doc  pulseaudio.log  PulseAudioRDPSink  PulseAudioRDPSource  PulseServer
run  runtime-dir  stderr.log  versions.txt  weston.log  wlog.log

$ wsl.exe -e bash -lc "head -6 /mnt/wslg/weston.log"
Date: 2026-09-26 CST
[17:22:33.030] weston 9.0.0
               https://wayland.freedesktop.org
[17:22:33.030] Command line: /usr/bin/weston --backend=rdp-backend.so --modules=wslgd-notify.so --xwayland --socket=wayland-0 --shell=rdprail-shell.so --log=/mnt/wslg/weston.log
```

**一行命令行就把这节课三件事说完了**:`--socket=wayland-0` 是 Wayland 协议通道,
`--xwayland` 给只认 X11 的老程序留了兼容层,`--backend=rdp-backend.so` 是画面出口(把合成结果用 RDP 送回 Windows)。
`versions.txt` 记的是 WSLg 1.0.71、weston 9.0.0、mesa 与 pulseaudio 各自的构建号。

再看这个通道到底是什么东西:

```bash
$ wsl.exe -e bash -lc "ls -l /run/user/0/wayland-0; ss -xl | grep wayland; ss -tln | grep -c ':6000 '"
lrwxrwxrwx 1 root root 31 Sep 26 17:23 /run/user/0/wayland-0 -> /mnt/wslg/runtime-dir/wayland-0
u_str LISTEN 0 128 /mnt/wslg/runtime-dir/wayland-0 16391 * 0
0
```

读法:Wayland 的通道是**一个 unix 域套接字**(`u_str`,文件系统里的一根"管子"),不是网络端口;
而 X11 默认连 TCP 6000 都没开(`grep -c` 的结果是 0),但也听在 `/tmp/.X11-unix/X0` 上 —— 两套通道同时存在,
正是"Wayland 主体 + Xwayland 兜底"的样子。环境变量也对得上:

```bash
$ wsl.exe -e bash -lc "echo \$XDG_SESSION_TYPE; echo \$WAYLAND_DISPLAY; echo \$DISPLAY; ls /usr/share/wayland-sessions"
                                    # XDG_SESSION_TYPE:空
wayland-0
:0
                                    # 会话清单:空
```

**诚实边界**:`XDG_SESSION_TYPE` 是空的 —— WSL 里这不是一次图形登录会话(`loginctl` 只有 `user-early` 级别的记录),
`/usr/share/wayland-sessions` 也没有桌面条目;`wayland-info` / `grim` / `wl-copy` 这些客户端工具本机都没装,
所以这节课不现场演示抓屏。但 WSLg 本身是**货真价实的 Wayland 实现**:有合成器、有 wayland-0 套接字、有客户端在跑。

---

## 五、常见误解

| 说法 | 问题在哪 | 更准的说法 |
| --- | --- | --- |
| 「Wayland 是另一个显示服务器」 | 它本身只是一份协议,没有可安装的"Wayland 服务端" | 装的是**合成器**(Mutter / KWin / Sway / Weston…) |
| 「Wayland 更快是因为优化得好」 | 结构上少了一层:X 服务端原本夹在客户端与合成器之间 | 客户端直接渲染、合成器直接排页翻转 |
| 「Wayland 下截不了屏」 | 老一套工具确实不行,但合成器与门户提供了新路 | 换成该合成器支持的工具,或让程序走 ScreenCast / Screenshot 门户 |
| 「`ssh -X` 在 Wayland 上一样好用」 | 协议明确不支持远程渲染 | 远程要整屏/整桌面的方案(RDP / VNC / 门户),不是"把单个窗口送过来" |
| 「Wayland 下全局快捷键没法做了」 | 只是不能"偷偷抓" | 走 GlobalShortcuts 门户,由用户同意后注册 |
| 「用 Xwayland 就等于还在 X11 里」 | 兼容层只让老程序显示出来 | 它显示的窗口同样要经合成器合成;画法仍是老路 |

---

## 六、和相邻术语的关系

| 术语 | 一句话定义 | 与 Wayland 的关系 |
| --- | --- | --- |
| **显示服务器** | 管输入设备、窗口与显示的常驻程序 | X11 里是 X 服务端;Wayland 里这个角色由合成器兼任 |
| **窗口管理器 / 合成器** | 决定窗口怎么摆、并把它们合成成一屏 | Wayland 把"显示服务器"这份职责也交给了它 |
| **Xwayland** | 让 X11 客户端跑在 Wayland 合成器里的兼容层 | 过渡期的桥,本机 WSLg 就开着它 |
| **EGL / GBM** | 图形库与缓冲分配接口 | 客户端与合成器共享缓冲区靠这套([Arch Wiki: Wayland](https://wiki.archlinux.org/title/Wayland)) |
| **PipeWire** | Linux 上的音视频流服务 | 录屏 / 共享的流常由门户交给它搬运 |
| **xdg-desktop-portal** | 桌面能力的统一申请接口 | 截图 / 录屏 / 全局快捷键 / 远程桌面的新入口 |
| **RDP / VNC** | 把整屏画面送到远端的协议 | Wayland 下远程桌面的常见落地方式(本机 WSLg 用 RDP) |

**一句话总结**:X11 是「**客户端发请求、服务端画并显示**」,Wayland 是「**客户端画进缓冲区、合成器合成并显示**」;
顺带把"谁有权看别人的画面、收别人的按键"从"谁都能"改成"要经合成器或门户同意"。

---

速查卡:[Wayland 速查](../reference/Wayland速查.html)(判定表、四类工具的替代路线、本机 WSLg 原始输出、
症状反查与命令对照)· 课程:[0010 · Wayland](../lessons/0010-Wayland.html) ·
对照阅读:[CLI,TUI,GUI 三种界面的区别](<CLI,TUI,GUI三种界面的区别.md>)
