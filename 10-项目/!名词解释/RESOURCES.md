# 名词解释(概念辨析速览)Resources

> 本工作区教学资源的唯一清单:解释性知识只从 Knowledge 取材,不凭模型记忆。
> 校验:2026-09-25 用 `curl -sS -o /dev/null -w "%{http_code}" -L` 逐个探测,结果记在每条末尾。

## Knowledge

- [Wikipedia: Command-line interface](https://en.wikipedia.org/wiki/Command-line_interface)(200)
  用在:CLI 的定义、「命令 + 参数」这种交互为什么天生可脚本化
- [Wikipedia: Text-based user interface](https://en.wikipedia.org/wiki/Text-based_user_interface)(200)
  用在:TUI 的定义,以及它为什么不依赖图形通道、能在 SSH 里跑
- [Wikipedia: Graphical user interface](https://en.wikipedia.org/wiki/Graphical_user_interface)(200)
  用在:GUI 的定义与「功能可见性 / 零门槛」的来源
- [Wikipedia: Terminal emulator](https://en.wikipedia.org/wiki/Terminal_emulator)(200)
  用在:终端 / Shell / 命令行 / 控制台这几个易混词的分层
- [Wikipedia: Source-code editor](https://en.wikipedia.org/wiki/Source-code_editor)(200)
  用在:「编辑器只负责文本层」这条边界
- [Wikipedia: Compiler](https://en.wikipedia.org/wiki/Compiler)(200)
  用在:编译的定义、「整份翻完再跑」带来的改一行重翻一遍
- [Wikipedia: Interpreter (computing)](https://en.wikipedia.org/wiki/Interpreter_(computing))(200)
  用在:解释器的定义与「逐句执行」的区别
- [Wikipedia: Integrated development environment](https://en.wikipedia.org/wiki/Integrated_development_environment)(200)
  用在:IDE 到底集成了哪些工具、代价是什么
- [Python 官方文档:Using the Python Interpreter](https://docs.python.org/3/tutorial/interpreter.html)(200)
  用在:解释器的一手说明(本机 `python -V` 实测为 3.14.6,就是它)
- [GNU Compiler Collection 官方手册](https://gcc.gnu.org/onlinedocs/)(200)
  用在:编译器的一手文档入口(本机 `gcc --version` 实测为 15.2.0)
- [Wikipedia: Big O notation](https://en.wikipedia.org/wiki/Big_O_notation)(200)
  用在:大 O 的数学定义(渐近上界、常数与低阶项为何可扔)
- [Wikipedia: Time complexity](https://en.wikipedia.org/wiki/Time_complexity)(200)
  用在:常见量级排序表与「数基本操作次数」的做法
- [Wikipedia: Space complexity](https://en.wikipedia.org/wiki/Space_complexity)(200)
  用在:空间复杂度数的是「额外」且「同时活着」的内存
- [Wikipedia: Best, worst and average case](https://en.wikipedia.org/wiki/Best,_worst_and_average_case)(200)
  用在:同一算法三种输入为何复杂度不同、默认该报哪一个
- [Node.js 官方:Introduction to Node.js](https://nodejs.org/en/learn/getting-started/introduction-to-nodejs)(200)
  用在:Node.js 是运行时(runtime)而不是语言这一定位(本机 `node -v` 实测为 v24.14.0)
- [npm 官方文档:About npm](https://docs.npmjs.com/about-npm)(200)
  用在:npm 的包管理器职责与 registry 的角色(本机 `npm -v` 实测为 11.9.0)
- [pnpm 官方:Motivation](https://pnpm.io/motivation)(200)
  用在:pnpm 为什么用「内容寻址仓库 + 硬链接」,幽灵依赖是什么(本机 `pnpm -v` 实测为 12.5.1)
- [nodejs/corepack(官方仓库)](https://github.com/nodejs/corepack)(200)
  用在:corepack 管的是「包管理器自身的版本」(本机 `corepack -v` 实测为 0.34.6)
- [Wikipedia: Test fixture](https://en.wikipedia.org/wiki/Test_fixture)(200)
  用在:夹具的经典含义 —— 测试前置状态与 setUp / tearDown 成对出现
- [pytest 官方:How to use fixtures](https://docs.pytest.org/en/stable/how-to/fixtures.html)(200)
  用在:夹具在真实框架里的写法(准备与收尾怎么落地)
- [Martin Fowler: Test Double](https://martinfowler.com/bliki/TestDouble.html)(200)
  用在:mock / stub / fake 的职责差别,以及「替身不是夹具」这条边界
- [Wikipedia: Test double](https://en.wikipedia.org/wiki/Test_double)(200)
  用在:替身家族的完整清单与各自用途
- [Wikipedia: Lint (software)](https://en.wikipedia.org/wiki/Lint_(software))(200)
  用在:这类「不运行代码就挑毛病」的工具是怎么来的
- [Wikipedia: Static program analysis](https://en.wikipedia.org/wiki/Static_program_analysis)(200)
  用在:静态检查能查什么、为什么查不到事实错误
- [GitHub Actions 官方:Understand GitHub Actions](https://docs.github.com/en/actions/get-started/understand-github-actions)(200)
  用在:CI 把「每次推送都跑一遍检查」自动化是怎么配的
- [pre-commit](https://pre-commit.com/)(200)
  用在:「提交前自动跑检查」的一手文档,与巡检器「手动跑」的差别对照

## Wisdom (Communities)

- [Stack Overflow](https://stackoverflow.com/)(403,站点反爬;浏览器可正常访问)
  用在:名词在真实工程里「怎么用」的分歧 —— 问「什么时候该上 IDE」比问「IDE 是什么」更有价值
- [Hacker News](https://news.ycombinator.com/)(200,需 `--http1.1`)
  用在:工具选型的现场争论(CLI 与 GUI 谁更好用这类话题长期在讨论)

## Gaps

- **中文权威来源缺位**:维基中文条目质量参差,本工作区一律以英文原文为准;真需要中文辅助时再补条目
- **中文权威来源缺位**:维基中文条目质量参差,本工作区一律以英文原文为准;真需要中文辅助时再补条目
- **「实际手感」只能靠实测**:能在这台机器上验的都验了(`python -V` / `node -v` / `gcc --version` / 装了哪些
  TUI 工具),验不了的(如 IDE 的资源占用)只做定性描述,不编造具体数字
- **巡检器一节的一手来源是本库自己的代码,不是网页**:`50-资源/工具/vault-check/`
  才是它的权威定义处(网页只能提供 linter / CI 的背景);所以那节课的判据、A1~A14 编号与实测输出
  都直接取自代码与真实运行结果,RESOURCES 里的四条网页只用来对照「它和相邻概念差在哪」
