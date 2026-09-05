# pi 如何设置与更新会话名

来源:pi 官方文档 docs/sessions.md、docs/session-format.md(pi 0.84)。

## 会话名是什么

每个 pi 会话默认没有名字,在 `/resume`(或 `pi -r`)的会话选择器里只显示首条消息作预览。设置"会话显示名"后:

- `/resume` / `pi -r` 列表里直接显示这个名字,不再只靠首条消息辨认;
- 底部状态栏(footer)也会展示当前会话名;
- 底层是 JSONL 会话文件里的 `session_info` 记录(`name` 字段)。

## 方法一:会话内命令 `/name`(最常用)

正在会话里时,直接输入斜杠命令改名:

```text
/name 重构 auth 模块
/name CI 审计
```

回车即生效,无需重启。用 `/session` 可查看当前会话文件、ID、消息数与 name 等元信息。

## 方法二:启动时指定 `--name` / `-n`

```bash
pi --name "重构 auth 模块"
pi -n "CI 审计" -p "Review this build failure"   # -p 为起始提示词
```

适合开启一个新任务会话时顺手命名。

## 方法三:在恢复选择器里改(改历史会话的名字)

`/resume` 或启动时 `pi -r` 打开会话选择器:

- 输入即搜索;
- `Ctrl+R`:重命名选中的会话(只改显示名,不改文件名);
- `Ctrl+N`:只看已命名的会话;
- `Ctrl+D`:删除(需确认,优先走 trash);
- `Ctrl+P`:切换显示完整路径;
- `Ctrl+S`:切换排序方式。

在会话外也能给任何历史会话补名字,不需要先进那个会话。

## 底层存储(一般不手动改)

会话按工作目录分文件夹保存在:

```text
~/.pi/agent/sessions/
  --C--Users-23652--/                      <- 目录路径转义后的文件夹
    2026-09-02T09-46-29-607Z_<id>.jsonl    <- 时间戳_会话ID.jsonl
```

每个会话是一个 JSONL 树文件,显示名存在其中一条记录里:

```json
{"type":"session_info","id":"...","parentId":"...","timestamp":"...","name":"重构 auth 模块"}
```

正常改名走上面的 `/name` 或 `Ctrl+R` 即可,不建议直接编辑 JSONL(会破坏树结构,且需重开 pi 才重读)。

## 相关命令速查

| 命令/参数 | 作用 |
|-----------|------|
| `/name <名字>` | 给当前会话设置/更新显示名 |
| `pi --name <名字>` / `pi -n` | 启动时命名 |
| `/session` | 查看当前会话信息(文件、ID、name、tokens、cost) |
| `/resume`、`pi -r` | 打开历史会话选择器(内可用 Ctrl+R 改名) |
| `/tree` | 会话树内跳转(不影响名字) |
| `/new` | 开新会话 |

## 小结

更新当前会话名就用 `/name`;补改历史会话名就用 `/resume` 里 `Ctrl+R`;自动化/脚本场景可用启动参数 `pi --name`。三者写的是同一处 `session_info.name`,优先级为最近一次设置覆盖。
