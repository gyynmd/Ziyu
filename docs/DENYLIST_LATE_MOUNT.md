# 排除列表（DenyList）与自定义字体：现象、根因与延迟挂载方案

本文记录一个在 ColorOS 17 + Zygisk Next 环境下稳定复现的问题：**开启“将非 root 应用视为排除列表”后，自定义字体会整屏变成方框（.notdef）**，并给出一条不改字体文件、不改 XML 的规避方案（延迟挂载）。

## 现象

- 应用字体后一切正常；
- 打开 Zygisk Next 的“将非 root 应用视为排除列表”并完整重启后，**连状态栏、通知栏、桌面都变成方框**；
- 关掉该开关立刻恢复；
- v1.4.7 的 `ZiyuFontPreload`（预加载伴随模块）在这台机器上无效：诊断里 `state=callback-observed`、`invoked=15`、`failed=0`，但应用仍然方框；单独停用它后依旧方框。

## 证据

在“排除列表开启、方框复现”的状态下，用只读探针采集被排除应用（设置 / 微信 / QQ / SystemUI）的挂载命名空间：

- 应用命名空间里 `/system/fonts` **没有任何挂载**（`mountinfo` 为空），但目录里是**完好的原厂字体**：
  - `SysSans-Hans-Regular.ttf` = 23,648,500 字节，文件头 `00 01 00 00`；
  - `fonts.xml` / `font_fallback.xml` 的 md5 与 root 完全一致；
  - `logcat` 里没有任何字体加载错误。
- 未被排除的 **zygote** 仍然挂着模块镜像（`/system/fonts → /data/adb/luoshu/self-mount/work/system-fonts`），并且已经 mmap 了 **38,554,724 字节**的自定义字体。

| 进程 | 看到的字体 | 结果 |
| --- | --- | --- |
| 被排除的应用 | 原厂字体（命名空间被撤挂载） | 方框 |
| zygote | 自定义字体（仍挂载） | —— |
| 未开启排除列表时 | 自定义字体 | 正常 |

## 根因

不是“撤挂载后没有字体”，而是 **zygote 预载的是自定义字体、应用命名空间里却是原厂字体，两边不一致**。应用进程继承 zygote 的字体状态，渲染时拿不到可用字形，于是整屏 `.notdef`。

两个已排除的替代路径：

- `/data/format_unclear/font/OplusOSUI-*.ttf` 这条 ColorOS 设备字体链**没有被应用使用**（所有应用的 maps 里只有 `/system/fonts`，没有 `/data/format_unclear` 路径）；
- `/system` 是只读 erofs，`/data/fonts` 的字体更新需要签名（`font.fsv_sig`），也无法走。

## 延迟挂载方案

不在 `post-fs-data` 挂载，而是在开机完成后再把字体文件 bind 到 `/system/fonts`：

- zygote 启动时看到原厂字体 → 预载原厂；
- 之后启动的普通应用看到 bind 后的自定义字体；
- 被排除的应用启动时撤挂载，命名空间里是原厂字体 → 与原厂 zygote 一致，**不再方框**（代价：这些应用显示原厂字体）；
- 系统 UI / 桌面在挂载前启动，需要重启一次才会用上自定义字体。

### 最小实现

```sh
#!/system/bin/sh
# 等开机完成（zygote 已经启动）
_i=0
while [ "$(getprop sys.boot_completed 2>/dev/null)" != "1" ] && [ "$_i" -lt 180 ]; do
    sleep 2
    _i=$((_i + 2))
done
sleep 3

SRC=/data/local/tmp/latefont.ttf
[ -s "$SRC" ] || exit 0

for n in SysSans-Hans-Regular.ttf SysSans-Hant-Regular.ttf SysSans-En-Regular.ttf \
         SysFont-Hans-Regular.ttf SysFont-Hant-Regular.ttf SysFont-Regular.ttf \
         SysFont-Static-Regular.ttf OPSans-En-Regular.ttf OSans-Solid-Digits-VF.ttf \
         Roboto-Regular.ttf RobotoFlex-Regular.ttf RobotoStatic-Regular.ttf \
         SourceSansPro-Regular.ttf SourceSansPro-SemiBold.ttf SourceSansPro-Bold.ttf; do
    dst="/system/fonts/$n"
    [ -e "$dst" ] || continue
    [ -L "$dst" ] && continue      # 这 4 个是 ColorOS 的设备字体软链，跳过
    mount -o bind "$SRC" "$dst"
done
```

卸载时对同样的路径 `umount` 即可。实测 11 个真实文件 bind 成功、4 个软链跳过。

### 实测结果（一加 PJZ110，ColorOS 17）

- 被排除的应用（设置 / 微信 / QQ）：原厂字体，无方框；
- 挂载后启动的普通应用：自定义字体；
- 系统 UI 与普通应用字体不同（因为启动早），重启 SystemUI 后一致。

## 与现有后端的关系

延迟挂载属于挂载后端的一种新策略，可归入 #254「通用字体引擎重构」Phase 7（Unified Mount Backends）：

1. 新增“延迟挂载（排除列表兼容）”后端：在 service 阶段 bind，而不是 `post-fs-data`；
2. 或增加“排除列表兼容模式”开关，检测到 DenyList 启用时自动切换；
3. 延迟挂载与现有自挂载共用同一份 payload，避免重复拷贝；
4. 现有 `self-directory-mirror` 每次开机会复制整个字体目录（约 200MB），延迟挂载可直接 bind 单文件，开销更小。

## 限制

- 被排除的应用无法同时使用自定义字体（由 Zygisk 撤挂载机制决定，属预期）；
- 系统 UI 需要重启 SystemUI / 桌面才能应用新字体；
- 每次开机都要重新 bind；
- 不同 ROM 的 `/system/fonts` 文件清单可能不同，需要按实际清单调整。

## 复现与验证

- 复现：ColorOS 17 + Zygisk Next，开启排除列表并重启；
- 验证：用只读探针分别采集被排除应用与 zygote 的 `/proc/<pid>/mountinfo`、`/proc/<pid>/maps`，确认“应用无挂载但为原厂字体、zygote 有挂载且映射自定义字体”；
- 修复验证：延迟挂载后，被排除应用显示原厂字体且无方框，普通应用显示自定义字体。
