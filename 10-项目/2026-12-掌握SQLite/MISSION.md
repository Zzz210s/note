# Mission: SQLite(嵌入式数据库)

> `teach` 教学工作区协议文件,与 [项目说明](<./!项目说明.md>) 配套(项目说明管任务与进度,本文件管「为什么学」)。
> 教学决策(下节教什么、给哪些资源、设计什么练习)都回到这份文件上。

## Why

零配置单文件,是练 SQL 与数据库原理成本最低的入口;而且这台机器上已经有一堆 SQLite 在跑(pi 的 codegraph 索引库、magic-context 的记忆库、浏览器的 History)。学会它,既能读懂自己每天在用的工具,又能为 2027 的边缘函数线(Cloudflare D1 就是 SQLite)打地基。

## Success looks like

- 用 CLI 与一门语言(Python `sqlite3` 或 Node `node:sqlite`)建库建表、写查询、上索引、开事务
- 写出 5 条有分量的查询(含 JOIN 与聚合),并说明索引为何生效(`EXPLAIN QUERY PLAN` 说得清)
- 能打开并读懂一个**真实存在**的库:列出表、读出 schema、查一条数据
- 能讲清「什么时候该用 SQLite、什么时候不该用」——包括并发写入、网络文件系统这些坑

## Constraints

- 窗口 2026-12-01 → 2026-12-31(撞期顺延,以根 `00-索引.md` 学习路线为准)
- 每天投入有限,课程要短、要能当场跑出结果
- 实战锚点用本机已有的真实 SQLite 库(先复制副本再动手,不直接改原库)

## Out of scope

- 不学 MySQL/PostgreSQL 的服务端运维(那是另一条线)
- 不深入 B-tree 与页结构实现(只到「索引为什么快」的原理层)
- 不学 ORM 框架(先手写 SQL)

---

配套文件:[RESOURCES.md](<./RESOURCES.md>)(资源与社群)· [NOTES.md](<./NOTES.md>)(教学偏好)· `lessons/`(课程)· `reference/`(速查卡)· `learning-records/`(学习记录,按需创建)
