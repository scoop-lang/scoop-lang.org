---
title: UI 教程：输入与表单
nav_title: UI · 输入与表单
description: 用 TextEditorState、选择类控件和 field 组合，写出带校验的资料表单。
permalink: /ui-forms.html
order: 43
---

# 输入与表单

本篇是 UI 教程的第 6–8 章：先学会文本输入，再认识勾选、单选、滑块和下拉选择，最后把它们组合成一个带校验的资料表单。上一篇是[状态与数据流]({{ '/ui-state.html' | relative_url }})，下一篇是[焦点、键盘与滚动]({{ '/ui-focus-scroll.html' | relative_url }})。

本篇的示例都是单文件程序，和[第一个应用]({{ '/ui.html' | relative_url }})一样用 `//! dep:` 声明依赖、用 `scoop run <文件> --release` 运行（Windows 写 `sco`）。示例在 macOS 上验证，Linux 上同样可用。

阅读代码前先记住两个写法，后面每个示例都会用到：

- **在 builder lambda 中不能隐式使用组件成员。** `column { ... }`、`button(...) { ... }` 这类 lambda 有自己的接收者，直接写组件字段 `name` 会报 `implicit use of an outer receiver is not allowed`。示例统一在 `render` 开头取局部变量（`val name = this.name`），再在 lambda 中使用；需要修改的状态用 `state(...)` 字段，通过 `.value` 读写。
- **根视图铺上页面背景。** 根组件得到整个窗口的空间；示例用 `frame(content)` 包住内容，以主题的背景色填充，并把内容放在左上角。

## 6. 文本输入

### 6.1 编辑模型由调用方持有

文本控件不自己保存文字。你先创建一个 `TextEditorState`（位于 `scoop.ui.text`），把它交给 `input` 或 `textarea`；控件只是“借用”这个模型来显示和编辑。这样做有几个直接的好处：

- 读取当前文字只需要 `editor.text`，在 `render` 中读取它，文字变化时界面会自动刷新；
- 程序可以随时用 `editor.replaceAll("...")` 改写内容，撤销历史、选区也保存在模型里；
- 控件因为布局变化被重新创建时，用户输入的内容不会丢失。

通常把 `TextEditorState` 声明为组件的字段，一个输入框对应一个模型。

### 6.2 单行与多行输入

`input(editor) { ... }` 是单行输入框，`textarea(editor) { ... }` 是多行输入框。常用的配置项：

| 配置 | 作用 |
| --- | --- |
| `placeholder` | 内容为空时显示的提示文字 |
| `onSubmit` | 单行输入按 Enter、多行输入按 Primary+Enter（macOS 上是 Cmd+Enter）时调用 |
| `onEdited` | 每次用户编辑后调用 |
| `enabled` / `readOnly` / `invalid` | 禁用、只读、标记为无效 |
| `rows`（仅 textarea） | 可见行数，类型是 `Long`，例如 `4L` |

### 6.3 编辑策略：长度、内容与粘贴

`policy` 决定“哪些编辑可以被接受”。用 `textEditPolicy { ... }` 构造：

- `maxLength = Some(20L)`：限制字符数；
- `singleLine = true`：不允许换行；
- `accepts { text -> ... }`：检查编辑后的完整文字，返回 `false` 时整次编辑被拒绝；
- `paste { candidate -> ... }`：只处理粘贴，可以返回 `TextEditDecision.Accept`、`Reject`，或用 `Transform(...)` 改写粘贴进来的内容；
- `transform { candidate -> ... }`：对所有来源的编辑做同样的改写。

策略在编辑写入模型**之前**生效，所以模型中永远不会出现不合规的文字，也不需要你在事后“修正”输入。

### 6.4 掩码与投影：密码框

`projection` 只改变“显示成什么样”，不改变模型里的文字。`textMask()` 把每个字符显示成 `•`，适合密码框；`textProjection()` 是默认的原样显示。切换两者时，选区和撤销历史都会保留。掩码状态下默认不允许复制。

