---
title: UI 教程：总览与第一个应用
nav_title: UI · 总览
description: 了解 Scoop UI 各个库的分工，用控件库和主题写出第一个可交互的桌面窗口。
permalink: /ui.html
order: 40
---

# UI 教程：总览与第一个应用

这套教程介绍如何用 Scoop 自带的 UI 库编写原生桌面应用。本篇是第一篇：先说明 UI 由哪些库组成，再写出第一个可交互的窗口。读完全套教程后，你应该能用现成控件搭出表单、列表、弹层和多窗口应用，也能在需要时自己绘制控件。

阅读前请先掌握[语言基础]({{ '/language-basics.html' | relative_url }})中的变量、函数、类和 lambda。下一篇：[布局与文字]({{ '/ui-layout.html' | relative_url }})。

## 教程目录

| 篇目 | 章节 | 内容 |
| --- | --- | --- |
| [总览与第一个应用]({{ '/ui.html' | relative_url }}) | 1–2 | 库的分层、运行环境、Counter |
| [布局与文字]({{ '/ui-layout.html' | relative_url }}) | 3–4 | row／column／stack、frame、约束、Label 与排版 |
| [状态与数据流]({{ '/ui-state.html' | relative_url }}) | 5 | State、Props、Binding、Store、key、线程规则 |
| [输入与表单]({{ '/ui-forms.html' | relative_url }}) | 6–8 | 文本输入、选择类控件、字段与校验 |
| [焦点、键盘与滚动]({{ '/ui-focus-scroll.html' | relative_url }}) | 9–10 | Tab 与快捷键、ScrollArea、虚拟列表 |
| [弹层与导航]({{ '/ui-overlays.html' | relative_url }}) | 11–12 | Popover、Dialog、菜单、Toast、Tabs、侧栏 |
| [数据展示]({{ '/ui-data.html' | relative_url }}) | 13 | 卡片、表格、日历、图表、会话组件 |
| [主题与样式]({{ '/ui-themes.html' | relative_url }}) | 14–15 | 主题预设与定制、局部样式和效果 |
| [自绘元素]({{ '/ui-custom.html' | relative_url }}) | 16–18 | Element、Canvas、焦点、自定义弹层与容器 |
| [桌面集成与异步]({{ '/ui-desktop.html' | relative_url }}) | 19–21 | 应用根、多窗口、原生菜单与窗框、后台任务 |
| [测试 UI]({{ '/ui-testing.html' | relative_url }}) | 22 | 状态测试与窗口测试 |
| [综合项目]({{ '/ui-project.html' | relative_url }}) | 23 | 从零写一个带表格、确认和撤销的数据应用 |

## 1. 认识 Scoop UI

### 1.1 几个库各管什么

Scoop UI 由几个普通的库 Cone 组成，应用按需依赖：

| Cone | 作用 |
| --- | --- |
| `scoop.ui` | 声明式 UI 框架：组件、状态、挂载、布局协议、输入、焦点、弹层、滚动。它本身**不带**按钮、标签这类控件，也不规定容器怎样排列子项。 |
| `scoop.ui.style` | 公共样式与主题协议：颜色、边框、圆角、阴影等 Style，以及主题的 tokens 和部件绘制。 |
| `scoop.ui.style.macos`、`.material`、`.fluent`、`.shadcn` | 四套主题预设，分别提供 `macosTheme`、`materialTheme`、`fluentTheme`、`shadcnTheme`。 |
| `scoop.ui.component` | 基础控件库：Label、Button、Input、Checkbox、布局容器、滚动、列表、弹层、菜单、表格等。 |
| `scoop.ui.component.tray` | 系统托盘组件，单独成库，不需要托盘的应用不必引入。 |

框架与控件是分开的：`scoop.ui.component` 只使用 `scoop.ui` 的公开接口来实现控件。所以你自己写的控件和库里的控件地位相同，可以用同一套状态、焦点和主题机制，[自绘元素]({{ '/ui-custom.html' | relative_url }})一篇会讲怎么做。

所有界面都由 Scoop 自己通过 Skia 绘制（macOS 用 Metal，Windows 用 D3D12，Linux 用 EGL／GLES），窗口、菜单、文件对话框和托盘等桌面能力则使用系统的原生实现。

### 1.2 几个核心概念

