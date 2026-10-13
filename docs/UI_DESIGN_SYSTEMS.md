# Ziyu UI 设计体系

本文说明应用内 Material 3、MIUIX KMP 与 COUI KMP 三种界面的实现边界。三种风格共用业务页面状态和动作，但由各自的主题、控件、排版、布局令牌、导航与弹层负责呈现。

## 风格选择与主题

- `LocalUiStyle` 是当前界面的唯一风格来源；页面和组件不得自行读取持久化设置来重复判断。
- `ZiyuTheme` 根据该风格安装 Material 3、`MiuixTheme` 或 `COUITheme`。MIUIX 与 COUI 使用各自的颜色方案、文本样式、主题控制器和弹出层宿主。
- `MaterialTheme` 在 MIUIX/COUI 下只为仍以 Material 3 类型表达的旧业务参数提供语义桥接，例如错误色、间距文字角色和 `ButtonColors`。实际显示的文字、按钮、输入框、弹层等必须进入对应的原生分支。
- Material 3、MIUIX 与 COUI 各有独立的字体比例、桥接形状及 `ZiyuLayoutMetrics`。页面边距、卡片间距、控件间距和底部导航安全空间通过 `LocalZiyuThemeTokens.current.layout` 读取，不要在新页面重复硬编码整页尺寸。

## 组件分层

`ui/design` 保存兼容现有业务调用方式的样式分发器。添加或迁移控件时，应保持回调、禁用/选中/错误状态、内容颜色、无障碍语义和 `Modifier` 行为，并在三个分支分别调用相应 UI 库的控件。

| 组件 | 入口 | MIUIX / COUI 呈现 |
| --- | --- | --- |
| 文字、图标 | `ZiyuText.kt` | MIUIX `Text`/`Icon` 或 COUI `Text`/`Icon`，使用原生文本角色 |
| 按钮、图标按钮 | `ZiyuActions.kt` | MIUIX/COUI Button 与 IconButton，采用各自的颜色和按压反馈 |
| 开关、复选、单选、滑块、输入框 | `ZiyuInputs.kt` | 按状态映射到相应原生控件；整行开关保留可点击与无障碍状态，填充/轮廓文本框保留各自表面与边框差异 |
| 列表项、进度、分隔线 | `ZiyuLists.kt`、`ZiyuProgress.kt` | 列表进入 MIUIX/COUI `BasicComponent`，插槽继承各自内容角色；进度与分隔线由活动主题提供 |
| 对话框、底部弹层、菜单 | `ZiyuDialogs.kt`、`ZiyuSheets.kt`、`ZiyuMenus.kt` | MIUIX/COUI 使用原生 Overlay 组件；Material 页面继续使用 Material 3 |
| 卡片、标签页 | `ui/theme/ZiyuCard.kt`、`ZiyuTabs.kt` | 原生卡片形状/反馈和各自的标签控件 |

`LocalZiyuContentColor` 与 `LocalZiyuTextStyle` 用来把原生容器的内容色和文字角色传入业务插槽。新建原生容器时，检查其标题、图标、按钮和辅助说明是否都在该作用域内正确继承颜色。

## 页面与业务状态

Home、字体库、组合、日志和设置页面继续调用既有 Route、ViewModel、仓储与动作回调。UI 风格只决定呈现；切换风格不得改变字体导入/应用、排序筛选、配置持久化、日志、备份、更新或 Root 操作。

Route 显式分发三种呈现，状态、筛选和业务动作仍由同一个 Route/ViewModel 持有。首页使用三个独立页面入口与各自的编排：Material 的色调预览和功能卡片、MIUIX 的大标题和分组列表、COUI 的紧凑预览与设备摘要；完整的任务、恢复、挂载、撤销和原厂扫描动作通过共享业务区块保留。

字体库共用搜索、筛选、排序、工具和详情状态。三套主题都使用一行一款字体的纵向列表，预览与操作区域保持相近尺度；卡片、按钮与文字角色按活动主题呈现。主要筛选使用“全部、收藏、组合、可变”等短标签，筛选状态与逻辑不变。任务页保留完整的任务/问题/日志页签、原始输出、复制、取消、回退、警告忽略和诊断导出；头部、指标与记录行采用当前设计体系。组合页保留 Material 专属实现，MIUIX/COUI 使用不同的预览选择与表单编排，共用字体轴和生成业务。

共享业务区块和列表构建器是明确的复用边界，不复制三份业务状态，也不声称所有页面完全没有共用的 Compose 结构。

令牌迁移按活动 Route 推进：页面宽度、纵向节奏、卡片内边距和导航安全区已由 `LocalZiyuThemeTokens.current.layout` 按主题提供；部分旧页面仍有局部固定尺寸和业务预览参数。扩展或大规模调整页面时，优先迁移到主题令牌，避免把当前覆盖范围描述为所有尺寸都已集中管理。

导航栏由 `ZiyuAppShell` 按风格分别调用 Material、MIUIX 和 COUI 导航组件。弹出层宿主只在 `ZiyuTheme` 根部安装一次，页面不得重复创建全局宿主。

