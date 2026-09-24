# SQLite(嵌入式数据库) Resources

> 本项目教学资源的唯一清单:解释性知识只从 Knowledge 取材,不凭模型记忆。
> 校验:2026-09-24 用 curl 逐个探测(200 正常;403 是站点反爬,浏览器可正常访问)。

## Knowledge

- [SQLite 官方文档总入口](https://sqlite.org/docs.html)
  唯一权威来源。用在:任何「SQLite 到底怎么规定的」问题,优先查这里而不是博客
- [官方:Command Line Shell For SQLite](https://sqlite.org/cli.html)
  CLI 的点命令(`.tables`/`.schema`/`.mode`/`.dump`)全在这里。用在:动手操作时对照
- [官方:SQL Syntax(语言手册)](https://sqlite.org/lang.html)
  SELECT/JOIN/事务/索引的语法定义。用在:写查询卡住时
- [官方:EXPLAIN QUERY PLAN](https://sqlite.org/lang_explain.html)
  看查询有没有走索引。用在:讲清「索引为何生效」的验收环节
- [官方:Appropriate Uses For SQLite](https://www.sqlite.org/whentouse.html)
  什么该用、什么不该用,官方自己划的界线。用在:验收里「什么时候不该用」那一条

## Wisdom (Communities)

- [SQLite 官方论坛(Google Groups)](https://sqlite.org/src/wiki?name=SQLite+Forum)
  核心开发者亲自答问的地方,信号极强。用在:遇到官方文档没写清的边界情况

## Gaps

- 中文系统教程(菜鸟教程/博客园)质量参差,本项目以官方文档为主;开课时若要中文辅助再补
