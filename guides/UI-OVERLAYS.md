---
title: UI 教程：弹层与导航
nav_title: UI · 弹层与导航
description: 用 Popover、Dialog、菜单和 Toast 组织临时界面，再用 Tabs、侧栏、可调面板和命令面板搭出工作区。
permalink: /ui-overlays.html
order: 45
---

# UI 教程：弹层与导航

本篇是 UI 教程的第 11–12 章。第 11 章介绍浮在页面之上的各类弹层：提示、气泡卡片、对话框、侧板、菜单和通知；第 12 章介绍在多个页面和面板之间切换的导航控件，最后把它们组合成一个工作区应用。

上一篇：[焦点、键盘与滚动]({{ '/ui-focus-scroll.html' | relative_url }})。下一篇：[数据展示]({{ '/ui-data.html' | relative_url }})。

本篇示例都使用 shadcn 主题，结构与[第一个应用]({{ '/ui.html' | relative_url }})中的布局版 Counter 相同：状态放在一个普通的模型类里，页面写成 `xxxPage(model, theme)` 函数，组件的 `render()` 只负责调用它；根 `frame` 用主题的页面底色铺底。示例中会看到 `import scoop.ui.component.column as makeColumn` 这样的别名导入，原因是：在 `column { }`、`row { }` 块里直接写 `button(...)` 表示“添加一个子项”，返回 `Unit`；当需要把控件作为**值**传给另一个函数（例如作为 `tooltip` 的触发器、`dialog` 的正文）时，要调用顶层函数，别名可以避开块内同名成员。

## 11. 弹层体系

### 11.1 统一模型：open 绑定是唯一的状态来源

所有弹层都遵循同一套规则：

- **是否打开由应用持有的 `Binding<Boolean>` 决定。** 你用 `state(false)` 保存打开状态，把 `open.binding()` 传给 `popover`、`dialog`、`dropdownMenu` 等函数。打开弹层就是把状态改成 `true`，关闭就是改成 `false`，弹层本身不再保存另一份“是否打开”。
- **触发器是可选的。** 配置块里写 `trigger("Open")` 会生成一个按钮，点击它会把绑定设为 `true`；也可以完全不写触发器，由你自己的按钮、菜单命令或快捷键去修改状态。
- **用户发起的关闭要先经过 `onCloseRequest`。** 按 Escape、点击弹层外部、点击关闭按钮，或调用 `OverlayHandle.requestClose()`，弹层都会先调用 `onCloseRequest(reason)`；返回 `false` 时保持打开。`reason` 是 `OverlayCloseReason`，取值为 `Explicit`、`Escape`、`OutsidePress`、`AnchorUnavailable`、`OwnerClosed`。
- **直接写状态是应用自己的决定，不会被拦截。** `open.value = false` 一定关闭弹层；需要“保存中禁止关闭”时，应在 `onCloseRequest` 中返回 `false`，并且不在自己的代码里直接写状态。

`onOpenChange` 在绑定被接受地改变时调用，`onClosed` 在关闭动画结束、弹层真正卸载后调用。绑定的 setter 也可以拒绝写入，例如用普通的 `binding(get, set)` 包一层：

```scoop
fun guardedOpen(open: State<Boolean>, locked: State<Boolean>): Binding<Boolean> =
    binding({ open.value }, { next -> if (!locked.value) open.value = next })
```

`locked` 为 `true` 时，触发器和关闭操作写入的新值都会被忽略，弹层维持现状。

### 11.2 提示、悬浮卡片与 Popover

三者都锚定在一个触发控件旁边：

| 函数 | 何时显示 | 正文能否操作 | 典型用途 |
| --- | --- | --- | --- |
| `tooltip(trigger, text)` | 指针悬停或键盘聚焦触发器 | 否，只展示文字 | 图标按钮的说明 |
| `hoverCard(trigger, content)` | 悬停一段时间后 | 可以选择文字、点击链接 | 用户名、链接的预览 |
| `popover(open, content)` | 点击触发器或改变 `open` | 可以，包含真实输入框 | 小型表单、筛选条件 |

`tooltip` 包装原有的按钮，不改变按钮的动作和焦点行为，默认带箭头；`hoverCard` 默认 600 毫秒后打开、300 毫秒后关闭。Popover 是唯一由 open 绑定控制的一个，它的 `mode` 决定与背景的关系：

- `OverlayMode.NonModal`（默认）：点击外部会关闭 Popover，同时这次点击照常作用于背景控件；Tab 可以离开弹层。
- `OverlayMode.FocusContained`：背景仍能接收指针和滚轮，但键盘焦点被限制在弹层内。
- `OverlayMode.Modal`：阻挡背景的所有输入，直到弹层关闭。

