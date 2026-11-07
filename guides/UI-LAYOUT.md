---
title: UI 教程：布局与文字
nav_title: UI · 布局与文字
description: 用 row、column、stack、frame 和 absolute 排列界面，理解约束模型，并用 Label、富文本和 Typography 排版文字。
permalink: /ui-layout.html
order: 41
---

# UI 教程：布局与文字

本篇是 UI 教程的第 3–4 章：先学会用容器把控件排成想要的样子，并弄清“为什么这段文字没有换行”这类问题背后的约束模型；然后介绍 Label、富文本、Typography 和键帽等文字控件。上一篇：[总览与第一个应用]({{ '/ui.html' | relative_url }})；下一篇：[状态与数据流]({{ '/ui-state.html' | relative_url }})。

本篇的示例都只用到 `scoop.ui.component` 中的现成容器和控件。每个示例都是完整的单文件程序，保存后用 `scoop run <文件名> --release` 运行（Windows 用 `sco`）。

## 3. 布局基础

### 3.1 一张名片：row、column 与 stack

先看一个完整的例子。把下面的程序保存为 `ui-layout-card.scoop`（[下载](examples/ui-layout-card.scoop)）：

```scoop
{% include_relative examples/ui-layout-card.scoop %}
```

```sh
scoop run ui-layout-card.scoop --release
```

窗口中央出现一张宽 320 的卡片：左上是蓝色圆形头像和居中的缩写 AL，右边是加粗的姓名和一行副标题；下面是一条分隔线、一段会自动换行的简介，以及两个按钮。

三种基础容器的分工：

| 容器 | 作用 |
| --- | --- |
| `column { ... }` | 子项从上到下排列 |
| `row { ... }` | 子项沿书写方向排列（从左到右；RTL 布局下从右到左） |
| `stack { ... }` | 子项按声明顺序叠放，后声明的在上面 |

`row` 和 `column` 的块中可以设置这些属性：

- `spacing`：相邻子项之间的间距；
- `alignment`：交叉轴对齐，类型是 `CrossAlignment`，可选 `Start`、`Center`、`End`、`Stretch`（拉伸到容器的交叉轴尺寸）和 `Baseline`（只用于 `row`，按文字基线对齐）；
- `justify`：主轴上的剩余空间如何分配，类型是 `MainAlignment`，可选 `Start`、`Center`、`End`、`SpaceBetween`、`SpaceAround`、`SpaceEvenly`；
- `padding`：容器内边距，类型是 `Insets(left, top, right, bottom)`，`Insets.all(20.0)` 表示四边相同。

`stack` 的对齐用 `alignment = Alignment(horizontal, vertical)`，两个分量都是 `AxisAlignment`（`Start`、`Center`、`End`），默认两个方向都居中。示例中的头像就是一个 48×48 的圆形 `frame` 与一个 Label 叠在一起。

如果某个子项需要单独设置弹性参数，用 `item(view) { ... }` 代替直接调用控件。下面的工具栏让标题占满剩余宽度，把按钮推到行尾，中间用一条竖向分隔线隔开：

```scoop
import scoop.ui.component.label as textView

fun toolbar(onSave: () -> Unit): View =
    row {
        item(textView("Untitled document")) { grow = 1.0 }
        separator {
            axis = FlexAxis.Vertical
            length = Some(24.0)
        }
        button("Save", onSave)
        spacing = 8.0
        alignment = CrossAlignment.Center
    }
```

`item` 的块中还可以设置 `shrink`（空间不足时的收缩权重，默认 1）、`basis`、`min`／`max`，以及只对这个子项生效的 `align`（类型是 `CrossAlignment?`，写作 `align = Some(CrossAlignment.Stretch)`）。主轴方向需要在运行时决定时，可以用 `flex { axis = FlexAxis.Vertical }`，它的其他用法与 `row`／`column` 相同。

`separator()` 画一条细线，默认横向并撑满可用宽度；`axis = FlexAxis.Vertical` 改为竖线，`length` 指定长度，`thickness` 和 `color` 可以调整粗细与颜色。

### 3.2 builder 块中的同名函数

上面的工具栏为什么要把 `label` 改名为 `textView` 导入？这涉及 builder 写法中最容易踩的坑。

