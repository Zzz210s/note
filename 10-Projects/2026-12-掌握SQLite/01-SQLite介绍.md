# SQLite 介绍

> 2026-09-05 联网调研撰写,作「2026-12-掌握SQLite」项目的入门材料。事实口径以 sqlite.org 官方为准,资料来源见文末。

## 一句话定位

SQLite 是一个**嵌入式、无服务器、零配置、事务性(ACID)的 SQL 关系型数据库引擎**。它不是独立运行的数据库服务,而是以**库文件**形式链接进应用程序,直接读写普通磁盘文件(或内存 `:memory:`)——一个完整数据库(表/索引/视图全在内)就是一个**单文件**,可随意复制、移动、跨平台使用。

它是**世界上部署最广的数据库引擎**(部署量超 1 万亿份):手机系统、浏览器、桌面应用、嵌入式设备的默认存储里到处是它。你几乎每天都在用,只是没意识到。

## 核心特性

| 特性 | 说明 |
| --- | --- |
| 部署形态 | 嵌入式库,无独立服务进程、无网络端口;单文件跨平台(表/索引/视图都在一个文件里) |
| 配置成本 | 零配置、免安装、免运维;备份 = 复制文件 |
| 可靠性 | 遵循 ACID 事务,断电/崩溃后不损坏(官方以极端测试著称,常被引为"航空级"质量) |
| 体积 | 全功能 <400KiB,精简可 <250KiB |
| 容量 | 单库上限 281 TB(2^48 字节),单行上限约 1 GB |
| 并发模型 | 多读单写(整个库一把写锁);`WAL` 模式下读不阻塞写,官方量级约每秒千次写 |
| 类型系统 | 动态类型:五个存储类 NULL/INTEGER/REAL/TEXT/BLOB,列不强制类型(类型亲和性) |
| 语言绑定 | C 原生 + 各语言驱动:Python 标准库自带 `sqlite3`、Node 22+ 内置 `node:sqlite`、Go/Rust/Java…应有尽有 |
| 许可 | 公有领域(2014 年起),免费用于任何目的 |

## 它不是什么(边界)

- **不是 client-server 数据库**:不通过网络监听、不需要账号密码,也没有远程访问——多人多机同时直连同一文件会踩写锁冲突;
- **不适合高并发写入与多用户在线场景**:整库一把写锁,写多会 `SQLITE_BUSY`(大流量 Web 后端选 MySQL/PostgreSQL);
- **非分布式**:单机单文件,跨机同步靠文件本身(边缘分布式场景用 Cloudflare D1,见下);
- **"281 TB"是理论上限**,日常请按"几百 GB 以内、单机、低并发写"来规划才舒服。

## 何时用 / 何时不用

| 适合 | 不适合 |
| --- | --- |
| 个人学习与练 SQL(成本最低的入口) | 多用户高并发写(电商/社交后端) |
| 桌面 / 移动 / 嵌入式本地存储 | 需要网络访问与细粒度权限控制的库 |
| 本地工具缓存、配置库、索引库(如 pi codegraph / magic-context) | 数据量几十 TB 级、要分布式扩展 |
| 原型先行:先 SQLite 快速出活,量起来再迁 PostgreSQL | 已有成熟的 MySQL/Pg 运维环境,没必要引入第二种 |

判断口诀:**"要不要跑独立服务、要不要多人并发写"**——两个都不要,SQLite 基本就是最优解;要了,换 client-server。

## 来历与现状(截至 2026-09)

- 2000 年由 **D. Richard Hipp** 发布,设计目标是在嵌入式/内存受限环境提供完整 SQL;
- 2014 年宣布**公有领域**,彻底免除授权顾虑;因零依赖、极端测试与超高稳定性,成为 NASA/民航/汽车等安全敏感领域的常客;
- **最新版本 3.53.4(2026-07-24,维护版)**:修复一个 WAL 重置导致的数据库损坏漏洞,及大部分由 AI 发现的 bug;
- 3.53.x 系列新特性:新增查询结果格式化程序(QRF)库并默认用于 CLI 交互模式;TEMP triggers 现在可以修改/查询主模式表;增强 `VACUUM INTO` 与 `ALTER TABLE`(可增删 NOT NULL、CHECK 约束);
- 路线预告:**3.54.0 起放弃 Windows XP/CE** 支持,要求 Windows Vista+。

## 你可能早就在用 SQLite

- 手机系统组件、浏览器(Chrome 书签/历史本地库)、桌面软件本地存储——日常无处不在;
- **本机(Windows)**:pi 的 codegraph 代码索引库就是 SQLite——任一被索引过的仓库目录下都有 `.codegraph/index.sqlite`(例如 `C:\Users\23652\config-ai\.test\.codegraph\index.sqlite`);magic-context 的记忆库 context.db 同样是 SQLite。等学会了,`sqlite3 <那个库> .schema` 一开,自己天天用的工具内部结构直接摊开在你面前——这就是最好的练习场。

## 延伸:SQLite 在边缘(与 2027 项目衔接)

**Cloudflare D1 = 基于 SQLite 构建的无服务器数据库**,与 Workers/Pages Functions 原生集成:全球 300+ 城市节点读、内置 JSON 与全文搜索、Time Travel 时间点恢复,免费额度约每天 500 万行读 / 10 万行写 + 5 GB 存储。它解决了"单文件难分布式、无内置容灾"的短板——"SQLite 只配单机"的旧印象在边缘场景已被改写。这也是「2027-掌握边缘函数原理」项目里数据侧的前置认知,本项目的学习为此直接铺路。

## 资料来源

- sqlite.org 官方首页 / Release 3.53.4 发布日志 / News(权威口径)
- [SQLite 中文镜像 sqlite.ac.cn](https://sqlite.ac.cn)(概述/适用场景/官方书籍列表)
- [维基百科 · SQLite](https://zh.wikipedia.org/zh-cn/SQLite)(历史与特性口径)
- [菜鸟教程 · SQLite](https://m.runoob.com/sqlite/)(入门速查)
- [InfoQ · SQLite vs MySQL vs PostgreSQL 比较](https://www.infoq.cn/article/2014/04/sqlite-mysql-postgresql)(选型参考)
- [Cloudflare D1 官方页](https://developers.cloudflare.com/d1/)(边缘 SQLite 口径)
