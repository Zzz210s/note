# 代理链路(VPS 采购 → Xray 上线) Resources

> 本项目教学资源的唯一清单:解释性知识只从 Knowledge 取材,不凭模型记忆。
> 校验:2026-09-24 用 curl 逐个探测(200 正常;403 是站点反爬,浏览器可正常访问)。

## Knowledge

- [Oracle Cloud Always Free 资源文档](https://docs.oracle.com/en-us/iaas/Content/FreeTier/freetier_topic-Always_Free_Resources.htm)
  免费额度、空闲回收规则的权威口径。用在:`20-知识/免费服务器资源` 的 Oracle 一节
- [Oracle Ampere A1 免费额度说明](https://docs.oracle.com/en-us/iaas/Content/Compute/References/arm.htm)
  PAYG 与 Always Free 的 A1 额度差异。用在:判断升级 PAYG 是否值得
- [Cloudflare Workers 限制表](https://developers.cloudflare.com/workers/platform/limits/)
  免费档请求数 / CPU 时间 / 内存的官方数字。用在:边缘方案选型
- [Xray 官方文档(Project X)](https://xtls.github.io/)
  配置与协议的权威来源,含 VLESS/Reality 说明。用在:一切配置项
- [XTLS/Xray-core(主仓库)](https://github.com/XTLS/Xray-core)
  源码与 issue,新特性与踩坑都在这里。用在:官方文档滞后时
- [v2fly/v2ray-core(对照实现)](https://github.com/v2fly/v2ray-core)
  另一支实现,配置概念相通。用在:交叉验证配置写法

## Wisdom (Communities)

- (暂无 —— 本项目暂不需要外部社群;遇到问题优先查官方文档与 issue 区)

## Gaps

- 本机已有 3x-ui 面板笔记(本项目 `20-知识/`),开课时先把「面板 vs 手工配置」的取舍写清
- 各厂商免费额度变动频繁(2026-10 已核实一轮,结果见 `20-知识/免费服务器资源.md`),超半年需重跑核实
