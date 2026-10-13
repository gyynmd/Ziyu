# 字域 v1.2.33 — Debug

- 补齐 OEM 前缀字体 XML 库存发现，包括小米报告中的 hyper_fonts、hyper_font_fallback、miui_fonts、miui_font_fallback、mi_fonts_customization、misans_variable_fonts。
- 库存扫描修订号升级到 6；旧库存补采遵守可信原厂视图规则，避免把当前替换字体记录成原厂度量。
- 独立分区诊断脚本支持跨共享字体分区解析相对文件名，并注明解析结果是可读候选。system_ext/fonts 不存在时不再直接把其 XML 引用的全部字体视为缺失。
- RMX5200 所给报告中的最终状态为 NoMount 验证通过；小米报告缺少具体字体清单、PID 1 与挂载结果。本版不宣称这两个型号已通过新版安装及重启验收。
