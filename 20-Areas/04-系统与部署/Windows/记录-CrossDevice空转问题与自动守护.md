# 记录:CrossDevice Files "设备未响应"问题与自动守护

> 2026-09-03 处理。症状:CrossDevice Files 报"设备未响应 / 此连接已超时"。

## 发生了什么

根因是 `CrossDeviceService`(跨设备文件服务)陷入**空转重试循环**:
持续 ~30% CPU、175 个线程、250MB 内存,反复连设备/云端失败。

处理:终止进程后恢复正常。同日部署了自动守护(计划任务 `CrossDeviceGuard`,
每 3 分钟检测一次 CPU 占用,超 30% 自动 kill),日志在 `%TEMP%\crossdevice-guard.log`。

## 提醒

- 若 CrossDeviceService 又出现高 CPU(或 CrossDevice Files 再次报错)
  → 守护会自动处理,查看日志确认即可
- 若 10 分钟内被连续 kill 3 次以上(日志出现 WARN)
  → 说明该功能在本机不可用,**直接去设置里关闭"跨设备体验"**,别让它反复折腾
- 守护本身不常驻、不占资源(3 分钟一次,瞬时完成),可长期保留