`column`、`row` 等 builder 的块接收者上有一组**成员函数**：`label(...)`、`button(...)`、`frame(...)`、`scrollArea(...)` 等。在块中调用它们会把控件**追加**为子项，返回值是 `Unit`。同名的**顶层函数**（例如 `scoop.ui.component.label`）则只创建并返回一个 `View`，不追加到任何地方。在块中写出 `label(...)` 时，编译器会优先选择成员函数。

所以在块中需要“一个 View 值”时（作为 `frame`、`item`、`scrollArea` 的参数），直接写 `label(...)` 会报错：

```scoop
column {
    frame(label("boxed")) { width = Some(80.0) } // Error: label(...) here returns Unit.
}
```

```text
error[SCOOPC_HIR_ERROR]: dependency function argument must be of type View, found Unit
```

有三种常用的解决办法：

1. 在 builder 块**外面**先创建 View，存到局部变量里，再在块中用 `add(view)` 加入（[下一篇]({{ '/ui-state.html' | relative_url }})的 Stepper 就是这样写的）；
2. 把一块界面写成返回 `View` 的顶层函数，块中用 `add(helper())` 加入（示例中的 `initials` 就是这样）；
3. 用别名导入顶层函数，例如 `import scoop.ui.component.label as textView`，在块中写 `textView(...)`。

第 3 种办法在“当前接收者没有同名成员”时尤其有用。例如 `grid { ... }` 的块里没有 `label` 成员，此时写 `label(...)` 会找到外层 `column` 块的成员，从而报出上一篇提到的 `implicit use of an outer receiver is not allowed`。

另一条规则同样来自上一篇：在带接收者的 builder 块中不能隐式访问外层接收者，包括组件自己的成员。render 中先写 `val count = this.count`，再在块中使用局部变量。

### 3.3 frame：尺寸、内边距、对齐与表面

`frame(content) { ... }` 只有一个子项，负责给它加上尺寸限制、内边距、对齐方式和外观：

| 属性 | 作用 |
| --- | --- |
| `width`、`height` | 尺寸上限，类型是 `Double?`，例如 `width = Some(320.0)` |
| `padding` | 内边距，类型是 `Insets?` |
| `alignment` | 子项在 frame 内的位置，默认两个方向都居中 |
| `surface` | 使用主题的表面：`SurfaceKind.Plain`、`Action` 或 `Elevated` |
| `style { ... }` | 局部装饰：`background(...)`、`corners(...)`、`border(...)` 等 |

名片示例中有三层 frame：

- 最外层没有尺寸，它接收窗口的紧约束，因此正好铺满窗口；它用主题 palette 的页面底色作为背景，并把子项居中。窗口本身不会自动铺底色，所以每个示例的根都这样设置一次。
- 中间一层 `width = Some(320.0)`、`padding = Some(Insets.all(20.0))`、`surface = Some(SurfaceKind.Elevated)`，得到一张带边框和阴影的主题卡片。表面的颜色、圆角和阴影都来自当前主题，换主题时卡片外观随之改变。
- 头像 `initials` 里的 frame 包着 `empty()`（一个什么都不画的 View），给定 48×48，再用 `style` 设置纯色背景和半径 24 的圆角，得到一个圆。

对齐方式可以分别设置两个方向。下面的 frame 是 200×120，内容放在右上角：

```scoop
fun corner(content: View): View =
    frame(content) {
        width = Some(200.0)
        height = Some(120.0)
        alignment = Alignment(AxisAlignment.End, AxisAlignment.Start)
    }
```

`width`／`height` 是上限而不是强制尺寸：父级给出的最小宽度更大时，以父级为准。这一点在下一节会再遇到。局部样式的完整写法见[主题与样式]({{ '/ui-themes.html' | relative_url }})。

### 3.4 约束模型：为什么文字有时不换行

布局按“约束向下、尺寸向上”的顺序进行：父级给子项一个约束，包括宽高各自的最小值和最大值（最大值也可能无界）；子项在约束内决定自己的尺寸，父级再根据子项尺寸摆放它们。理解下面几条规则，就能解释大部分布局现象：

