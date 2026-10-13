# 字域 v1.2.44 Debug

## 升级挂载选择

- 偏好读取支持明确指定模块目录，升级从新模块中读取已迁移的选择。
- 安装界面保留传入的 auto、magic、overlayfs、self_mount，停止固定写入 auto。
- 使用系统默认字体或存在外部排除标记时，也保留用户的模式选择；安装日志分别显示已保存模式和是否实际挂载。
- 启动时继续依据用户选择和本次启动验证运行，不修改自挂载和元模块的选择规则。

## 字体处理性能

- ColorOS / HyperOS 度量输出只编译 head、hhea、OS/2，以及需要修改时的 cmap；其他表保持来源字节。使用 FontTools SFNTWriter 更新字体目录、校验和及 head 校验调整。
- 避免 TTFont.save 的完整表依赖编译与第二次整文件重排；非 SFNT 容器保留原保存路径。
- 在单次处理内复用来源原始表（缓存上限 32 MiB）；ColorOS 的相同源文件复用未修改的 cmap 和 glyph order，度量表仍独立解析和修改。
- 升级迁移 safe-switch-cache，使用时继续按源文件、库存、ROM 和处理器身份验证；处理器变化仍会重新生成。
- 切换配置值改用 shell 内建读取，减少 sed/head/tr 子进程。
- 字体度量报告增加单个结果 metricsWriteSeconds；切换日志记录 rawTableReads、rawTableCacheHits、cmapCacheHits、directMetricsWrites。

本版处理器发生变化，首次应用可能重建对齐缓存。新字体与被容量限制淘汰的缓存仍需生成。
保留字重、原厂度量、CJK fallback 路由、特殊字体保护、源变化检测、热切换前后校验和失败回滚。
验证范围：静态语法、Android 编译、签名、APK/模块版本及 ZIP 完整性；未运行行为测试或手机耗时测试。
