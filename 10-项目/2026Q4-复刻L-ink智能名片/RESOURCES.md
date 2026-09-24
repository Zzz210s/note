# 无源 NFC 墨水屏名片(L-ink Card) Resources

> 本项目教学资源的唯一清单:解释性知识只从 Knowledge 取材,不凭模型记忆。
> 校验:2026-09-24 用 curl 逐个探测(200 正常;403 是站点反爬,浏览器可正常访问)。

## Knowledge

- [peng-zhihui/L-ink_Card(母项目)](https://github.com/peng-zhihui/L-ink_Card)
  STM32 C 固件 + Altium 硬件工程 + 说明文档,复刻的唯一权威来源。用在:原理、BOM、固件结构
- [母项目 Hardware 目录(原理图与 PCB)](https://github.com/peng-zhihui/L-ink_Card/tree/master/Hardware)
  原理图与 PCB 工程文件。用在:研究取电电路与墨水屏驱动电路
- [simonire/L-ink_Card(社区修正版)](https://github.com/simonire/L-ink_Card)
  社区修正过的版本,踩坑信息更全。用在:原版器件停产/打样问题时对照
- [ST(意法半导体)官网](https://www.st.com/)
  ST25DV(NFC 动态标签)与 STM32L051 的数据手册与选型。用在:查电气参数与替代型号

## Wisdom (Communities)

- (暂无 —— 本项目暂不需要外部社群;遇到问题优先查官方文档与 issue 区)

## Gaps

- 中文社区对无源 NFC 取电的实践资料很少;主要靠 issue 区与电子论坛(如 EEVblog)
- ISO 15693 协议原文(ISO 标准)需付费,暂以 ST25DV 手册中的协议描述替代