- **Component（组件）**：一个 class，挂载后会一直保留同一个实例，用成员 State 保存自己的状态。它的 `render()` 返回一个 View。
- **View（视图描述）**：不可变的轻量描述，说明“这里应该有什么”。`button(...)`、`column { ... }` 等函数都只是创建 View，并不会立刻生成控件。
- **State（状态）**：render 读取了哪个 State，框架就记下这个依赖；State 被写入后，只有依赖它的组件会重新 render。
- **挂载与更新**：框架比较前后两次 render 返回的 View，类型和 key 相同的位置会保留原来的组件实例和状态，只更新它的输入。

这种模型和 React、Jetpack Compose、SwiftUI 相似，但组件是保留身份的 class，状态就放在组件的字段里。

### 1.3 运行环境

UI 库随配套工具链一起安装，不需要单独下载。按[快速开始](../docs/install.html)安装后，用 `scoop --version` 确认工具链可用。当前支持的桌面平台：

- macOS（Apple Silicon 与 x86-64）；
- Linux GNU x86-64：Wayland 与 X11 都支持，可以用环境变量 `SCOOP_WINDOW_BACKEND=wayland` 或 `x11` 选择显示协议；
- Windows x86-64（MSVC）：主驱动名为 `sco`，本教程中的 `scoop` 命令都换成 `sco`。

教程中的示例都在 macOS 上编译验证过。快捷键在 macOS 上用 ⌘，在 Linux 和 Windows 上用 Ctrl，框架统称为 Primary。

## 2. 第一个应用：Counter

### 2.1 最小程序

把下面的程序保存为 `ui-counter.scoop`，也可以[下载同一份源码](examples/ui-counter.scoop)：

```scoop
{% include_relative examples/ui-counter.scoop %}
```

运行：

```sh
scoop run ui-counter.scoop --release
```

第一次编译要链接图形相关的库，需要几十秒。之后会打开一个标题为 Counter 的窗口，整个窗口是一个按钮，每点一次，文字 `Count: 0` 中的数字加一。关闭窗口后程序退出。

逐段说明：

- 开头的 `//! dep:` 行声明单文件程序的依赖，必须写在所有代码之前。单文件程序默认只有 core 和 std，UI 相关的库要逐个声明，坐标格式是 `group:name:版本`。声明依赖后，仍要用 `import` 引入名字。
- `class Counter(scope: ComponentScope): Component(scope)` 声明一个组件。框架在挂载时传入 `ComponentScope`，组件通过它访问窗口、资源和生命周期。
- `private var count: Int by state(0)` 把成员属性委托给 State。读 `count` 会登记依赖，写 `count` 会让组件重新 render。
- `render()` 返回一个 View。这里只有一个 `button(text, onClick)`，回调里修改 `count`。
- `runUiApplication(title, create)` 创建应用和一个窗口，把 `Counter` 挂载为窗口根，关闭最后一个窗口时退出。
- `ThemeSource(macosTheme(ThemeMode.Light))` 选择控件使用的主题。`context(source) { ... }` 用语言的 Context 机制把主题来源交给其中挂载的所有控件；控件库的控件都需要这个来源，否则无法决定颜色、字号和尺寸。

### 2.2 为什么按钮铺满了窗口

窗口根组件接收的是**紧约束**：宽高都必须正好等于窗口大小。按钮直接作为根，只能填满整个窗口。要让内容按自身大小显示并居中，需要在外面套一层容器。下一节的 `frame` 会把紧约束放宽为“最大不超过窗口”，并默认在两个方向上居中。布局约束的完整说明见[第 3 章]({{ '/ui-layout.html' | relative_url }})。

### 2.3 用布局和多个控件改写

保存为 `ui-counter-layout.scoop`（[下载](examples/ui-counter-layout.scoop)）：

```scoop
{% include_relative examples/ui-counter-layout.scoop %}
```

```sh
scoop run ui-counter-layout.scoop --release
```

窗口中央显示标题 Counter、一行计数文字和三个按钮，背景为主题的页面底色。计数为 0 时，`-1` 按钮呈禁用状态；点一次 `+1` 后变为可用。这次换成了 shadcn 主题：依赖头和 import 改为 `scoop.ui.style.shadcn`，控件代码不用改。

这个版本有四处变化：