保存为 `ui-overlays-popover.scoop`（[下载](examples/ui-overlays-popover.scoop)）：

```scoop
{% include_relative examples/ui-overlays-popover.scoop %}
```

```sh
scoop run ui-overlays-popover.scoop --release
```

Windows 写作 `sco run ui-overlays-popover.scoop --release`，本篇其余命令同理。

窗口顶部是黑色的 Save 按钮和文字 `@ada`：悬停 Save 显示“Save the current name”提示，在 `@ada` 上停留片刻会弹出资料卡片。中间一排按钮切换 Popover 的模式。点击 Edit name 会在按钮下方打开标题为 Display name 的弹层，光标已经在输入框中。

几个值得注意的地方：

- `focus = OverlayFocusOptions(Some(model.nameFocus))` 指定打开后的初始焦点；输入框通过 `focus = FocusOptions(Some(model.nameFocus))` 关联同一个 `FocusHandle`。
- Done 按钮调用 `model.handle.requestClose()`，走的是“用户请求关闭”的路径。点 Lock closing 后，Escape、点击外部和 Done 都关不掉弹层，因为 `onCloseRequest` 返回了 `false`；再点 Unlock closing 即可恢复。
- 底部一行文字显示 `open = true/false`，说明弹层状态完全由 `model.open` 表示。
- `popover` 放在一个 `row` 中，是为了让触发按钮保持自身宽度，而不是被纵向 column 拉伸到整行。

Popover 的其他常用配置有 `side` / `alignment`（首选方向与对齐，空间不够时自动翻转）、`width`、`arrow = Some(PopupArrow())`，以及用 `anchor` 锚定到别处的控件而不使用自带触发器。

### 11.3 对话框、确认框、侧板与抽屉

模态弹层占据整个窗口，打开时背景变暗并阻挡输入：

- `dialog(open, content)`：普通对话框，可以有固定的 `footer`，默认显示右上角关闭按钮，Escape 和点击遮罩都会请求关闭。
- `alertDialog(open, content)`：需要用户明确选择的确认框。初始焦点默认在取消按钮上，点击遮罩**不会**关闭；`action(text, onClick)` 只执行你的回调，不会替你关闭，需要在回调里自己把状态改回 `false`（这样才能在操作进行中保持打开）。
- `sheet(open, content)`：从窗口一边滑出的侧板，`side` 取 `SheetSide.Top`、`Bottom`、`Start`、`End`，其中 Start / End 随从右到左的布局方向自动对调。
- `drawer(open, content)`：抽屉，默认从底部滑出，可以用指针拖动关闭，还支持多个吸附高度、可聚焦的拖动把手和嵌套抽屉。

四者共享同一组配置，保存在 `ModalOptions` 中；在配置块里它们直接以成员形式出现：`title`、`description`、`header`、`scrollable` 与 `scrollState`（长表单滚动）、`focus`、`handle`、`backdrop`、`onOpenChange`、`onCloseRequest`、`onClosed` 等。学会一个，其他几个的写法就都会了。

下面的例子用四个按钮分别打开这几种弹层，并在操作完成后用 Toast 通知（Toast 在 11.5 节说明）。保存为 `ui-overlays-modal.scoop`（[下载](examples/ui-overlays-modal.scoop)）：

```scoop
{% include_relative examples/ui-overlays-modal.scoop %}
```

```sh
scoop run ui-overlays-modal.scoop --release
```

窗口显示标题 `Project: Atlas` 和四个按钮。点 Rename… 打开 Rename project 对话框，输入框已获得焦点，内容是当前名称；把它改成 `Atlas Prime` 再点 Save，对话框关闭，标题随之更新，右下角出现 “Project renamed” 的成功通知。点 Delete 打开确认框，焦点在 Keep project 上；点 Activity 会从底部滑出 Recent activity 抽屉。

这个例子没有使用 `trigger(...)`：四个弹层都由页面上的普通按钮修改状态打开。`startEdit()` 在打开前用 `draft.replaceAll(name.value)` 把草稿重置为当前名称，这样取消后再次打开，看到的仍是最新名称。

### 11.4 菜单

菜单内容用 `menu { }` 构建，得到一个 `MenuContent` 值，同一份内容可以给不同的入口复用：