三套主题的悬浮底栏都接收同一页面 backdrop。Material 和 COUI 用 `ZiyuGlassDockSurface` 绘制半透明、模糊与折射，导航内容仍分别使用各自原生组件；Material 将原生导航项直接放进玻璃容器，避免内层 NavigationBar 再铺一层表面；完整玻璃绘制层裁切到同一个圆角轮廓，避免 surface 回调留下矩形内底；MIUIX 保留既有滑动玻璃底栏并将填充裁切到胶囊轮廓。玻璃开关决定是否启用半透明与折射，模糊开关只决定模糊效果；关闭模糊时提高表面 tint，避免页面文字透出，模糊仍可单独关闭。RuntimeShader 效果需要 Android 13 以上和设备渲染支持，不支持时保留普通可用底栏。关闭悬浮底栏后使用各主题常规底栏，玻璃相关设置暂停生效而不清除偏好。

纯黑开关在实际深色模式下将三主题根页面背景设为 `Color.Black`。Host 与页面使用同一个背景令牌，卡片保留独立深色表面；纯黑不强制覆盖用户选择的浅色模式。跟随系统时，是否启用深色以设备系统设置为准。

## 动效、性能与无障碍

- 动效由 `ZiyuMotion.kt` 集中定义；按可见/活动状态触发有限动画，避免隐藏页、未选中标签或静止页面持续重组。
- 页面与控件在组合期间只读取必要状态。昂贵的筛选、展示列表和映射应以输入状态为 key 使用 `remember`；动画状态不要重复由页面与控件同时驱动。
- 保持每个操作原有可点击范围、enabled 状态、键盘/返回键关闭、底部弹层拖动关闭与滚动行为。图标按钮需要描述性语义；开关行暴露 `Role.Switch` 和当前选中状态。
- 编译和打包只能确认源码/API/产物可用，不代表真实设备上的手势、动画帧率、键盘避让或视觉验收。每个 UI 库升级后需重新核对它的公开 API 和真机表现。

MIUIX/COUI 原生 Overlay API 没有 Material 的全部窗口与遮罩参数。原生 AlertDialog 使用各自库的尺寸、形状和系统遮罩；Material `DialogProperties` 的平台宽度/窗口标志不能一一映射，原生 API 也无法在回调中区分返回键和点外部关闭。原生 BottomSheet 使用库默认遮罩、形状和表面效果；`sheetGesturesEnabled` 关闭拖拽时仍保留返回键关闭。Material 页面继续完整使用 Material 3 对应参数。

## 表面、文字和形状契约

- MIUIX/COUI 普通卡片使用各库 CardDefaults 对应的 `surfaceContainer`，将半透明容器色在页面背景上合成一次；AMOLED 模式保留独立的深色卡片表面。页面背景来自活动主题，不叠加固定的装饰渐变。
- 普通卡片默认使用随浅色/深色表面变化的 0.75dp 描边。原生默认卡片的描边和阴影都沿原生 squircle 绘制，自定义 Shape 卡片沿同一 Shape 绘制。阴影使用各主题的 `cardElevation`；调用方显式提供的描边仍优先。首页分组、状态卡和组合通知等 Surface 卡片显式复用相同边界令牌，普通图标底座和列表行不自动加卡片边框。
- 控件拥有自身插槽的前景色。按钮不得继承父卡片的文字色来覆盖 `onPrimary` 或 disabled 色；外部明确传入的文字色仍受支持。
- MIUIX 标签栏使用透明未选背景和明显的选中容器色，避免默认白色矩形露出或选中项与父卡片融合；行高使用各库的默认值，除非具体页面显式指定。
- Material 顶栏操作使用透明原生 IconButton，不叠加额外的带阴影 Surface。固定和滚动标签栏都使用透明容器，避免默认 surface 形成大片白底。
- 默认卡片和按钮采用原生 squircle，描边沿同一原生路径绘制。调用方显式请求任意 `Shape` 时，通过同一库的 `Surface` 保证背景、裁剪和边框一致；该路径属于自定义形状兼容适配，不冒充库默认 Button/Card 外观。
- 原生列表操作通过 `ZiyuListItem.onClick`、`enabled` 与 `onClickLabel` 传入 `BasicComponent`，保留原生点击反馈和按钮语义；不要额外叠加另一层整行点击处理。
- 输入框未指定形状时保留原生默认外观。显式形状同时控制填充、裁剪与描边；COUI 1.1.0 的自定义 outlined 适配使用 `None` 去除内部轮廓并保留 Rectangle 内边距，浮动标签字重因此采用库的普通字重。输入、焦点、错误与键盘状态仍由原生字段负责。
- 字体文件名使用信息文字角色，实际字体样本使用预览文字角色。预览字体的字号与字体轴属于字体对比参数，不能等同于应用界面文字比例。

## 新页面迁移约定

1. 从 `LocalUiStyle` 读取当前风格，不在业务层复制三份状态逻辑。
2. 页面控件优先导入 `ui.design.Ziyu*` 入口，卡片使用 `ZiyuCard`，标签使用 `ZiyuSegmentedTabs`。
3. 检查新增组件在 Material、MIUIX、COUI 中都有真实呈现分支；不要在非 Material 风格中退回 Material 组件。
4. 容器的颜色/排版插槽用 `LocalZiyuContentColor`、`LocalZiyuTextStyle` 传递原生角色。业务数据色（成功、警告、错误）可通过桥接语义传入，但由原生组件负责最终绘制。
5. 使用 `LocalZiyuThemeTokens.current.layout` 取页面和导航尺寸；保留现有路由参数、业务回调、持久化键与状态所有者。
6. 检查空态、加载态、错误态、禁用态、键盘、返回、滚动与 TalkBack 状态后再接入完整页面。
