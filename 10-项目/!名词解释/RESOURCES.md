# 名词解释(概念辨析速览)Resources

> 本工作区教学资源的唯一清单:解释性知识只从 Knowledge 取材,不凭模型记忆。
> 校验:2026-09-25 用 `curl -sS -o /dev/null -w "%{http_code}" -L` 逐个探测,结果记在每条末尾;
> 2026-09-26 第四批(路由 / 桥接与 Wayland)新增的条目同法逐个探测。

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

### 2026-09-25 重写轮新增(课内引用就地给链接)

- [Wikipedia: Pipeline (Unix)](https://en.wikipedia.org/wiki/Pipeline_(Unix))(200)
  用在:CLI 的输出为什么能直接喂给下一条命令(0001 课里那个「两数都是 6」的自查)
- [Wikipedia: Shell (computing)](https://en.wikipedia.org/wiki/Shell_(computing))(200)
  用在:终端 / Shell / 命令行三层对照(速查卡里的那张表)
- [Wikipedia: Executable](https://en.wikipedia.org/wiki/Executable)(200)
  用在:编译产物是「机器能执行的文件」而不是文本(sum.exe 与 sum.c 的类别差)
- [GCC 官方手册: Invoking GCC](https://gcc.gnu.org/onlinedocs/gcc/Invoking-GCC.html)(200)
  用在:`gcc sum.c -o sum.exe` 里 `-o` 到底做什么
- [Wikipedia: Bytecode](https://en.wikipedia.org/wiki/Bytecode)(200)
  用在:「解释器也有编译这一步」中的字节码是什么(0002 课的 dis 输出)
- [Python 官方教程: Compiled Python files](https://docs.python.org/3/tutorial/modules.html#compiled-python-files)(200)
  用在:CPython 为什么默认也生成 `.pyc`;0002 的一手资源推荐就是这一条
- [Python 官方: py_compile](https://docs.python.org/3/library/py_compile.html)(200)
  用在:`python -m py_compile tiny.py` 落盘的那个 138 B 产物
- [Wikipedia: Constant folding](https://en.wikipedia.org/wiki/Constant_folding)(200)
  用在:`dis` 输出里没有加法(`LOAD_SMALL_INT 3`)—— `1 + 2` 在运行前就算完了
- [Wikipedia: Call stack](https://en.wikipedia.org/wiki/Call_stack)(200)
  用在:「递归占 O(n) 空间」靠的是每层未返回的栈帧同时活着
- [Python 官方: timeit](https://docs.python.org/3/library/timeit.html)(200)
  用在:0003 两组实测数字(同是 O(1) 差两个数量级、O(n) 翻倍 / O(n²) 翻四倍)的测量方法与口径

- [npm 官方:package.json](https://docs.npmjs.com/cli/v11/configuring-npm/package-json)(200)
  用在:依赖声明与 `packageManager` 字段(0004 里 corepack 照它切版本)
- [npm 官方:package-lock.json](https://docs.npmjs.com/cli/v11/configuring-npm/package-lock-json)(200)
  用在:锁文件记的是什么、为什么它该入库而 `node_modules/` 不该
- [npm 官方:npm root](https://docs.npmjs.com/cli/v11/commands/root)(200)
  用在:0004 实测里「本地的包到底在哪」这一问的官方口径
- [npm 官方:npx](https://docs.npmjs.com/cli/v11/commands/npx)(200)
  用在:npx「临时获取并执行、不长期保留」的定位
- [Node.js 官方:Modules](https://nodejs.org/api/modules.html)(200)
  用在:`require.resolve('npm')` 为什么返回 MODULE_NOT_FOUND —— 模块解析只沿当前目录往上找 `node_modules`
- [Node.js 官方:corepack](https://nodejs.org/api/corepack.html)(200)
  用在:corepack 管的是「包管理器自身的版本」
- [pnpm 官方:符号链接布局](https://pnpm.io/symlinked-node-modules-structure)(200)
  用在:pnpm 的 `node_modules/` 里为什么是一堆链接而不是拷贝
- [pnpm 官方:pnpm store](https://pnpm.io/cli/store)(200)
  用在:`pnpm store path` 的官方口径 —— 它只保证「返回当前生效的 store 目录」,位置本身取决于 cwd 在哪块盘
  (本机:F 盘下 `F:\.pnpm-store\v11`,C 盘下 `C:\Users\23652\AppData\Local\pnpm\store\v11`)
- [pnpm 官方:store 设置(storeDir)](https://pnpm.io/settings/store)(200)
  用在:store 默认位置与「一盘一个 store」—— 硬链接只能同盘,所以 store 总在项目所在那块盘上
- [pnpm 官方:FAQ(跨盘怎么处理)](https://pnpm.io/faq#does-pnpm-work-across-multiple-drives-or-filesystems)(200)
  用在:「仓库与安装不同盘时会复制而不是链接」这条边界(0004 靠它推翻了一个错结论)
- [Yarn 官方:yarn.lock](https://classic.yarnpkg.com/lang/en/docs/yarn-lock/)(200)
  用在:凭锁文件认包管理器(见 `yarn.lock` 就别换工具)
- [Martin Fowler: Mocks Aren't Stubs](https://martinfowler.com/articles/mocksArentStubs.html)(200)
  用在:mock 与 stub 的分界 —— 「自带期望」还是「念死台词」(0005 对比表的判据)
- [Python 官方:unittest](https://docs.python.org/3/library/unittest.html)(200)
  用在:setUp / tearDown 成对出现的一手定义(夹具含义一的落地形态)
- [Wikipedia: Exit status](https://en.wikipedia.org/wiki/Exit_status)(200)
  用在:退出码 0 与非 0 的语义 —— 0006 的结论落在退出码上
- [Wikipedia: Continuous integration](https://en.wikipedia.org/wiki/Continuous_integration)(200)
  用在:CI 把「每次推送都跑一遍检查」自动化是干什么的(与手动跑巡检器对照)

### 2026-09-25 第三批新增(UI / UX 与 CI)

- [Wikipedia: User interface](https://en.wikipedia.org/wiki/User_interface)(200)
  用在:UI 的定义 —— 「人与机器发生交互的那个空间」,以及机器要回馈可判断的信息
- [Wikipedia: User experience](https://en.wikipedia.org/wiki/User_experience)(200)
  用在:UX 的定义与 ISO 9241 的措辞(使用或预期使用时产生的感知与反应)
- [NN/g: The Definition of User Experience (UX)](https://www.nngroup.com/articles/definition-user-experience/)(200)
  用在:UI / UX / 可用性三者的分界、「可用性是 UI 的一项质量属性」这句,以及那个「UI 完美但片库缺片」的影评网站反例(0007 课的核心判据)
- [NN/g: Usability 101](https://www.nngroup.com/articles/usability-101-introduction-to-usability/)(200)
  用在:可用性「评估界面有多易用」的定义与五个分量(可学 / 高效 / 易记 / 少错 / 满意)
- [W3C: Understanding SC 1.4.3 Contrast (Minimum)](https://www.w3.org/WAI/WCAG21/Understanding/contrast-minimum.html)(200)
  用在:正文对比度 ≥ 4.5:1、大号文字 ≥ 3:1,以及「大号 = 18pt / 24px 或加粗 14pt」
- [W3C: Understanding SC 1.4.11 Non-text Contrast](https://www.w3.org/WAI/WCAG21/Understanding/non-text-contrast.html)(200)
  用在:非文字件 3:1 的另一档口径 —— 解释本机那条 1.44:1 的分隔线为何不算违规
- [Butterick's Practical Typography: Line length](https://practicaltypography.com/line-length.html)(200)
  用在:45~90 字符行宽的经验值,与 0007 课里 46rem / 736px 的换算对照
- [Martin Fowler: Continuous Integration](https://martinfowler.com/articles/continuousIntegration.html)(200)
  用在:CI 的原始定义、那条实践清单,以及「只在功能分支上跑 = 半集成」「十分钟构建」等判据
- [Martin Fowler: Continuous Delivery](https://martinfowler.com/bliki/ContinuousDelivery.html)(200)
  用在:交付的定义与「可重复的流水线」为何是前提;两个 CD 只差一个「人工确认」
- [Wikipedia: Continuous deployment](https://en.wikipedia.org/wiki/Continuous_deployment)(200)
  用在:持续部署的定义 —— 验证通过就自动进生产,没有人工确认
- [GitHub 官方:Workflow syntax for GitHub Actions](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax)(200)
  用在:0008 课里那段最小骨架的字段含义(name / on / jobs / runs-on / steps / uses / run)
- [GitHub 官方:Quickstart for GitHub Actions](https://docs.github.com/en/actions/get-started/quickstart)(200)
  用在:workflow 文件放哪里、怎么被触发(与骨架逐行注对照)

### 2026-09-26 第四批新增(路由 / 桥接与 Wayland)

- [Wikipedia: Router (computing)](https://en.wikipedia.org/wiki/Router_(computing))(200)
  用在:路由的定义 —— 连接多个网络、按目标 IP 在网段之间转发
- [Wikipedia: Network address translation](https://en.wikipedia.org/wiki/Network_address_translation)(200)
  用在:NAT 在做什么(出口处替换地址并记住连接来源),以及「外面看不见我」这条代价的成因
- [Wikipedia: Bridging (networking)](https://en.wikipedia.org/wiki/Bridging_(networking))(200)
  用在:桥接的定义 —— 数据链路层把多段接成一片、对主机透明
- [Wikipedia: Point-to-Point Protocol over Ethernet](https://en.wikipedia.org/wiki/Point-to-Point_Protocol_over_Ethernet)(200)
  用在:三问里「谁在拨号」的技术底座(PPPoE)
- [Wikipedia: TUN/TAP](https://en.wikipedia.org/wiki/TUN/TAP)(200)
  用在:TUN 三层接管 / TAP 二层接管 —— 本机 sing-tun 代理与路由模式的关系
- [Microsoft Learn: Accessing network applications with WSL](https://learn.microsoft.com/en-us/windows/wsl/networking)(200)
  用在:默认 NAT、mirrored 模式与「Windows 与 WSL 谁是网关」(0009 课的一手资源)
- [Microsoft Learn: 高级设置配置(wsl-config)](https://learn.microsoft.com/en-us/windows/wsl/wsl-config)(200)
  用在:`networkingMode` 的合法值,以及 `bridged` 自 WSL 2.4.5 起已 deprecated
- [Oracle VM VirtualBox 手册 第 6 章(Virtual Networking)](https://www.virtualbox.org/manual/ch06.html)(200)
  用在:桥接「绕过宿主网络栈」与仅主机「类似回环的虚拟网卡」两条取舍
- [Wayland 官方: Architecture](https://wayland.freedesktop.org/architecture.html)(200)
  用在:X 与 Wayland 的分工差别(谁画、谁管前缓冲、谁算得准点击落在哪个窗口);0010 课的一手资源
- [Wayland 官方: FAQ](https://wayland.freedesktop.org/faq.html)(200)
  用在:「合成器发输入、客户端本地渲染并交回缓冲区」与「不支持网络透明 / 远程渲染」两句原文
- [Arch Wiki: Wayland](https://wiki.archlinux.org/title/Wayland)(200)
  用在:「Wayland 只是协议,没有统一的显示服务器可装」;GUI 库后端变量(GDK_BACKEND / QT_QPA_PLATFORM / SDL_VIDEODRIVER)、Xwayland 程序的识别(`xlsclients -l`)与远程显示后端(wayvnc / gnome-remote-desktop / krfb)
- [Arch Wiki: Screen capture](https://wiki.archlinux.org/title/Screen_capture)(200)
  用在:截图 / 录屏工具在 Wayland 下按合成器分家(grim / gnome-screenshot / spectacle 各自的前提)
- [XDG Desktop Portal 文档](https://flatpak.github.io/xdg-desktop-portal/docs/)(200)
  用在:截图 / 录屏 / 全局快捷键 / 远程桌面在新架构里都要经门户申请
- [XDG Desktop Portal: ScreenCast](https://flatpak.github.io/xdg-desktop-portal/docs/doc-org.freedesktop.portal.ScreenCast.html)(200)
  用在:录屏 / 共享要从门户拿一条流(而不是自己抓屏)
- [XDG Desktop Portal: GlobalShortcuts](https://flatpak.github.io/xdg-desktop-portal/docs/doc-org.freedesktop.portal.GlobalShortcuts.html)(200)
  用在:全局快捷键为什么不再能「自己抓」
- [XDG Desktop Portal: RemoteDesktop](https://flatpak.github.io/xdg-desktop-portal/docs/doc-org.freedesktop.portal.RemoteDesktop.html)(200)
  用在:远程桌面的门户化路线
- [microsoft/wslg](https://github.com/microsoft/wslg)(200)
  用在:WSLg 是 Wayland 实现这件事的项目主页(与 weston.log 的本机证据相互印证)
- [Microsoft Learn: Run Linux GUI apps with WSL](https://learn.microsoft.com/en-us/windows/wsl/tutorials/gui-apps)(200)
  用在:WSL 里跑 Linux 图形程序靠的是一套独立的图形子系统

## Wisdom (Communities)

- [Stack Overflow](https://stackoverflow.com/)(403,站点反爬;浏览器可正常访问)
  用在:名词在真实工程里「怎么用」的分歧 —— 问「什么时候该上 IDE」比问「IDE 是什么」更有价值
- [Hacker News](https://news.ycombinator.com/)(200,需 `--http1.1`)
  用在:工具选型的现场争论(CLI 与 GUI 谁更好用这类话题长期在讨论)

## Gaps

- **中文权威来源缺位**:维基中文条目质量参差,本工作区一律以英文原文为准;真需要中文辅助时再补条目
- **「实际手感」只能靠实测**:能在这台机器上验的都验了(`python -V` / `node -v` / `gcc --version` / 装了哪些
  TUI 工具),验不了的(如 IDE 的资源占用)只做定性描述,不编造具体数字
- **巡检器一节的一手来源是本库自己的代码,不是网页**:`50-资源/工具/vault-check/`
  才是它的权威定义处(网页只能提供 linter / CI 的背景);所以那节课的判据、A1~A14 编号与实测输出
  都直接取自代码与真实运行结果,RESOURCES 里的四条网页只用来对照「它和相邻概念差在哪」
- **CI / CD 一节的证据一半在本机仓库里**(不是网页来源):`Zzz210s/ai-session-hub` 的
  `.github/workflows/test.yml` 与四次真实运行记录是 CI 的真样本;
  `Zzz210s/personal-content` 的 `trigger-site.yml`(push `main` → 打 Cloudflare Pages deploy hook,
  全自动上线 = **真持续部署**)与 `Zzz210s/GoodNight` 的 `ci.yml`(打 `v*` tag → 构建 APK 并自动发 Release,
  `draft: false` = 人工只剩打 tag,属**持续交付**)是 CD 的真样本。三份文件都能在本机 `F:/0-code` 下直接读到,
  运行记录用 `gh run list` 复现;
  本库自己(`Zzz210s/note`)2026-09-25 尚无 `.github/workflows/`,课里的骨架因此是骨架而不是现状
- **路由 / 桥接与 Wayland 两节的证据一半在本机**:WSL2 的网络配置(`ip route` / `ipconfig /all` / 一次
  curl 可达性实验 / `tracert`)与 WSLg 的合成器日志和套接字(`weston.log` / `ss -xl` / `XDG_SESSION_TYPE`)
  都是现跑的原始输出;网页来源(Wikipedia / Microsoft Learn / Wayland 官方 / Arch Wiki / 门户文档)
  只用来对照定义与判据。拿不到的那部分也写清了:WSL 里 `XDG_SESSION_TYPE` 为空、
  `wayland-info` / `grim` 未装,所以 0010 不演示抓屏;对公网地址的 `tracert` 被本机 TUN 代理污染,不作论据