1. **窗口根是紧约束**：最小值和最大值都等于窗口尺寸，根只能铺满窗口。
2. **frame 放宽约束**：frame 给子项的最小值是 0，最大值不超过自己的可用尺寸（再减去 padding）。所以套一层 frame 后，子项可以小于窗口，并按 `alignment` 摆放。
3. **Label 在有界宽度下按可用宽度排版**：宽度有上限时，Label 在这个宽度内换行，自身宽度也等于这个上限，文字默认靠段落起始边。这就是名片中 `AL` 需要 `settings { alignment = TextAlignment.Center }` 才能居中的原因：Label 已经和头像一样宽，再设置 stack 的对齐也不会移动它。按钮和输入框在有界宽度下同样会占满宽度。
4. **宽度无界时，Label 不换行**：水平滚动区域的内容、row 第一轮测量子项时，宽度都是无界的，Label 按一整行的自然宽度排版。
5. **row 先按自然宽度测量**：row 先在无界宽度下测量各子项，得到自然宽度；总宽度超出容器时，再按 `shrink` 权重压缩，有 `grow` 的子项则分配剩余空间。因此放在 row 里的 Label 和按钮会保持自然宽度。示例中徽章 `NEW` 外面套一层 `row`，正是利用这一点让它贴合文字。
6. **Stretch 会抬高最小值**：容器的 `alignment = CrossAlignment.Stretch` 会把交叉轴最小尺寸设为容器的尺寸。此时子项 frame 的 `width` 小于这个最小值，会被撑到容器宽度。

用下面的程序观察这些规则。保存为 `ui-layout-constraints.scoop`（[下载](examples/ui-layout-constraints.scoop)）：

```scoop
{% include_relative examples/ui-layout-constraints.scoop %}
```

```sh
scoop run ui-layout-constraints.scoop --release
```

窗口从左上角开始显示四段：

1. 第一段的句子放在宽 260 的 frame 中，折成三行。
2. 第二段是同一个句子，放在水平滚动区域中，排成一行；把窗口拉窄后，可以横向滚动查看后半句。
3. 第三段的七个徽章放在宽 260 的 `wrap` 中，一行放不下时转到下一行。
4. 第四段是两列表格式的 `grid`：第一列固定宽 90，第二列占剩余宽度。

注意外层 column 用的是 `alignment = CrossAlignment.Start`。如果改成 `Stretch`，第一段的 frame 会被撑到整列宽度（规则 6），句子就只在窗口边缘才换行。需要拉伸的个别子项用 `item(view) { align = Some(CrossAlignment.Stretch) }` 单独设置，示例中的滚动区域和 grid 就是这样做的。

示例还用到了两个容器：

- `wrap { ... }`：与 `row` 用法相同，子项放不下时换到下一行；`lineSpacing` 是行间距，`axis = FlexAxis.Vertical` 可改为纵向排列、按列换行。
- `grid { ... }`：`columns` 和 `rows` 是轨道列表，`GridTrack.Fixed(宽度)`、`GridTrack.Auto`（按内容）、`GridTrack.Fraction(权重)`（按比例分剩余空间）；`columnGap`、`rowGap` 是间距；`item(view) { column = 1L; row = 0L }` 指定单元格，还可以设置 `columnSpan`、`rowSpan` 和单元格内的 `horizontal`／`vertical` 对齐。

滚动区域的细节见[焦点、键盘与滚动]({{ '/ui-focus-scroll.html' | relative_url }})。

### 3.5 absolute 与 aspectRatio

有些界面需要把元素叠放在指定位置，例如封面图上的角标。`absolute { ... }` 在一个有限大小的容器里按偏移定位子项；`aspectRatio(content, ratio)` 在父级约束内算出固定宽高比的外框。保存为 `ui-layout-absolute.scoop`（[下载](examples/ui-layout-absolute.scoop)）：

```scoop
{% include_relative examples/ui-layout-absolute.scoop %}
```

```sh
scoop run ui-layout-absolute.scoop --release
```

窗口中央是一张 420 宽、16:9 的深蓝色圆角封面：右上角是红底白字的 `NEW` 角标，左下角是白色大标题 Analytical Engine，正中央是一个半透明的小圆。

每个子项用 `item(view) { ... }` 加入，并分别设置两个轴。`AbsoluteAxis` 有四种取值：

