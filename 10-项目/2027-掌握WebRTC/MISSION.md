# Mission: WebRTC(实时音视频与数据通道)

> `teach` 教学工作区协议文件,与 [项目说明](<./!项目说明.md>) 配套(项目说明管任务与进度,本文件管「为什么学」)。
> 教学决策(下节教什么、给哪些资源、设计什么练习)都回到这份文件上。

## Why

WebRTC 是「浏览器之间直连」的标准答案:它把 NAT 穿透、编解码协商、加密传输全部包进浏览器。对海外销售/售前这条线,它是能当场演示、也能讲清原理的技术作品素材。

## Success looks like

- 两个浏览器页面通过 `RTCPeerConnection` 打通音视频(或数据通道),本地可复现
- 能讲清信令 / ICE / STUN / TURN 各自解决什么问题,以及为什么需要信令服务器
- 能读懂 SDP 里关键字段(编解码、ICE 候选)在说什么
- 留下可展示的 demo 与原理说明(不是只跑通一次)

## Constraints

- 窗口 —— → 2026-12-31;当前状态:未开始
- 环境:本机浏览器 + Node.js(写最小信令服务)
- 最小可用优先:先跑通官方 Codelab,再改

## Out of scope

- 不深入音视频编解码实现(H.264/VP8 只到知道差别)
- 不做 SFU/MCU 媒体服务器(如 mediasoup/LiveKit)
- 不做生产级信令与鉴权

---

配套文件:[RESOURCES.md](<./RESOURCES.md>)(资源与社群)· [NOTES.md](<./NOTES.md>)(教学偏好)· `lessons/`(课程)· `reference/`(速查卡)· `learning-records/`(学习记录,按需创建)
