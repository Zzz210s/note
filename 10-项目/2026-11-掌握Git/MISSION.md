# Mission: Git(版本控制与协作工作流)

> `teach` 教学工作区协议文件,与 [项目说明](<./!项目说明.md>) 配套(项目说明管任务与进度,本文件管「为什么学」)。
> 教学决策(下节教什么、给哪些资源、设计什么练习)都回到这份文件上。

## Why

Git 是两件事的共同底座:一是这个笔记库自己的版本管理,二是给 Zephyr 提 PR 的协作流程(DCO、rebase、review 往返)。不会 Git 就没法把「我做了什么」变成别人能验证的东西。

## Success looks like

- 能独立解决冲突、回滚误操作、做分支合并,并讲清背后原理(不是背命令)
- learnGitBranching 主要关卡通关(把分支模型玩成直觉)
- 在真实仓库完成一次 feature 分支开发 → 合并 → 回滚的完整往返
- 能说清 `reset` / `revert` / `rebase` / `cherry-pick` 各自改变了什么历史

## Constraints

- 窗口 —— → 2027-03-31;当前状态:未开始
- 以真实仓库为练习场:本库(`F:/0-Note`)与 Zephyr fork
- 母项目定位是「工程协作底座」,服务 2026Q4-参与Zephyr开源社区 与 2027 边缘函数线

## Out of scope

- 不深入 Git 内部对象存储实现(只到「能解释命令对历史做了什么」)
- 不学 GitHub Actions / CI 流水线 —— 那是 `20-领域/03-开发工具与工作流/` 里的独立主题
- 不碰 Git LFS / 子模块等小众特性,除非 Zephyr 流程需要

---

配套文件:[RESOURCES.md](<./RESOURCES.md>)(资源与社群)· [NOTES.md](<./NOTES.md>)(教学偏好)· `lessons/`(课程)· `reference/`(速查卡)· `learning-records/`(学习记录,按需创建)