- `item(key, text, onSelect)`：普通命令。配置块中可设 `shortcut`（只显示快捷键标签，真正响应快捷键见[第 9 章]({{ '/ui-focus-scroll.html' | relative_url }})）、`destructive`、`enabled`、`icon`。
- `checkboxItem(key, text, binding)`：勾选项，绑定一个 `Boolean`。
- `radioItem(key, text, value, binding)`：单选项，同一个绑定的多个选项构成一组。
- `submenu(key, text, menu { ... })`：子菜单；`label(key, text)`、`separator(key)`：分组标题和分隔线。

每个条目都需要一个稳定的 `ViewKey`，菜单靠它在重新 render 时保持焦点与悬停位置。入口有三种：

- `dropdownMenu(open, content)`：点击触发器弹出，open 绑定规则与 Popover 相同；
- `contextMenu(view, content)`：包装一个已有的控件，右键或焦点在其上时按 Shift+F10 弹出，原控件的点击动作不受影响；
- `menubar(binding) { menu(key, text, content) }`：横向菜单栏，绑定的是当前展开的那一项 `ViewKey?`。

保存为 `ui-overlays-menus.scoop`（[下载](examples/ui-overlays-menus.scoop)）。菜单项的快捷键标签用到了 `scoop.window` 中的 `ShortcutChord`，所以多声明了一个依赖：

```scoop
{% include_relative examples/ui-overlays-menus.scoop %}
```

```sh
scoop run ui-overlays-menus.scoop --release
```

点 File 弹出菜单：第一组是 Open…（右侧显示 `⌘o`）和带箭头的 Share 子菜单，下面是勾选项、Appearance 单选组和红色的 Delete。右键点击“Right-click here”方框会在指针处弹出同一份菜单。选择普通命令后菜单关闭，底部文字显示所选命令；勾选项和单选项在切换后**保持菜单打开**，方便连续调整，按 Escape 或点击外部关闭。方向键移动高亮，直接键入字母可以跳到以它开头的条目。

横向菜单栏的写法：

```scoop
menubar(model.bar.binding()) {
    menu(
        ViewKey.Text("file"),
        "File",
        menu { item(ViewKey.Text("new"), "New", { model.save() }) }
    )
}
```

其中 `model.bar` 是 `state<ViewKey?>(None)`。这些都是窗口内自绘的菜单；系统菜单栏、原生右键菜单见[桌面集成]({{ '/ui-desktop.html' | relative_url }})。

### 11.5 通知 Toast

Toast 是窗口一角短暂出现的通知。它不使用 open 绑定，而是由一个 `ToastState` 管理队列：

1. 在模型中创建 `val toasts = ToastState()`；
2. 在页面中放一个 `toaster(model.toasts)`，它负责显示，`position` 选择六个位置之一（例如 `ToastPosition.BottomEnd`）；
3. 在回调里调用 `toasts.show(title) { kind = ...; description(...) }`。

`kind` 有 `Default`、`Success`、`Info`、`Warning`、`Error`、`Loading` 六种。`show` 返回 `ToastId`，可以随后原位更新或关闭同一条通知：

```scoop
val id = toasts.show("Saving…") { kind = ToastKind.Loading }
toasts.update(id, "Saved") { kind = ToastKind.Success }
```

`update` 和 `dismiss(id)` 在通知已经关闭时返回 `false`，后台任务晚到的结果因此不会让一条旧通知重新出现。默认 5 秒后自动消失，指针悬停、获得焦点或窗口失去焦点时暂停计时；`duration = None` 表示不自动关闭，`action("Undo", onClick)` 添加一个操作按钮。一个 `ToastState` 同一时刻只能交给一个 `toaster` 显示。在后台任务中更新通知的完整写法见[桌面集成与异步]({{ '/ui-desktop.html' | relative_url }})。

### 11.6 焦点：打开时去哪里，关闭后回到哪里

弹层打开时，焦点自动移入弹层：默认是其中第一个可聚焦的控件（AlertDialog 是取消按钮）。关闭后，焦点默认回到打开前所在的控件，通常就是触发器。这些行为由 `OverlayFocusOptions` 描述：

| 字段 | 默认 | 含义 |
| --- | --- | --- |
| `initialFocus` | `None` | 打开后聚焦的 `FocusHandle` |
| `autoFocus` | `true` | 没有指定 `initialFocus` 时是否自动聚焦第一个控件 |
| `restoreFocus` | `true` | 关闭后是否恢复焦点 |
| `restoreTarget` | `None` | 关闭后改为聚焦这个 `FocusHandle` |

既可以像 11.2 节那样直接构造 `OverlayFocusOptions(Some(handle))`，也可以用配置块逐项修改：