| 取值 | 含义 |
| --- | --- |
| `Start(offset, size)` | 距起始边 `offset`；`size` 为 `Some(...)` 时固定这个轴的尺寸 |
| `End(offset, size)` | 距结束边 `offset` |
| `Center(offset, size)` | 居中后再偏移 `offset` |
| `Stretch(start, end)` | 两端分别距边缘 `start` 和 `end`，尺寸随容器 |

几点说明：

- `zIndex` 决定叠放和命中的先后，值大的画在上面；值相同时按声明顺序。示例中的角标先于标题声明，但 `zIndex = 1` 让它始终在最上层。zIndex 不改变 Tab 焦点顺序。
- absolute 的尺寸不由子项撑开。父级在某个方向无界时，必须用 `width`／`height` 给出明确尺寸。这里由 `aspectRatio` 提供了有限的外框。
- absolute 不会裁剪超出边界的子项，允许负偏移。需要外观时，可以在外面再套 frame。
- `aspectRatio` 默认裁剪到比例外框（`clip = true`），常与图片的 Cover／Contain 适配一起使用（见[数据展示]({{ '/ui-data.html' | relative_url }})）。

## 4. 文字与排版

### 4.1 一个完整的文字示例

保存为 `ui-layout-text.scoop`（[下载](examples/ui-layout-text.scoop)）：

```scoop
{% include_relative examples/ui-layout-text.scoop %}
```

```sh
scoop run ui-layout-text.scoop --release
```

窗口自上而下显示：粗大的 H1 标题、一行灰色导语、一行普通文字、一行红色加粗的大字、一段混合样式的构建提示（`2 warnings` 红色加粗，`3.4 s` 斜体）、一段带等宽行内代码的说明、一行灰色小字，然后是一行 `Search ⌘ k or Esc to close`（⌘、k 和 Esc 各显示为一个键帽），最后再显示一次构建提示，这一次可以用鼠标选中。下面逐项说明。

### 4.2 label 与 SpanStyle

`label(text)` 显示普通文字，默认使用当前主题的正文样式。尾随块中的 `style { ... }` 构造一个 `SpanStyle`，只覆盖其中明确设置的项，其余项继续沿用主题：

```scoop
label("This one overrides size, weight and color.") {
    style {
        fontSize = Some(18.0)
        weight = Some(600)
        color = Some(accent)
    }
}
```

SpanStyle 的每个属性都是可选值，常用的有 `fontSize`、`weight`（400 为常规，700 为粗体）、`color`、`slant`（`FontSlant.Italic`）、`families`（字体族列表）、`letterSpacing` 和 `lineHeight`。

`settings { ... }` 设置段落属性：`alignment`（`TextAlignment.Start`、`Center`、`End`、`Justify` 等）、`maxLines` 和 `ellipsis`。例如 `settings { maxLines = Some(2L) }` 限制最多两行，超出部分用省略号截断。

Label 只用于展示，不能选择，也不参与 Tab 焦点。要给表单控件加可点击的标签，使用 `fieldLabel`（见[输入与表单]({{ '/ui-forms.html' | relative_url }})）。

### 4.3 StyledText 富文本

同一段文字中混合多种样式时，用 `scoop.graphics.text` 的 `styledText { ... }` 构造 `StyledText`：

- `style { ... }` 设置整段的**完整**基础样式（`TextStyle`：`fontSize`、`color` 等不是可选值）；
- `text("...")` 追加一段使用当前样式的文字；
- `span { style { ... }; text("...") }` 追加一个片段，片段的 `style` 是 SpanStyle，只覆盖部分属性，片段可以嵌套。

示例中的 `notice` 就是这样构造的，然后用 `label(notice)` 显示。

要注意，StyledText 自带完整样式，**不会**继承主题的正文字体和颜色。示例显式写了字号和深色文字色；如果切换到深色主题，这段文字仍然是深色的。需要跟随主题的富文本时，优先使用下一节 `typography { ... }` 的 builder 形式：它的基础样式来自主题角色，块中的 `span` 只覆盖局部属性。

### 4.4 typography 与行内代码

`typography(text, role)` 按排版角色显示文字，样式、上下间距和装饰都由主题决定。`TypographyRole` 包括：