1. **builder 写法**：`column { ... }`、`row { ... }` 用接收者 lambda 收集子项。在块中直接调用 `typography`、`label`、`button`，就会依次添加子项；`spacing`、`alignment` 等属性用来配置容器本身。控件的可选配置也写在尾随块里，例如 `button("-1", onClick) { variant = ButtonVariant.Outline }`。
2. **State 作为字段**：`private val count = state(0)` 直接保存 `State<Int>`，通过 `count.value` 读写。render 开头的 `val count = this.count` 把它取到局部变量。
3. **窗口底色**：组件构造时用 `currentThemeSource()` 取得 `context(source)` 中的主题来源。render 读取 `theme.current.value` 拿到当前主题，再用其中 `tokens.palette.background.background` 作为根 `frame` 的背景。读取 `current.value` 同时登记了依赖，以后在运行时切换主题，背景会随之更新。窗口本身不会自动铺底色，忘了这一步时，深色文字可能画在黑色背景上。
4. **文字居中**：`column` 的 `alignment = CrossAlignment.Center` 让较窄的子项（例如按钮行）居中。但 Label 和 Typography 在有界宽度下会按可用宽度排版，宽度撑满整列，文字默认靠段落起始边。要让文字本身居中，需要通过 `settings { alignment = TextAlignment.Center }` 设置段落对齐。

第 2 点是必须的。builder 块中有自己的接收者（`column` 和 `row` 的块接收者是 `LinearBuilder`），Scoop **不允许**在这样的块中隐式使用外层接收者（这里是 Counter 组件的成员）。直接写 `label(f"${count.value}")` 会得到：

```text
error[SCOOPC_HIR_ERROR]: implicit use of an outer receiver is not allowed; use `this@label` or an explicit object reference
```

所以要先用 `val count = this.count`（或 `val model = this.model`）取出局部变量，再在块中使用。第一个版本没有这个问题：`button(text, onClick)` 的回调是普通 lambda，不带接收者，可以直接访问组件成员。

### 2.4 练一练

- 把主题换成 `ThemeMode.Dark`，观察表面和按钮颜色的变化。
- 给 `+1` 按钮加 `variant = ButtonVariant.Secondary`。可选的外观有 `Default`、`Outline`、`Secondary`、`Ghost`、`Destructive`、`Link`。
- 去掉 `frame`，直接返回 `content`，体会紧约束对 column 的影响。
- 不重启程序、在运行时切换主题，要用到 `ThemeSource` 的状态，见[主题与样式]({{ '/ui-themes.html' | relative_url }})。

## 常见错误与继续阅读

| 现象 | 原因与处理 |
| --- | --- |
| 编译时报找不到 `scoop.ui...` | 单文件程序漏写了 `//! dep:`，或依赖头没放在最前面 |
| 报找不到 `Paint`、`ShortcutScope` 等类型 | 单文件依赖不会传递：直接 import 了哪个 Cone（如 `scoop.graphics`、`scoop.surface`、`scoop.window`），就要为它写 `//! dep:` |
| builder 块中报 `argument must be of type View, found Unit` | 块中的 `label`、`button`、`frame` 等是“追加一个子项”的成员函数，返回 `Unit`；要把控件作为参数传给 `frame(...)`、`tooltip(...)` 等，先在块外创建 View，详见[第 3 章]({{ '/ui-layout.html' | relative_url }}) |
| 控件报缺少主题来源 | 挂载入口外层没有 `context(source) { ... }` |
| builder 块中报 `implicit use of an outer receiver` | 先把组件成员取到局部变量，再在块中使用 |
| 控件铺满整个窗口 | 根是紧约束，外面套 `frame` 或其他容器 |
| 窗口是黑底，文字看不清 | 窗口不自动铺底色；用主题 palette 的 background 给根 `frame` 设置背景 |
| column 设了居中，文字仍靠左 | Label 撑满可用宽度；用段落 `settings { alignment = TextAlignment.Center }` |
| 在 `render()` 中修改 State | 不允许。render 只能读取状态，修改应放在回调或生命周期中，见[状态与数据流]({{ '/ui-state.html' | relative_url }}) |

下一篇[布局与文字]({{ '/ui-layout.html' | relative_url }})介绍容器、约束与文字排版。各库的完整 API 可以在 [API 文档](../api/index.html)中查找；实现必须遵守的完整规则见 Scoop 仓库的 [UI 规范](https://github.com/windoze/scoop/tree/main/docs/specs)。
