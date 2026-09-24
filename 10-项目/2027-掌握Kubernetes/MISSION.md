# Mission: Kubernetes(容器编排)

> `teach` 教学工作区协议文件,与 [项目说明](<./!项目说明.md>) 配套(项目说明管任务与进度,本文件管「为什么学」)。
> 教学决策(下节教什么、给哪些资源、设计什么练习)都回到这份文件上。

## Why

K8s 是 Docker 之后的自然下一步:当服务不止一个、还要在机器之间调度与自愈时,手写 Compose 就不够了。它也是边缘线的一环 —— KubeEdge 把 K8s 的能力延伸到边缘节点,与边缘函数同属 2027Q1 的知识树。

## Success looks like

- minikube 起本地集群,用 YAML 部署一个应用(Pod / Deployment / Service 全链路)
- `kubectl` 常用操作熟练:查状态、看日志、进容器、滚动更新与回滚
- 能讲清 K8s 与边缘计算的关系,以及 KubeEdge 在其中的位置
- 能把一个已有服务从 Docker Compose 迁到 K8s YAML

## Constraints

- 窗口 —— → 2027-03-31;当前状态:未开始(排在 Docker 之后)
- 本地资源有限:用 minikube 单节点,不上云集群
- 以 YAML 手写为主,不用 Helm 起步

## Out of scope

- 不学集群运维(etcd 备份、证书轮换、多节点网络方案)
- 不深入 CNI/CSI 插件实现
- 不学服务网格(Istio 等)

---

配套文件:[RESOURCES.md](<./RESOURCES.md>)(资源与社群)· [NOTES.md](<./NOTES.md>)(教学偏好)· `lessons/`(课程)· `reference/`(速查卡)· `learning-records/`(学习记录,按需创建)