| 角色 | 用途 |
| --- | --- |
| `H1`、`H2`、`H3`、`H4` | 各级标题 |
| `P` | 正文段落（默认） |
| `Lead` | 导语，字号较大、颜色较浅 |
| `Large`、`Small`、`Muted` | 强调、小字、弱化说明 |
| `Blockquote` | 引用 |
| `InlineCode` | 单独显示的代码片段 |

需要在一个段落中混排文字和行内代码时，使用 builder 形式：

```scoop
typography {
    text("Run ")
    code("scoop build --release")
    text(" to compile, then ")
    span {
        style { weight = Some(700) }
        text("ship it")
    }
    text(".")
}
```

`code(...)` 生成真正的行内代码块（等宽字体，并带主题的代码底色），换行时作为一个整体移动；复制整段时，代码按普通文字复制。`typography` 的第一个参数仍可以指定角色，例如 `typography(TypographyRole.Small) { ... }`。

Typography 与 Label 的主要区别是：Typography **默认可以选择和复制**，设置 `selectable = false` 可以关闭。静态的列表和表格排版可以用 `typographyList { item("...") }` 和 `typographyTable { header { cell("...") }; row { cell("...") } }`。

### 4.5 键帽：kbd 与 kbdGroup

`kbd("Esc")` 把文字显示为一个键帽。显示快捷键时，更好的做法是使用 `scoop.window` 的 `ShortcutChord`：

```scoop
val searchChord =
    ShortcutChord(
        ShortcutKey.Logical(LogicalKey.Character("k")),
        ShortcutModifiers(primary = true)
    )
```

`kbd(searchChord)` 用一个键帽显示整个组合，`kbdGroup(searchChord)` 则把每个键分成单独的键帽。键名按平台显示：`primary = true` 在 macOS 上显示为 ⌘，在 Linux 和 Windows 上显示为 Ctrl。也可以用 `kbdGroup { kbd("↑"); kbd("↓") }` 自由组合。

键帽只负责显示，不会登记快捷键。真正响应按键要用同一个 `ShortcutChord` 注册绑定，见[焦点、键盘与滚动]({{ '/ui-focus-scroll.html' | relative_url }})。

### 4.6 可选择的文本

`selectableStyledText(content)` 显示一段 StyledText，用户可以拖动选择、双击选词，并用平台的全选和复制快捷键复制文字。它可以通过 Tab 获得焦点。示例最后一行就是它：双击 `warnings` 会选中这个词。

选择相关的配置写在尾随块中：`onSelectionChanged` 接收选区变化，`actions` 和 `decorations` 可以给指定文字范围加上可点击动作或下划线。Typography 内部也使用同一个组件，所以 `typography(...)` 的块中有同样的配置项。

## 常见错误与继续阅读

| 现象 | 原因与处理 |
| --- | --- |
| 块中写 `frame(label(...))` 报 `found Unit` | 块中的 `label` 是追加子项的成员函数；在块外创建 View、写顶层辅助函数，或用别名导入顶层 `label` |
| 块中报 `implicit use of an outer receiver` | 访问了组件成员或外层 builder 的成员；先取到局部变量，或改用别名导入的顶层函数 |
| column 设了 `Center`，文字仍靠左 | 有界宽度下 Label 撑满可用宽度；用 `settings { alignment = TextAlignment.Center }` |
| 小徽章、短文字被拉得很宽 | 同上；外面套一层 `row`，让它按自然宽度测量，或给出固定尺寸 |
| frame 设置了 `width`，实际却更宽 | 父容器用了 `Stretch`，最小宽度高于 `width`；改用 `Start`／`Center`，或只拉伸个别子项 |
| 长句子排成一行、超出窗口 | 宽度无界（例如 row 或水平滚动区域中）；用 frame 给出宽度上限 |
| absolute 报需要有界父级 | 父级在该方向无界；用 `width`／`height` 指定容器尺寸，或放进 `aspectRatio`、frame |
| StyledText 在深色主题下看不清 | StyledText 不继承主题；改用 `typography { ... }`，或从主题 tokens 取颜色 |

下一篇[状态与数据流]({{ '/ui-state.html' | relative_url }})讲解 State、Props、Binding、共享 Store 与 key。主题表面和局部样式的完整写法见[主题与样式]({{ '/ui-themes.html' | relative_url }})；需要自己实现布局策略时，见[自绘元素]({{ '/ui-custom.html' | relative_url }})。
