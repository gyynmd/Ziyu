# 字域 v1.2.29 — Debug

## 内置软重启

临时 Root 模式下，首页重启按钮与挂载方式切换弹窗可确认“立即软重启”，由模块内置 `common/soft_reboot.sh` 请求本机 `ksud soft-reboot`。设置中可以启用该流程，late-load 用户自动识别。

脚本仅使用本机已安装的 KernelSU 系列守护程序；先检查 Root 身份及 `soft-reboot --help` 的命令支持。未提供接口时显示原因，保留待应用字体和挂载偏好。请求结果仅代表命令返回，不表示 Android 已完成重启或字体已生效。

已有 `emulated-soft-reboot.sh` 作为 KernelSU 重启阶段钩子，负责回收字域自己的规则、文件挂载和目录镜像，再撤销旧挂载选择。发现遗留挂载或清理不确定时，记录失败，由 `post-fs-data.sh` 阻止激活待应用字体。KernelSU 是否继续重启用户空间由本机实现决定，钩子失败不等于整个操作系统重启被取消。

请求日志：`/data/adb/modules/LuoShu/logs/soft-reboot.log`。清理和挂载结果：`logs/mount-backend.log`、`config/temporary-root-soft-reboot.conf`。诊断导出包含以上记录。

可在手机 Root 终端单独使用：

```sh
sh /data/adb/modules/LuoShu/common/soft_reboot.sh status
sh /data/adb/modules/LuoShu/common/soft_reboot.sh request
```

入口依据：[KernelSU 管理器源码](https://github.com/tiann/KernelSU/blob/main/manager/app/src/main/java/me/weishu/kernelsu/ui/util/KsuCli.kt#L454)、[软重启流程源码](https://github.com/tiann/KernelSU/blob/main/userspace/ksud/src/soft_reboot.rs)。

## 验证范围

交付报告记录静态语法检查、Debug 编译、APK 签名、内置 APK 哈希、模块清单与 ZIP 完整性。未新增或运行测试，未安装或在手机发起软重启，实际兼容情况需用户设备验证。
