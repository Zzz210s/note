---
type: tutorial
tags: [java, gradle, vscode, jdk, 版本兼容, 工具链]
status: done
date: 2026-09-05
---

# VS Code Java 扩展报错修复:Gradle 与 JDK 版本不匹配

> 适用:VS Code 打开 Gradle 项目时弹 "Can't use Java 26 and Gradle 8.x to import Gradle project",或任何 Java 扩展与 Gradle 版本冲突提示。
> 实测背景:2026-09-05,uhabits 项目(Gradle wrapper 8.11.1 + AGP 8.9.2),机器装有 JDK 26(Oracle)与 JDK 21(Temurin,scoop),VS Code 1.x + Language Support for Java。
> 一句话本质:Java 与 Gradle 各有版本支持上限,且 VS Code Java 扩展有一套独立的 JDK 探测链——报错往往发生在"探测链拿到过新的 JDK"而 Gradle daemon 实际用的是另一个 JDK 的场景。

## 一、版本兼容核心表(2026-09 实测查证)

- Gradle 能**运行**的最高 JDK:Java 24 需 Gradle 8.14,Java 25 需 Gradle 9.1,Java 26 需 **Gradle 9.4.0**(Gradle 8.x 全家最高只到 Java 24)
- Android Gradle Plugin(AGP)与 Gradle 最低版本:AGP 8.9 -> Gradle 8.11.1;AGP 9.0 -> Gradle 9.1.0;AGP 9.2 -> Gradle 9.4.1
- 推论:想用 Java 26 跑 Android 项目 = Gradle 9.4+ **且** AGP 9.2+,是 AGP 9 大迁移,普通项目不值

## 二、根因:两条 JDK 链

| 链 | 决定什么 | 本机实际指向 |
|---|---|---|
| Gradle daemon 实际 JDK | 谁能跑 daemon | 用户级 `~/.gradle/gradle.properties` 的 `org.gradle.java.home`(此处为 Android Studio 的 JBR 21) |
| vscode-java 检查用 JDK | import 前的版本匹配检查 | 自己的优先级链,当时落到 PATH 的 JDK 26 |

结果:Gradle daemon 一直跑在 JBR 21 上没问题,但 vscode-java 的检查看到 26 与 Gradle 8.11.1 不匹配,import 前就弹错(误报,它看不到 org.gradle.java.home)。

## 三、修复(最小侵入路线)

1. 装一个与项目 Gradle 兼容的 JDK(推荐 LTS):`scoop bucket add java && scoop install temurin21-jdk`
   - 路径形如 `C:\Users\23652\scoop\apps\temurin21-jdk\current`
2. VS Code **用户设置** `settings.json` 加(该键在 vscode-java JDK 链中优先级最高,只影响 Gradle daemon 的选取):

```json
"java.import.gradle.java.home": "C:\\Users\\23652\\scoop\\apps\\temurin21-jdk\\current"
```

3. 验证:命令行 `JAVA_HOME=<jdk21> ./gradlew --version`,应看到 `Launcher JVM: 21.x`
4. VS Code 里 `Developer: Reload Window`;仍弹则 `Java: Clean Java Language Server Workspace` 后重载

效果:用户级全局生效,之后任何 Gradle 8.x 项目都不会再被这条检查误伤;系统 PATH 的 java、Android Studio JBR 均不受影响。

## 四、坑与备注

- 报错文案里的 Gradle 版本可能与 wrapper 实际版本不一致(可能来自扩展缓存/其它项目),以 `gradle/wrapper/gradle-wrapper.properties` 为准
- 用户级 `~/.gradle/gradle.properties` 的 `org.gradle.java.home` 会决定 daemon 真实 JVM(命令行/CI 都生效),但**不影响 vscode-java 的检查**,两条链要分别对齐
- 若项目真要 Java 26:升级路径是 Gradle 9.4+ + AGP 9.2+(Android 项目),涉及 AGP 9 DSL 迁移,另当别论
- 卸载/换版本:`scoop uninstall temurin21-jdk` 并删掉 settings.json 对应键

## 相关与复习

- 内存/daemon 堆积问题见 [[Windows内存与磁盘优化记录-2026-09]] 同批排查思路(Java 多进程常驻也占 16G 内存,需配合 daemon 清理)
