# 边缘函数(运行时原理) Resources

> 本项目教学资源的唯一清单:解释性知识只从 Knowledge 取材,不凭模型记忆。
> 校验:2026-09-24 用 curl 逐个探测(200 正常;403 是站点反爬,浏览器可正常访问)。

## Knowledge

- [Cloudflare Workers 文档](https://developers.cloudflare.com/workers/)
  边缘运行时的一手文档:路由、绑定、限制、本地开发。用在:部署与能力边界
- [Cloudflare:How Workers works](https://developers.cloudflare.com/workers/reference/how-workers-works/)
  隔离模型与调度机制的官方解释。用在:验收里「运行时如何调度执行」那一条
- [Vercel Functions 文档](https://vercel.com/docs/functions)
  另一家边缘/无服务器实现的对照。用在:横向对比运行时差异
- [cloudflare/workers-sdk(含 wrangler)](https://github.com/cloudflare/workers-sdk)
  本地开发与部署工具链源码。用在:理解 CLI 行为与调试
- [Deno(官方站点)](https://deno.com/)
  V8 Isolate 路线的另一个代表(Deno Deploy)。用在:对比隔离模型

## Wisdom (Communities)

- (暂无 —— 本项目暂不需要外部社群;遇到问题优先查官方文档与 issue 区)

## Gaps

- 冷启动的实测数据需要自己压测得到(官方只给机制解释,不给具体数字)