### 6.5 输入组与验证码

`inputGroup { ... }` 把一个输入框和若干附加部分（addon）拼成一个整体：`addon { this.text("https://") }` 加一段前缀文字，`addon(InputGroupAlign.InlineEnd) { this.button(...) }` 在末尾加按钮。一个输入组中只能有一个输入控件。

`inputOtp(editor, 6L)` 是分格的验证码输入：所有格子共享同一个 `TextEditorState`，默认只接受数字，粘贴时会自动去掉空格和短横线；填满时调用 `onComplete`。

### 6.6 完整示例

下面的程序把以上内容放在一个窗口里：

```scoop
{% include_relative examples/ui-forms-text.scoop %}
```

运行：

```sh
scoop run ui-forms-text.scoop --release
```

你会看到一列输入框。在姓名框中输入名字并按 Enter，下方提示变为 `Hello, <名字>!`；姓名最多 20 个字符。手机号框只接受数字，最多 11 位，粘贴 `138-0013 8000` 会得到 `13800138000`，输入字母则不会产生任何变化。点击 Show 显示密码明文，再点 Hide 恢复为圆点。输入组前面是固定的 `https://`，末尾的 Clear 清空网址。验证码填满 6 位时，下方显示 `Code ... complete`。

`stripSeparators` 展示了粘贴改写的写法：`candidate.after.text` 是粘贴后的完整文字，`TextEditReplacement` 用 **UTF-8 字节**范围描述要替换的片段（因此用 `byteLength` 累加偏移，`Utf8Range` 来自 `scoop.window`，需要声明对应依赖）。粘贴结果先经过 `paste`，再经过 `accepts` 和长度限制。

## 7. 选择类控件

### 7.1 值通过 Binding 传入

勾选框、开关、单选、滑块和下拉选择都**不**自己保存值，而是接收一个 `Binding`：控件读取它来显示，用户操作时写回它。最常见的来源是状态的 `.binding()`：

```scoop
val darkMode = state(false)
// ...
this.switchControl(darkMode.binding())
```

也可以用 `binding({ 读取 }, { 新值 -> 写入 })` 构造“派生”绑定，读写时换算成别的数据——下面的“全选”勾选框就是这样实现的。这种方式让业务代码完全掌握数据：例如在 setter 中忽略新值，就能拒绝某次修改。

### 7.2 勾选、开关与切换按钮

- `checkbox(binding)`：绑定 `Boolean` 时是普通勾选框；绑定 `CheckState` 时支持三态 `Unchecked`、`Checked`、`Indeterminate`（部分选中）。
- `switchControl(binding)`：开关，绑定 `Boolean`。
- `toggle("Bold", binding)`：可以按下/弹起的按钮，绑定 `Boolean`。

勾选框本身没有文字。要让点击文字也能切换，用 `FieldTarget` 把控件和 `fieldLabel` 关联起来：控件设置 `labelTarget = Some(target)`，旁边放 `fieldLabel("文字", target)`。第 8 章会详细介绍这个机制。

### 7.3 单选组

`radioGroup(binding) { item(...) }` 绑定一个可选值 `T?`（`None` 表示还没有选择），每个选项是一个 `Choice(key, value, label, enabled)`：`key` 是稳定的视图身份，`value` 是写回 binding 的值，最后的 `enabled` 可省略。`axis = FlexAxis.Horizontal` 让选项横向排列。键盘上，Tab 进入当前选中项，方向键在选项间移动并选中。

同一模块还提供 `toggleGroup`，用一组切换按钮做单选或多选，用法与 `radioGroup` 相同。

### 7.4 滑块与多个滑块头

`slider(values, RangeSpec(...))` 绑定的是 `Array<Double>`：数组有几个元素就有几个滑块头（thumb）。一个元素是普通滑块，两个元素就是区间选择。`RangeSpec(minimum, maximum, step, minimumGap)` 描述取值范围、步长（`Some(5.0)`，`None` 表示连续）和相邻滑块头之间的最小间距。

