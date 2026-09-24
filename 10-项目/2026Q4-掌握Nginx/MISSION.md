# Mission: Nginx(静态服务 / 反向代理 / 负载均衡)

> `teach` 教学工作区协议文件,与 [项目说明](<./!项目说明.md>) 配套(项目说明管任务与进度,本文件管「为什么学」)。
> 教学决策(下节教什么、给哪些资源、设计什么练习)都回到这份文件上。

## Why

Nginx 是「把服务暴露出去」的默认答案:本库将来要部署的边缘函数、Docker 里的 web 服务、VPS 上的代理链路,前面都站着它。读懂 `nginx.conf` 是从「会跑」到「会配」的分界线。

## Success looks like

- 给本地一个服务配上反向代理 + 域名 + HTTPS,并能解释每个 `location` 块为什么这么写
- 能独立排查一次 502 / 504:知道该看哪层日志、常见成因是什么
- 能配出负载均衡(upstream 多后端)并验证分发效果
- 能讲清 Nginx 的事件驱动模型为什么比「一请求一进程」更省资源

## Constraints

- 窗口 —— → 2026-12-31;当前状态:未开始
- 练习环境:本机 + 已有 VPS;域名与证书用真实域名验证
- 与 Docker 项目串联:后端服务尽量跑在容器里

## Out of scope

- 不深入 Nginx 模块开发(C 模块编译)
- 不学 OpenResty/Lua 扩展
- 不学云厂商负载均衡产品(ALB/CLB 等)

---

配套文件:[RESOURCES.md](<./RESOURCES.md>)(资源与社群)· [NOTES.md](<./NOTES.md>)(教学偏好)· `lessons/`(课程)· `reference/`(速查卡)· `learning-records/`(学习记录,按需创建)
