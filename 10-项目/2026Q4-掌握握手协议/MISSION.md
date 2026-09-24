# Mission: 握手协议链路(TCP → TLS 1.3 → WebSocket → QUIC)

> `teach` 教学工作区协议文件,与 [项目说明](<./!项目说明.md>) 配套(项目说明管任务与进度,本文件管「为什么学」)。
> 教学决策(下节教什么、给哪些资源、设计什么练习)都回到这份文件上。

## Why

边缘函数工程师知识树的第一支柱是连接层:请求怎么建立连接、怎么加密、怎么升级、怎么在 QUIC 上省掉往返。把这条链路讲通,后面看边缘运行时、CDN 分发、0-RTT 这些概念才有落脚点。

## Success looks like

- 能用 Wireshark 逐帧指出:TCP 三次握手 / TLS ClientHello 与证书协商 / HTTP 101 协议切换 / QUIC 0-RTT
- 能口述一条完整链路:从 DNS 到 TLS 完成再到应用数据,每步发生了什么、几次往返
- 能讲清「为什么 QUIC 快」:0-RTT、连接迁移、队头阻塞的差异
- 留下抓包文件与标注(可复现的证据,而不是笔记里的示意图)

## Constraints

- 窗口 —— → 2026-12-31;当前状态:未开始
- 环境:本机 Windows + Wireshark;需要能抓到真实流量(浏览器 + 本地服务)
- 以 RFC 原文为准,博客只做辅助

## Out of scope

- 不做协议实现(不写 TLS 库、不实现 QUIC)
- 不深入密码学数学原理(只到「握手在协商什么」)
- 不学 HTTP/2 与 HTTP/3 的全部细节,只到握手与连接层

---

配套文件:[RESOURCES.md](<./RESOURCES.md>)(资源与社群)· [NOTES.md](<./NOTES.md>)(教学偏好)· `lessons/`(课程)· `reference/`(速查卡)· `learning-records/`(学习记录,按需创建)
