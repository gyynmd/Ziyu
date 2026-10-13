# 字域 v1.2.30 — Debug

## OverlayFS 兼容处理

- 源目录先解析真实路径，以只读多 lower 层挂载；不引入可写 upper/work。
- 按 `/sys/module/overlay/parameters` 暴露的能力构造兼容组合：`index=off`、`metacopy=off`、`nfs_export=off`、`redirect_dir=nofollow`。只发送具有对应参数入口的选项，并保留基本参数尝试。
- 存在 Android 旧版 `override_creds` 参数入口时，增加 `override_creds=off` 组合；不把这一语法强加给接口不同的上游内核。
- lower 原目录 bind 立即登记到事务账本，再隔离传播。兼容 Android Toybox 的 `-o private -t none none <lower>`，保留 util-linux 的 `--make-private` 尝试，并校验挂载表中的传播标志。
- lower 保存或隔离失败即停止该事务。OverlayFS 参数全部拒绝时，明确选择 OverlayFS 的用户仍得到失败及回滚，不自动改用元模块或目录镜像；字域自挂载保留其既有 bind/镜像后续路径。
- OverlayFS 命令成功仍须通过组件内容和 PID 1 负载验证，不能仅凭 mount 返回 0 宣称字体已应用。

## 已补齐的日志及清理问题

- 新增 `common/mount_diagnostics.sh`：记录每步命令参数、退出码和原始 stdout/stderr；记录文件系统、剩余空间、SELinux 标签、内核版本、进程凭据、两份挂载命名空间及 OverlayFS 参数。
- `logs/mount-diagnostics.log` 达到 1 MiB 后在下一次环境快照前保留为 `.previous`；诊断包含当前与上一份尾部。内核日志只保留 OverlayFS、AVC 拒绝及 Root/NoMount 相关尾部，采集失败记录返回码及错误；历史快照不能单独证明某次失败的原因。
- 诊断导出补齐原先缺少的 `self-mount.log`、`self-mount-required.conf`、本机挂载账本与 boot-id、PID 1 挂载表及 Universal/字体路由日志。空文件、缺失和不可读分别说明。
- 用户自主运行的 `font_partition_compat_report.sh` 同步加入只读能力和内核快照，以及未经关键字删减的挂载诊断尾部；它不执行挂载。
- 组件/PID 1 内容验证失败记录具体文件、读取或内容不匹配、大小和快速指纹。bind、镜像挂载、只读重挂载及普通回滚保留命令原始错误。
- 所有 OverlayFS 尝试失败后不再忽略 lower 卸载结果并直接递归删除。统一回滚确认两个命名空间没有私有负载或工作目录挂载后才清理工作目录；无法确认时保留现场并报告回滚未确认。
- 旧 boot-id 下仍可见工作目录挂载时拒绝清空账本；避免清理来源不明的当前挂载。

## 使用与证据范围

更新匹配模块和 App 后，选择 OverlayFS，确认重启/软重启验证。若仍失败，通过 App 导出本次诊断日志；重点查看 `self-mount.conf`、`self-mount.log` 与 `mount-diagnostics.log`，区分 lower 准备、OverlayFS 参数拒绝、文件内容/PID 1 不匹配和回滚失败。

此前 PLK110 的 EINVAL 只证明原诊断里的挂载组合失败，不能在缺少具体内核报错时证明所有 OverlayFS 实现永久不可用。本版参数是否能在该设备成功，仍须真机验证。

依据：[Linux OverlayFS 文档](https://docs.kernel.org/filesystems/overlayfs.html)、[Android override_creds 补丁说明](https://android.googlesource.com/kernel/common-patches/+/4a4ab33ba32e1b03a02f3ea8aee45308509249fb/android-mainline/ANDROID-overlayfs-override_creds-off-option-bypass-creator_cred.patch)、[Toybox mount 源码](https://github.com/landley/toybox/blob/master/toys/lsb/mount.c)。

交付检查范围：Shell 静态语法、Debug 编译、APK 签名、版本、内置 APK SHA-256、模块清单及 ZIP 完整性。未新增或运行测试，未在手机安装、挂载或重启。