拖动时 binding 会连续更新；如果只关心最终值，设置 `onValueCommit`。

### 7.5 下拉选择与组合框

`select(binding) { item(Choice(...)) }` 是从固定列表中选一项的下拉框，用 `placeholder` 设置未选择时的文字，`group(key, title) { ... }` 和 `separator(key)` 可以给选项分组。

`combobox(value, choices, query)` 是可以输入搜索的组合框，多出来的 `query` 是另一个 `TextEditorState`，保存搜索框中的文字（与选中值互相独立）。它有两种选择模式，由 binding 的类型决定：

- 绑定 `T?`：单选，可设 `showClear = true` 显示清除按钮；
- 绑定 `Array<T>`：多选，选中项显示为输入框中的小标签（chip），在空输入框按 Backspace 删除最后一个；`valueText` 决定标签上的文字。

`choices` 可以是 `Array<Choice<T>>`，也可以用 `choiceItems<T> { group(...) { item(...) } }` 构造带分组和搜索关键词（`keywords`）的列表。数据量很大时，实现 `ChoiceSource<T>` 接口按需提供条目，并配合 `filter = ComboboxFilter.Provided` 由你自己决定显示哪些结果。

### 7.6 完整示例

```scoop
{% include_relative examples/ui-forms-choices.scoop %}
```

运行：

```sh
scoop run ui-forms-choices.scoop --release
```

窗口从上到下依次是：

- “All topics” 和三个子项。只勾选部分子项时，“All topics” 显示为横杠（`Indeterminate`）；点击它会一次勾选或清空全部子项。点击子项的文字同样会切换勾选。
- 开关 “Dark mode” 和切换按钮 “Bold”。
- 横向的单选组，初始选中 “Default”。
- 音量滑块和价格区间滑块；区间的两个滑块头至少相隔 10。
- 国家下拉框和语言组合框（单选），下面是多选的语言组合框，初始带一个 `Scoop` 标签。
- 最底下一行实时显示当前的选择。

注意 `Preferences` 是一个普通的类：所有状态都放在它里面，组件只持有一个实例，并在 `render` 开头用 `val model = this.model` 取出来。值较多时，这比在组件上声明一长串字段更清楚。

## 8. 表单组合

### 8.1 标签和控件的关联：FieldTarget

`FieldTarget` 是一个“关联点”，把标签和控件连接起来：

```scoop
val emailTarget = FieldTarget()
// The control registers itself as the target...
input(email) { this.labelTarget = Some(emailTarget) }
// ...and the label points to it.
fieldLabel("Email", emailTarget)
```

关联之后，点击标签会聚焦输入框，或切换勾选框、开关。`FieldTarget` 和 `FocusHandle` 一样，需要在多次 `render` 之间保持同一个对象，所以放在组件或模型的字段里，不要在 `render` 中新建。

### 8.2 field：标签、说明与错误

`field(control) { ... }` 把一个控件和它周围的文字排成标准的表单行：

- `label("文字", target)`：带关联的标签；不需要关联时用 `title("文字")`；
- `description("...")`：灰色的说明文字；
- `errors = [...]`：错误信息数组，为空时不显示；
- `required = true`：在标签旁标出“必填”；
- `orientation = FieldOrientation.Horizontal` 加 `controlPlacement = FieldControlPlacement.Start`：控件在左、文字在右，适合勾选框和开关。

多个 field 放进 `fieldGroup { ... }` 获得统一的间距；`fieldSet(content) { legend("...") }` 给一组字段加上标题；`fieldSeparator()` 画一条分隔线（也可以带文字）。

### 8.3 校验：业务决定错误，控件只负责呈现