```scoop
dialog(guardedOpen(model.open, model.locked), form) {
    title("Rename")
    focus {
        initialFocus = Some(model.nameFocus)
        restoreTarget = Some(model.triggerFocus)
    }
    onCloseRequest = { reason -> reason != OverlayCloseReason.OutsidePress }
}
```

这个对话框打开时聚焦名称输入框，关闭后焦点回到 `triggerFocus` 对应的控件；点击遮罩不会关闭它，Escape 和关闭按钮仍然有效。弹层可以嵌套（对话框里再开 Sheet），每关闭一层，焦点回到上一层中原来的位置。

## 12. 导航与工作区布局

### 12.1 Tabs、面包屑与导航菜单

三种控件解决不同层级的导航：

- **`tabs(selected) { item(choice, content) }`** 在同一区域切换面板。`selected` 是 `Binding<T?>`，每个页签用 `Choice(key, value, label)` 描述：稳定 key、对应的值和标题。`variant = TabsVariant.Line` 是下划线样式；方向键在页签间移动并立即切换（`activation = TabActivation.Manual` 时改为 Space / Enter 确认）；`axis = FlexAxis.Vertical` 竖排页签。默认切走的面板会被卸载，`retention = ContentRetention.KeepMounted` 保留它的实例和编辑状态。
- **`breadcrumb { item(text, onNavigate); current(text) }`** 显示当前位置的层级路径，`ellipsis()` 折叠中间层级，`custom(view)` 放入任意控件（例如一个下拉菜单）。
- **`navigationMenu(open) { link(...); item(...) }`** 是网站式的顶部导航：`link(key, text, onNavigate)` 直接跳转，`item(key, text, panel)` 在悬停或点击时展开一个内容面板。面板中用 `navigationMenuLink(text, onNavigate)` 放链接。`open` 是可选的 `Binding<ViewKey?>`，表示当前展开的面板；导航后把它设为 `None` 即可收起。

这些控件只负责呈现和交互，“跳转到哪一页”由应用自己的状态决定。保存为 `ui-overlays-nav.scoop`（[下载](examples/ui-overlays-nav.scoop)）：

```scoop
{% include_relative examples/ui-overlays-nav.scoop %}
```

```sh
scoop run ui-overlays-nav.scoop --release
```

窗口顶部是 Home 和带下拉箭头的 Guides；下面是面包屑 `Home › Guides › Overview`，再下面是 Overview / Notes 两个页签。悬停或点击 Guides 展开三个链接，点 Language guide 后面板收起，面包屑末项和正文都变成 Language guide。切到 Notes 页签修改输入框，再切回 Overview 又切回来，修改仍在——这是 `KeepMounted` 的效果。

### 12.2 侧栏、可调面板与命令面板

桌面应用常见的工作区由三部分组成：

**侧栏 `sidebar(open, content) { inset(main) }`。** `open` 表示展开还是收起，`inset(...)` 是侧栏旁边的主区域。`content` 可以是一个 View，也可以是 `{ shown -> ... }` 形式的函数：`shown` 是 `SidebarPresentation`，其中 `collapsed` 告诉你当前是否处于收起状态，便于只显示图标。主要配置：

- `collapsible`：收起方式。`SidebarCollapse.Offcanvas`（默认）整个移出视野，`Icon` 收窄为图标栏，`None` 不可收起；
- `variant`：`Sidebar`、`Floating`、`Inset` 三种外观；`side`：`SidebarSide.Start` 或 `End`；
- `rail = true`：在侧栏边缘放一条可点击的细栏，用来切换展开状态；
- `layout` 与 `breakpoint`：默认 `SidebarLayout.Auto`，可用宽度小于 `breakpoint`（默认 768）时改用抽屉式的窄屏布局；
- 默认快捷键 Primary+B（macOS 上是 ⌘B）切换侧栏，`shortcut = None` 关闭它。

侧栏内的导航条目用 `sidebarMenu { item(key, label, onClick) { active = ...; icon(view) } }` 编写，它的 `collapsed` 属性应跟随 `shown.collapsed`。`sidebarTrigger(open)` 生成标准的切换按钮。改成移出式、放在右侧的侧栏：

```scoop
sidebar(model.nav.binding(), links) {
    collapsible = SidebarCollapse.Offcanvas
    side = SidebarSide.End
    inset(main)
}
```

