# NOTES

> 教学偏好与工作笔记。设计课程前先读这份文件。

## 教学偏好(全局,用户已确认)

- **语言与格式**:中文输出;**不用 emoji**;概念讲解固定三段式「**为解决什么痛点而生 / 一句话定义 / 大白话注解**」
- **文档风格**:结论先行、表格优先;能一段说清就不列清单;具体胜过形容
- **笔记归属**:成品知识写进 `20-领域/`(项目层只留脚手架与过程记录);名词与概念辨析进 `20-领域/10-名词解释/`
- **链接**:正文互连用 `[[双链]]`;MOC / 索引 / README 用相对路径链接
- **篇幅**:代码文件 ≤200 行;`.md` 笔记不限长
- **每节课的硬要求**:① 一个当场可验证的小胜利 ② 等长选项的测验(反馈闭环) ③ 一手资源引用 ④ 结尾提醒"随时追问"
- **一手资源优先**:解释性内容只从 `RESOURCES.md` 取材,不凭模型记忆;找不到就写进 Gaps

## 本项目专属

- (待记:用户说过的、只针对这个项目的偏好)

## 环境就绪状态(2026-09-25 实测)

- **已修**:Docker 守护进程原本没起来(报 `failed to connect to the docker API`);已启动并验证过(Server 29.2.1 ✓),验证完已停止以省内存
- 已预拉课程要用的镜像:`alpine:latest`(13 MB)、`nginx:alpine`(94.4 MB)
- **注意**:Docker Desktop 现在**不会开机自启**,所以每次上课都要先手动启动;不启动就执行 docker 命令,会报 `failed to connect to the docker API`
- **开机自启已关**(2026-09-25):Docker Desktop 常驻约 1~2 GB 内存,已从 HKCU Run 键移除自启项,并已停止运行
- **上课前先启动**:开始菜单搜 Docker,或命令行 `docker desktop start`(等守护进程就绪:`docker version` 能同时打印 Client 与 Server)
- **下课后释放内存**:`docker desktop stop`
- 想恢复开机自启:把 `C:\Program Files\Docker\Docker\Docker Desktop.exe` 加回 HKCU Run 键,或在 Docker Desktop 设置里勾选 Start Docker Desktop when you sign in
