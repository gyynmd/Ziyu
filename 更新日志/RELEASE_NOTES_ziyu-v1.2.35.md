# 字域 v1.2.35 — Debug

- 实机启动日志确认：OverlayFS 已进入 F2FS 兼容路径，但 BusyBox mke2fs 报 invalid option -- t，导致 ext4 下层生成失败并回滚。
- 用绝对路径选择系统完整 e2fsprogs 格式化工具，绕过 KernelSU/SukiSU BusyBox standalone 的 applet 优先解析。
- 记录格式化工具路径、版本、镜像分配结果；缺少完整工具时给出具体失败阶段。
- 保留用户选定的 OverlayFS 后端及原子回滚，不改选 NoMount 或元模块。
- 包含 v1.2.34 的日志警告忽略和字体结果显示修复。

验证与交付范围另见本次设备诊断报告及 package-verification.json。不将隔离环境验证视为刷入后完整启动验收。