**可调面板 `resizable(sizes) { panel(key, content) }`。** `sizes` 是 `Binding<Array<ResizableSize>>`，每项记录一个面板 key 及其所占比例（例如 0.7 和 0.3），拖动把手时更新它。`panel` 的配置块可设 `minimum` / `maximum`（逻辑像素）和 `collapsible`；`withHandle = true` 在分隔线上显示可见的拖动把手，把手也能用 Tab 聚焦后按方向键调整。`orientation = Orientation.Vertical` 改为上下分割。比例保存在你的状态里，因此可以持久化，也可以通过修改状态恢复默认布局。

**命令面板 `command(source, query)`。** `source` 通常用 `commandItems { group(key, title) { item(key, text, onRun) } }` 构建，`query` 是一个 `TextEditorState`，保存搜索框中的文字。默认使用模糊匹配（`CommandFilter.Ranked`），标题和 `keywords` 都参与搜索；方向键移动高亮时焦点始终留在搜索框，Enter 执行高亮的命令，`onSelect` 在执行后调用。命令面板本身只是一个普通控件，放进 `dialog` 就成了常见的“⌘K 面板”。需要自己提供搜索结果时可改用 `filter = CommandFilter.Provided`。

### 12.3 实战：一个精简的工作区

下面把上述控件组合起来：左侧是可收起为图标栏的导航，右侧顶部是侧栏开关和 Commands 按钮，下面是 Document / Preview 两个页签；Document 页签中是左右可调的编辑区和检查器，Commands 打开一个包含命令面板的对话框。保存为 `ui-overlays-workspace.scoop`（[下载](examples/ui-overlays-workspace.scoop)）：

```scoop
{% include_relative examples/ui-overlays-workspace.scoop %}
```

```sh
scoop run ui-overlays-workspace.scoop --release
```

可以这样试用：

1. 在编辑区输入几行文字，拖动编辑区与 Inspector 之间的把手调整宽度；也可以按 Tab 把焦点移到把手上，再用左右方向键调整。Inspector 设置了 `collapsible = true`，宽度拖到小于 `minimum` 时会折叠到 `collapsedSize`（默认 0），而不是停在一个过窄的宽度。
2. 点左上角的侧栏按钮或按 ⌘B，侧栏收窄为只显示 A、D、P 的图标栏；再按一次恢复。
3. 点 Commands，输入 `render`，结果中出现 Show preview（它的 keywords 包含 render），按 Enter 后对话框关闭并切换到 Preview 页签，显示刚才输入的文字。
4. 切回 Document，之前的文字和面板宽度都还在。

这个程序里所有“当前状态”——侧栏是否展开、当前页签、面板比例、对话框是否打开、草稿文字——都在 `WorkspaceModel` 中。侧栏菜单、页签和命令面板只是同一份状态的三个入口：侧栏点 Preview、页签点 Preview、命令面板执行 Show preview，修改的都是 `model.tab`，因此三处显示始终一致。命令对话框通过 `focus { initialFocus = Some(model.queryFocus) }` 在打开时直接聚焦搜索框；`openCommands()` 在打开前清空上次的搜索词。

## 常见错误与继续阅读

| 现象 | 原因与处理 |
| --- | --- |
| 把 `button(...)` 传给 `tooltip` 或 `dialog` 时报 “argument must be of type View, found Unit” | 在 builder 块里，`button` 是“添加子项”的成员函数；先在块外构造好 View，或用 `import ... as makeButton` 调用顶层函数 |
| `onCloseRequest` 返回 `false`，弹层仍被关闭 | 代码直接写了 `open.value = false`；需要受拦截的关闭请用 `OverlayHandle.requestClose()` |
| AlertDialog 点了确认按钮却不关闭 | `action` 不会替应用关闭，在回调中把状态改回 `false` |
| 触发按钮被拉伸到整行宽 | 外层 column 拉伸了子项；把弹层放进 `row` 或给外层设置合适的对齐 |
| 菜单报重复 key，或重新 render 后高亮跳动 | 每个菜单条目、侧栏条目都要有唯一且稳定的 `ViewKey` |
| Toast 不显示 | 页面中没有放 `toaster(state)`，或同一个 `ToastState` 交给了多个 toaster |
| 关闭对话框后焦点回到了意外的位置 | 用 `focus { restoreTarget = Some(handle) }` 指定关闭后的焦点 |

下一篇[数据展示]({{ '/ui-data.html' | relative_url }})介绍卡片、表格、日历、图表和会话组件。弹层与焦点的完整规则见 Scoop 仓库的 [UI 规范](https://github.com/windoze/scoop/tree/main/docs/specs)；各控件的全部配置项可以在 [API 文档](../api/index.html)中查找。以上示例在 macOS 上验证，Linux 上用法相同。
