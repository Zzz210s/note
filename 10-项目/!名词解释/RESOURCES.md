# 名词解释(概念辨析速览)Resources

> 本工作区教学资源的唯一清单:解释性知识只从 Knowledge 取材,不凭模型记忆。
> 校验:2026-09-26 用 `curl -sS -o /dev/null -w "%{http_code}" -L` 把下面每一条逐个探测,结果记在每条末尾;
> 2026-09-25 概念化重写轮(0001~0005 去掉本机数据)与 2026-09-26 第五批(0006~0010 同法)新增的条目同法逐个探测。
> **课一律不用本机数据**(见 `NOTES.md` 的「新课标准」);只服务某次本机实测的条目已随重写删除。

## Knowledge

### 界面形态与工具链(课 0001 / 0002)

- [Wikipedia: Command-line interface](https://en.wikipedia.org/wiki/Command-line_interface)(200)
  用在:CLI 的定义、「命令 + 参数」这种交互为什么天生可脚本化
- [Wikipedia: Text-based user interface](https://en.wikipedia.org/wiki/Text-based_user_interface)(200)
  用在:TUI 的定义,以及它为什么不依赖图形通道、能在 SSH 里跑
- [Wikipedia: Graphical user interface](https://en.wikipedia.org/wiki/Graphical_user_interface)(200)
  用在:GUI 的定义与「功能可见性 / 零门槛」的来源
- [Wikipedia: Terminal emulator](https://en.wikipedia.org/wiki/Terminal_emulator)(200)
  用在:终端 / Shell / 命令行 / 控制台这几个易混词的分层
- [Wikipedia: Shell (computing)](https://en.wikipedia.org/wiki/Shell_(computing))(200)
  用在:终端 / Shell / 命令行三层对照(速查卡里的那张表)
- [Wikipedia: Pipeline (Unix)](https://en.wikipedia.org/wiki/Pipeline_(Unix))(200)
  用在:CLI 的输出为什么能直接喂给下一条命令
- [Wikipedia: Source-code editor](https://en.wikipedia.org/wiki/Source-code_editor)(200)
  用在:「编辑器只负责文本层」这条边界
- [Wikipedia: Compiler](https://en.wikipedia.org/wiki/Compiler)(200)
  用在:编译的定义、「整份翻完再跑」带来的改一行重翻一遍
- [Wikipedia: Interpreter (computing)](https://en.wikipedia.org/wiki/Interpreter_(computing))(200)
  用在:解释器的定义与「逐句执行」的区别
- [Wikipedia: Integrated development environment](https://en.wikipedia.org/wiki/Integrated_development_environment)(200)
  用在:IDE 到底集成了哪些工具、代价是什么
- [Wikipedia: Bytecode](https://en.wikipedia.org/wiki/Bytecode)(200) ·
  [Virtual machine](https://en.wikipedia.org/wiki/Virtual_machine)(200) ·
  [Just-in-time compilation](https://en.wikipedia.org/wiki/Just-in-time_compilation)(200)
  用在:纯编译与纯解释之间的混合形态 —— 先编译成字节码、由虚拟机解释、热点再 JIT(0002 的一节)
- [Python 官方教程:Using the Python Interpreter](https://docs.python.org/3/tutorial/interpreter.html)(200)
  用在:解释器的一手说明(怎么启动它、它以什么方式执行源码)
- [Python 官方教程:Compiled Python files](https://docs.python.org/3/tutorial/modules.html#compiled-python-files)(200)
  用在:CPython 为什么默认也生成 `.pyc`(0002 的一手资源推荐)
- [GNU Compiler Collection 官方手册](https://gcc.gnu.org/onlinedocs/)(200)
  用在:编译器的一手文档入口(编译选项、产物格式)

### 算法复杂度(课 0003)

- [Wikipedia: Big O notation](https://en.wikipedia.org/wiki/Big_O_notation)(200)
  用在:大 O 的数学定义(渐近上界、常数与低阶项为何可扔)
- [Wikipedia: Time complexity](https://en.wikipedia.org/wiki/Time_complexity)(200)
  用在:常见量级排序表与「数基本操作次数」的做法
- [Wikipedia: Space complexity](https://en.wikipedia.org/wiki/Space_complexity)(200)
  用在:空间复杂度数的是「额外」且「同时活着」的内存
- [Wikipedia: Best, worst and average case](https://en.wikipedia.org/wiki/Best,_worst_and_average_case)(200)
  用在:同一算法三种输入为何复杂度不同、默认该报哪一个
- [Wikipedia: Analysis of algorithms](https://en.wikipedia.org/wiki/Analysis_of_algorithms)(200)
  用在:复杂度「只留最高阶、扔掉系数」的依据
- [Wikipedia: Call stack](https://en.wikipedia.org/wiki/Call_stack)(200)
  用在:「递归占 O(n) 空间」靠的是每层未返回的栈帧同时活着

### 运行时与包管理(课 0004)

- [Node.js 官方:Introduction to Node.js](https://nodejs.org/en/learn/getting-started/introduction-to-nodejs)(200)
  用在:Node.js 是运行时(runtime)而不是语言这一定位
- [npm 官方文档:About npm](https://docs.npmjs.com/about-npm)(200)
  用在:npm 的包管理器职责与 registry 的角色
- [pnpm 官方:Motivation](https://pnpm.io/motivation)(200)
  用在:pnpm 为什么用「内容寻址仓库 + 硬链接」,幽灵依赖是什么
- [nodejs/corepack(官方仓库)](https://github.com/nodejs/corepack)(200) ·
  [Node.js 官方:corepack](https://nodejs.org/api/corepack.html)(200)
  用在:corepack 管的是「包管理器自身的版本」
- [npm 官方:package.json](https://docs.npmjs.com/cli/v11/configuring-npm/package-json)(200)
  用在:依赖声明与 `packageManager` 字段(corepack 照它切版本)
- [npm 官方:package-lock.json](https://docs.npmjs.com/cli/v11/configuring-npm/package-lock-json)(200)
  用在:锁文件记的是什么、为什么它该入库而 `node_modules/` 不该
- [npm 官方:npm root](https://docs.npmjs.com/cli/v11/commands/root)(200) ·
  [npm 官方:npx](https://docs.npmjs.com/cli/v11/commands/npx)(200)
  用在:「本地的包到底在哪」与 npx「临时获取并执行、不长期保留」的官方口径
- [Node.js 官方:Modules](https://nodejs.org/api/modules.html)(200)
  用在:模块解析只沿当前目录往上找 `node_modules` —— 全局装的包为什么导入不到
- [pnpm 官方:符号链接布局](https://pnpm.io/symlinked-node-modules-structure)(200)
  用在:pnpm 的 `node_modules/` 里为什么是一堆链接而不是拷贝
- [pnpm 官方:pnpm store](https://pnpm.io/cli/store)(200) ·
  [store 设置(storeDir)](https://pnpm.io/settings/store)(200) ·
  [FAQ:跨盘怎么处理](https://pnpm.io/faq#does-pnpm-work-across-multiple-drives-or-filesystems)(200)
  用在:store 的位置取决于当前目录在哪块盘、硬链接只能同盘(速查卡「包放在哪几个地方」)
- [Yarn 官方:yarn.lock](https://classic.yarnpkg.com/lang/en/docs/yarn-lock/)(200)
  用在:凭锁文件认包管理器(见 `yarn.lock` 就别换工具)

### 测试与替身(课 0005)

- [Wikipedia: Test fixture](https://en.wikipedia.org/wiki/Test_fixture)(200)
  用在:夹具的经典含义 —— 测试前置状态与 setUp / tearDown 成对出现;也是 0006「检查器自己也要被检查」的出处
- [pytest 官方:How to use fixtures](https://docs.pytest.org/en/stable/how-to/fixtures.html)(200)
  用在:夹具在真实框架里的写法(准备与收尾怎么落地)
- [Python 官方:unittest](https://docs.python.org/3/library/unittest.html)(200)
  用在:setUp / tearDown 成对出现的一手定义(夹具含义一的落地形态)
- [Martin Fowler: Test Double](https://martinfowler.com/bliki/TestDouble.html)(200) ·
  [Wikipedia: Test double](https://en.wikipedia.org/wiki/Test_double)(200)
  用在:mock / stub / fake 的职责差别,与替身家族的完整清单
- [Martin Fowler: Mocks Aren't Stubs](https://martinfowler.com/articles/mocksArentStubs.html)(200)
  用在:mock 与 stub 的分界 —— 「自带期望」还是「念死台词」(0005 对比表的判据)

### 巡检器 / 一致性检查器(课 0006)

- [Wikipedia: Lint (software)](https://en.wikipedia.org/wiki/Lint_(software))(200)
  用在:这类「不运行内容就挑毛病」的工具从哪来、边界在哪(0006 的一手资源)
- [Wikipedia: Static program analysis](https://en.wikipedia.org/wiki/Static_program_analysis)(200)
  用在:静态检查能查什么、为什么查不到事实错误
- [Wikipedia: Link rot](https://en.wikipedia.org/wiki/Link_rot)(200)
  用在:链接会烂、且烂了不会让任何东西报错 —— 巡检器存在的第一个理由
- [Wikipedia: Exit status](https://en.wikipedia.org/wiki/Exit_status)(200)
  用在:退出码 0 与非 0 的语义 —— 0006 的结论、0008 里 CI 判红绿都落在它上面
- [pre-commit](https://pre-commit.com/)(200)
  用在:「提交前自动跑检查」的一手文档 —— 让巡检这类检查自动发生的第一种方式
- [GitHub Actions 官方:Understand GitHub Actions](https://docs.github.com/en/actions/get-started/understand-github-actions)(200)
  用在:让检查在每次推送时自动发生的第二种方式(与 0008 同一份来源)
- [Wikipedia: Continuous integration](https://en.wikipedia.org/wiki/Continuous_integration)(200)
  用在:CI 把「每次推送都跑一遍检查」制度化是干什么的(0006 与 0008 共用)

### 交互设计(课 0007)

- [Wikipedia: User interface](https://en.wikipedia.org/wiki/User_interface)(200)
  用在:UI 的定义 —— 「人与机器发生交互的那个空间」,以及机器要回馈可判断的信息
- [Wikipedia: User experience](https://en.wikipedia.org/wiki/User_experience)(200)
  用在:UX 的定义与 ISO 9241 的措辞(使用或预期使用时产生的感知与反应)
- [NN/g: The Definition of User Experience (UX)](https://www.nngroup.com/articles/definition-user-experience/)(200)
  用在:UI / UX / 可用性三者的分界、「可用性是 UI 的一项质量属性」这句,以及那个「UI 完美但片库缺片」的影评网站反例(0007 的一手资源)
- [NN/g: Usability 101](https://www.nngroup.com/articles/usability-101-introduction-to-usability/)(200)
  用在:可用性「评估界面有多易用」的定义与五个分量(可学 / 高效 / 易记 / 少错 / 满意)
- [W3C: Understanding SC 1.4.3 Contrast (Minimum)](https://www.w3.org/WAI/WCAG21/Understanding/contrast-minimum.html)(200)
  用在:正文对比度 ≥ 4.5:1、大号文字 ≥ 3:1,以及「大号 = 18pt / 24px 或加粗 14pt」
- [W3C: Understanding SC 1.4.11 Non-text Contrast](https://www.w3.org/WAI/WCAG21/Understanding/non-text-contrast.html)(200)
  用在:非文字件 3:1 的另一档口径 —— 解释「低于 4.5 不等于违规」
- [W3C: Understanding SC 2.5.8 Target Size (Minimum)](https://www.w3.org/WAI/WCAG22/Understanding/target-size-minimum.html)(200)
  用在:点按目标 24×24 CSS px 的下限(速查卡五条阈值之一)
- [Butterick's Practical Typography: Line length](https://practicaltypography.com/line-length.html)(200)
  用在:45~90 字符行宽的经验值,以及「2~3 个字母表」那条同页建议

### CI / CD(课 0008)

- [Martin Fowler: Continuous Integration](https://martinfowler.com/articles/continuousIntegration.html)(200)
  用在:CI 的原始定义、实践清单,以及「只在功能分支上跑 = 半集成」「十分钟构建」等判据
- [Martin Fowler: Continuous Delivery](https://martinfowler.com/bliki/ContinuousDelivery.html)(200)
  用在:交付的定义与「可重复的流水线」为何是前提;两个 CD 只差一个「人工确认」(0008 的一手资源)
- [Wikipedia: Continuous deployment](https://en.wikipedia.org/wiki/Continuous_deployment)(200)
  用在:持续部署的定义 —— 验证通过就自动进生产,没有人工确认
- [GitHub 官方:Workflow syntax for GitHub Actions](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax)(200)
  用在:最小骨架里每个字段的含义,以及「`environment` 上挂人工批准 = 持续交付」这条分界
- [GitHub 官方:Quickstart for GitHub Actions](https://docs.github.com/en/actions/get-started/quickstart)(200)
  用在:配置文件放哪里、怎么被触发
- [Wikipedia: Feature toggle](https://en.wikipedia.org/wiki/Feature_toggle)(200) ·
  [Wikipedia: Blue-green deployment](https://en.wikipedia.org/wiki/Blue%E2%80%93green_deployment)(200)
  用在:持续部署前提清单里的两条 —— 把「部署」与「发布」拆开、以及怎么把风险切成两半

### 网络接法(课 0009)

- [Wikipedia: Router (computing)](https://en.wikipedia.org/wiki/Router_(computing))(200)
  用在:路由的定义 —— 连接多个网络、按目标地址在网段之间转发
- [Wikipedia: Network address translation](https://en.wikipedia.org/wiki/Network_address_translation)(200)
  用在:地址转换在做什么(出口处替换地址并记住连接来源),以及「外面看不见我」这条代价的成因
- [Wikipedia: Point-to-Point Protocol over Ethernet](https://en.wikipedia.org/wiki/Point-to-Point_Protocol_over_Ethernet)(200)
  用在:三问里「谁在拨号」的技术底座(PPPoE)
- [Wikipedia: Dynamic Host Configuration Protocol](https://en.wikipedia.org/wiki/Dynamic_Host_Configuration_Protocol)(200)
  用在:三问里「谁发 IP」是什么机制
- [Wikipedia: Bridging (networking)](https://en.wikipedia.org/wiki/Bridging_(networking))(200)
  用在:桥接的定义 —— 数据链路层把多段接成一片、对主机透明
- [Wikipedia: Broadcasting (networking)](https://en.wikipedia.org/wiki/Broadcasting_(networking))(200)
  用在:为什么「要收广播 / 被自动发现」的东西不能待在路由器后面
- [Wikipedia: Port forwarding](https://en.wikipedia.org/wiki/Port_forwarding)(200)
  用在:NAT 后面想被外面主动连进来,必须显式配的那一步
- [Wikipedia: TUN/TAP](https://en.wikipedia.org/wiki/TUN/TAP)(200)
  用在:TUN 三层接管 / TAP 二层接管 —— 隧道上的路由与桥接(速查卡「相邻线索」)
- [Oracle VM VirtualBox 手册 第 6 章(Virtual Networking)](https://www.virtualbox.org/manual/ch06.html)(200)
  用在:桥接 / NAT / 仅主机 / 内部网络四态的定义,以及桥接「绕过宿主网络栈」这条取舍(0009 的一手资源)

### 显示层(课 0010)

- [Wayland 官方: Architecture](https://wayland.freedesktop.org/architecture.html)(200)
  用在:X 与 Wayland 的分工差别(谁画、谁管前缓冲、谁算得准点击落在哪个窗口);0010 的一手资源
- [Wayland 官方: FAQ](https://wayland.freedesktop.org/faq.html)(200)
  用在:「合成器发输入、客户端本地渲染并交回缓冲区」与「不支持网络透明」两句原文
- [Wikipedia: Wayland (protocol)](https://en.wikipedia.org/wiki/Wayland_(protocol))(200) ·
  [Wikipedia: X Window System](https://en.wikipedia.org/wiki/X_Window_System)(200)
  用在:两代显示架构的百科定义与历史脉络
- [Arch Wiki: Wayland](https://wiki.archlinux.org/title/Wayland)(200)
  用在:「Wayland 只是协议,没有统一的显示服务器可装」;GUI 库后端变量、Xwayland 程序的识别与远程显示后端
- [Arch Wiki: Xwayland](https://wiki.archlinux.org/title/Xwayland)(200)
  用在:「能跑 X11 程序不等于还在 X11 里」的落地细节
- [Arch Wiki: Screen capture](https://wiki.archlinux.org/title/Screen_capture)(200)
  用在:截图 / 录屏工具在 Wayland 下按合成器分家(grim / gnome-screenshot / spectacle 各自的前提)
- [XDG Desktop Portal 文档](https://flatpak.github.io/xdg-desktop-portal/docs/)(200) ·
  [ScreenCast](https://flatpak.github.io/xdg-desktop-portal/docs/doc-org.freedesktop.portal.ScreenCast.html)(200) ·
  [GlobalShortcuts](https://flatpak.github.io/xdg-desktop-portal/docs/doc-org.freedesktop.portal.GlobalShortcuts.html)(200) ·
  [RemoteDesktop](https://flatpak.github.io/xdg-desktop-portal/docs/doc-org.freedesktop.portal.RemoteDesktop.html)(200)
  用在:截图 / 录屏 / 全局快捷键 / 远程桌面在新架构里都要经门户申请
- [Ubuntu 25.10 发行说明(Wayland 一节)](https://documentation.ubuntu.com/release-notes/25.10/)(200)
  用在:发行版侧的一手事实 —— 该版起 GNOME 会话只跑 Wayland 后端,老程序靠 XWayland 显示
- [The Wayland Protocol(wayland-book.com)](https://wayland-book.com/)(200)
  用在:常见协议与接口的总览(比 FAQ 更细,按需深入)

## Wisdom (Communities)

- [Stack Overflow](https://stackoverflow.com/)(403,站点反爬;浏览器可正常访问)
  用在:名词在真实工程里「怎么用」的分歧 —— 问「什么时候该上 IDE」比问「IDE 是什么」更有价值
- [Hacker News](https://news.ycombinator.com/)(200,需 `--http1.1`)
  用在:工具选型的现场争论(CLI 与 GUI 谁更好用这类话题长期在讨论)

## Gaps

- **中文权威来源缺位**:维基中文条目质量参差,本工作区一律以英文原文为准;真需要中文辅助时再补条目
- **0001~0010 全部是全概念课,不含本机数据**:按用户 2026-09-25 的决定,课只讲定义、作用与判据,
  并在 2026-09-26 的第五批里推到 0006~0010;只服务某次本机实测的条目已删除
  (WSLg 项目主页、Microsoft Learn 的 WSL 网络与 wsl-config、WSL GUI 应用三篇都在此列)
- **0006 的通用化取舍**:这节课讲的是「巡检器 / 一致性检查器」这一类工具的*通用形状*
  —— 规则化检查、按文件行号报违规、退出码给流水线用;某个具体实现的那套判据编号与实测输出**不进课**,
  只留在长版词条 [巡检器](20-知识/巡检器.md) 里。所以课里引的是 Lint / Link rot / Exit status / 静态分析
  这几条通用来源,而不是某个工具的代码
- **0009 / 0010 的通用例子优先**:家用宽带(光猫拨号与桥接)与虚拟机网络四态都是公开可查的通用语境,
  虚拟化一侧的一手来源用 VirtualBox 手册;WSL 那一侧的网络文档不再引用,因为它只服务被删掉的本机实测
- **0010 缺一份 Ubuntu 专属的 Wayland 手册页**:`wiki.ubuntu.com/Wayland` 已 404,
  目前只引到发行说明(release notes)里的那一节;若以后出现官方手册页再补
- **0011(tmux)/ 0012(GRUB)尚未开课**:这两节要等下一批,届时按同一套标准写
