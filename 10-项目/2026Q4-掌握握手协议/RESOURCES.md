# 握手协议链路(TCP → TLS 1.3 → WebSocket → QUIC) Resources

> 本项目教学资源的唯一清单:解释性知识只从 Knowledge 取材,不凭模型记忆。
> 校验:2026-09-24 用 curl 逐个探测(200 正常;403 是站点反爬,浏览器可正常访问)。

## Knowledge

- [RFC 9293(TCP)](https://www.rfc-editor.org/rfc/rfc9293.html)
  TCP 的现行标准,三次握手与状态机定义。用在:抓包对照每一帧
- [RFC 8446(TLS 1.3)](https://www.rfc-editor.org/rfc/rfc8446.html)
  TLS 1.3 握手流程与密钥派生。用在:ClientHello/证书协商那一步
- [RFC 6455(WebSocket)](https://www.rfc-editor.org/rfc/rfc6455.html)
  HTTP 101 升级与帧格式。用在:协议切换那一步
- [RFC 9000(QUIC)](https://www.rfc-editor.org/rfc/rfc9000.html)
  QUIC 传输层定义,0-RTT 与连接迁移。用在:「为什么快」那一条
- [Wireshark 官方文档](https://www.wireshark.org/docs/)
  过滤器语法与协议解析说明。用在:抓包时定位与过滤

## Wisdom (Communities)

- (暂无 —— 本项目暂不需要外部社群;遇到问题优先查官方文档与 issue 区)

## Gaps

- RFC 很长,需要自己压成一张「握手链路速查卡」放 reference —— 这正是本项目的主要产出之一