`field` 和控件不会自己判断输入是否合法。它们只呈现你给出的结果：`errors` 中有什么就显示什么，`invalid = true` 时控件显示为错误样式。判断规则写在你自己的代码里，通常是模型上的一个计算属性：

```scoop
val nameErrors: Array<String> get() =
    if (attempted.value && name.text.charLength == 0L)
        ["Name is required."]
    else
        []
```

因为这个属性在 `render` 中读取了 `name.text` 和 `attempted.value`，用户每次编辑或点击保存，界面都会重新计算并更新错误信息。`attempted` 用来实现常见的交互：用户第一次点击保存之前不显示错误，之后错误随输入实时更新。

保存时如果有错误，用 `FocusHandle.requestFocus()` 把焦点移到第一个出错的输入框——`FocusHandle` 通过控件的 `focus = FocusOptions(Some(handle))` 关联。焦点的更多用法见[下一篇]({{ '/ui-focus-scroll.html' | relative_url }})。

### 8.4 实战：资料表单

```scoop
{% include_relative examples/ui-forms-profile.scoop %}
```

运行：

```sh
scoop run ui-forms-profile.scoop --release
```

窗口中有 “Account” 和 “Preferences” 两组字段。直接点击 Save：Display name 和 Email 下方出现错误，输入框变为错误样式，焦点移到 Display name。填好名字再保存，错误转移到 Email；输入不带 `@` 的地址会提示 `Include an @ sign.`。两项都合法后，底部显示 `Saved <名字> <<邮箱>>`。Bio 下方实时显示字数，超过 160 个字符的输入不会被接受。点击 “Monthly newsletter” 文字可以切换勾选框。Reset 清空所有内容，错误也随之隐藏。

这个例子有几处值得模仿：

- **数据、规则和动作都在 `ProfileForm` 里**，组件只负责把它们摆成界面。规则可以单独测试，界面也可以换一种布局而不改规则。
- **先在 builder 外创建控件**，再交给 `field`。在 `fieldGroup { ... }` 内部直接写 `input(...)` 会解析成 builder 自己的成员方法（它把子视图加入列表并返回 `Unit`），而 `field` 需要的是一个 `View`。另一种写法是导入别名，例如 `import scoop.ui.component.input as makeInput`。
- **整页放进 `scrollArea`**，窗口变矮时仍能滚动到底部的按钮。

## 常见错误与继续阅读

| 现象 | 原因与解决 |
| --- | --- |
| `implicit use of an outer receiver is not allowed` | 在 builder lambda 中直接使用了组件字段。在 `render` 开头取局部变量后再使用 |
| `dependency function argument must be of type View, found Unit` | 在 builder lambda 内调用了同名的成员方法（如 `input`、`checkbox`），它返回 `Unit`。在 lambda 外创建控件，或使用导入别名 |
| 输入框的内容在界面刷新后被清空 | 在 `render` 中新建了 `TextEditorState`。把它放在组件或模型的字段里 |
| 点击标签没有反应 | 控件没有设置 `labelTarget`，或标签和控件用的不是同一个 `FieldTarget` |
| 粘贴改写后文字错位 | `TextEditReplacement` 的范围是 UTF-8 字节偏移，按 `byteLength` 累加，不要用字符下标 |
| `import scoop.window.Utf8Range` 报 `import target is not available` | 单文件程序需要为直接导入的 Cone 声明依赖：`//! dep: scoop:scoop.window:0.1.0` |
| 期望控件自动检查“必填”“邮箱格式” | 控件只呈现结果；规则写在业务代码中，通过 `errors` 和 `invalid` 交给控件 |

下一篇[焦点、键盘与滚动]({{ '/ui-focus-scroll.html' | relative_url }})介绍 Tab 顺序、程序聚焦、快捷键、滚动区域和可以承载上亿条数据的虚拟列表。完整的控件清单见 `scoop.ui.component` 的 README 与 shadcn 示例（安装后位于 `~/.scoop/src/scoop.ui.component/`）。
