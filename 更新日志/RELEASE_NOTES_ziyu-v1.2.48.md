# 字域 v1.2.48 Debug

## 截图对应的依据

历史只读日志 `diagnostics/20261010-122022-partial-live-readonly/backend-task-live.txt`
记录 checkedFonts=14、appliedCount=12、failures=[]；仅 SysFont-Hans-Regular.ttf 和
SysFont-Hant-Regular.ttf 的 physical-slot-route-not-proven 提示。结合验证器源码：
这两个文件已通过源内容、PID 1 可见内容、可读权限和挂载路径检查，缺少加载路径依据。
这不等于整个 system 分区挂载失败，也不能证明每个应用已经绘制新字体。

原验证器只为 Latin / digit 补验 OEM 直接槽位，排除了 CJK；随后把所有未确认加载
路径的已挂载文件加入 unappliedFonts，App 又统一显示“部分位置未应用”。

## 修复

- OEM 中文直接槽位可参与验证。必须在 ready 原厂清单中记录同一个完整路径，
  来源是原厂 XML / 受验证扫描，格式为 TTF / OTF / TTC，正常样式且 stock metrics
  具有不少于 512 个汉字的覆盖。只存在于候选列表或模块生成目录的名字不被认定。
- 无依据的槽位继续保持提示，不能通过改写原厂清单或删除校验制造通过结果。
- 增加 mountedFonts / mountedCount、unconfirmedFonts / unconfirmedDetails、routeEvidence。
  unappliedFonts 仅记录未通过挂载文件检查的槽位，appliedFonts 保留加载路径已确认语义。
- 现有 partial 及警告处理流程保留。界面统一使用“有提示”，正文显示具体的挂载数量、
  加载路径已确认数量、待确认及挂载未通过的数量，不擅自宣称全部已加载。
- SystemUI 缓存检查包含全部挂载通过的槽位。解析绝对链接时始终留在目标进程的
  namespace，避免读取到调用进程的其他字体视图。

## 不改变生成结果的优化

- 一轮验证只读取一次动态分区配置，不为每个字体清单条目重新读取。
- 同一 XML 中重复的 VF 声明按文件路径、字体族、语言去重，避免为各个字重重复
  解析同一加载路径；保留不同字体族、语言、XML 文件之间的检查和原有查找顺序。
- 输出 routeScan 统计检查 / 复用次数，便于后续设备日志评估。
- 同一进程的缓存检查复用已解析的可见路径身份；仍逐条检查映射对象和进程存活身份。
- 日志页独立状态查询并行，保留各自超时与失败结果；不并行修改字体或挂载。

## 范围与待确认

用户暂时不能连接设备，本次以历史日志和源码为依据。对原厂清单尚未记录的 OEM
主题链接，例如旧日志中离开字体分区的 /data/format_unclear/font 路径，继续标为
加载用途待确认；不把可变主题文件当成原厂度量，不擅自挂载或写入该目录。

构建生成可安装 Debug APK 和内置同一 APK 的模块 ZIP，进行语法、编译、版本、
签名及打包完整性检查。不新增或运行行为测试，没有安装、刷模块、重启或速度实测。
