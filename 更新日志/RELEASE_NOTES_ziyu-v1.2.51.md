# 字域 v1.2.51 Debug（已有正式签名）

原 Debug 配置总是加 .debug applicationIdSuffix，正式 App 与 Debug 被 Android 视为两个包。
本版在已有正式签名配置齐全时使用正式 applicationId，仍通过 assembleDebug 构建，版本名
1.2.51-debug。证书必须与既有正式工作流相同，不生成或替换密钥。

本机使用已有 ZiyuSigning 密钥及 Windows 加密密码；云端 Debug 发布复用正式签名 secrets。
未配置正式签名时仍允许独立开发 Debug，以免默认 Android Debug 签名伪装成可覆盖正式版。
模块安装器已使用 pm install -r，无需修改安装逻辑或删除 App 数据。

有旧 .debug 独立 App 的用户可手动卸载旧独立 Debug 一次；本版不自动卸载任何 App。
正式包与本版共享数据及递增 versionCode，后续正式版本也须高于已安装 Debug 版本。

保留 v1.2.50 字体桥接链验证和优化，没有更改字体挂载、回滚或系统缓存刷新。
交付独立 APK 和内置同一 APK 的模块 ZIP；检查正式证书、包名、版本、内置摘要、
运行源码一致性与 ZIP CRC。未运行行为测试或云端工作流，未安装/刷入本版。
