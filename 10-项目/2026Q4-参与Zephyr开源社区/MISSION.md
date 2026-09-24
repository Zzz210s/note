# Mission: Zephyr RTOS 开源协作

> `teach` 教学工作区协议文件,与 [项目说明](<./!项目说明.md>) 配套(项目说明管任务与进度,本文件管「为什么学」)。
> 教学决策(下节教什么、给哪些资源、设计什么练习)都回到这份文件上。

## Why

① 这条线纯 Python / Markdown,在只有 Windows、硬件未采购的情况下就能跑;② 母项目 16.5k star、4600+ 贡献者,满足「高赞且多贡献者」;③ 与内核线共用同一套 DCO / review / CI 礼仪,一份学习两处产出;④ 面试可直接讲「我给工业级 RTOS 的官方工具链提过被合并的 PR」。

## Success looks like

- 至少 3 个被合并的贡献(≥1 代码/工具链 + ≥1 文档)
- 与 maintainer 产生真实的 review 往返(不是一次通过,而是有来有回地改)
- 能在本地跑通 Zephyr 文档构建(WSL2)与 twister 相关流程
- 留下可复述的贡献记录:每个 PR 的动机、往返、最终形态(在 `开源贡献/` 里)

## Constraints

- 事件驱动:以 3 个合并 PR 为出口,**不设日历节点**;起始 2026-09-21
- 环境只有 Windows(可用 WSL2),不依赖目标硬件
- 贡献礼仪必须守住:AI 参与要按项目要求署名,绝不替人加 `Signed-off-by`

## Out of scope

- 不做需要目标硬件的驱动开发(如板级 bring-up)
- 不碰 Zephyr 内核调度器等高风险子系统(先工具链/文档)
- 本项目不重复讲 Git 基础 —— 那是 `2026-11-掌握Git`

---

配套文件:[RESOURCES.md](<./RESOURCES.md>)(资源与社群)· [NOTES.md](<./NOTES.md>)(教学偏好)· `lessons/`(课程)· `reference/`(速查卡)· `learning-records/`(学习记录,按需创建)
