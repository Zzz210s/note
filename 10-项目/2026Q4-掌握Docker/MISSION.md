# Mission: Docker(容器化)

> `teach` 教学工作区协议文件,与 [项目说明](<./!项目说明.md>) 配套(项目说明管任务与进度,本文件管「为什么学」)。
> 教学决策(下节教什么、给哪些资源、设计什么练习)都回到这份文件上。

## Why

容器化是「把本地跑通的东西变成别人也能跑起来的东西」的最短路径,也是边缘函数线的支撑层(Docker 与 K8s、边缘函数同属 2027Q1)。本库自己的工具链(巡检器、脚本)迟早也要能一键跑起来。

## Success looks like

- 用 Dockerfile + Compose 把一个自写小服务跑起来,并解释镜像/容器/网络/卷的关系
- 能读懂并写出多阶段构建,把镜像体积压下来
- 能排掉常见故障:端口不通、卷权限、容器内看不到宿主机文件、镜像缓存不生效
- 能在服务器上部署一个完整小项目(与 Nginx 项目串联)

## Constraints

- 窗口 —— → 2027-03-31;当前状态:未开始
- 练习环境:本机 Windows(WSL2 或 Docker Desktop)+ 一台 VPS
- 以真实服务为练习对象(优先本库工具与已有 VPS 上的服务)

## Out of scope

- 不深入容器运行时实现(namespace/cgroup 只到能解释隔离原理)
- 不做 Swarm/自建 Registry 集群等企业级话题
- 不学 K8s —— 那是 `2027-掌握Kubernetes`(本项目只到「知道它解决什么」)

---

配套文件:[RESOURCES.md](<./RESOURCES.md>)(资源与社群)· [NOTES.md](<./NOTES.md>)(教学偏好)· `lessons/`(课程)· `reference/`(速查卡)· `learning-records/`(学习记录,按需创建)
