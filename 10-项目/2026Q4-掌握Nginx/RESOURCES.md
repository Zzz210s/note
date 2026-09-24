# Nginx(静态服务 / 反向代理 / 负载均衡) Resources

> 本项目教学资源的唯一清单:解释性知识只从 Knowledge 取材,不凭模型记忆。
> 校验:2026-09-24 用 curl 逐个探测(200 正常;403 是站点反爬,浏览器可正常访问)。

## Knowledge

- [Nginx 官方文档](https://nginx.org/en/docs/)
  指令与模块的权威定义,`nginx.conf` 里每个词都能在这里查到。用在:配置项存疑时
- [官方 Beginner's Guide](https://nginx.org/en/docs/beginners_guide.html)
  官方入门:静态服务、反向代理、FastCGI 三件事。用在:第一次配通链路
- [NGINX 官方文档站(docs.nginx.com)](https://docs.nginx.com/)
  商业版与官方教程集合,含常见架构模式。用在:负载均衡与 TLS 配置范例

## Wisdom (Communities)

- (暂无 —— 本项目暂不需要外部社群;遇到问题优先查官方文档与 issue 区)

## Gaps

- 502/504 排查的「症状 → 成因」速查表需要在实践中自己整理成 reference
