---
title: UI 教程：触摸、手势与无障碍
nav_title: UI · 手势与无障碍
description: 用触屏、触控板、键盘或读屏器翻同一组卡片，为自绘控件提供可读的名称、状态和动作。
permalink: /ui-interaction.html
order: 52
---

# 触摸、手势与无障碍

## 24. 让同一个操作有多个入口

翻页可以是向左轻扫，也可以是按下“下一页”按钮。两种输入调用同一个翻页函数，读屏器通过按钮执行同一个动作。Scoop 的标准按钮、复选框、输入框、滑块和对话框都已接入系统无障碍接口。自绘控件也可以提供自己的角色、名称、状态和动作。

### 用轻扫和按钮翻页

这个例子有三张卡片。向左轻扫卡片会从“计划”翻到“实现”，向右轻扫会回到“计划”。也可以用 Tab 聚焦“下一页”，用空格或回车激活。标题标为 `SemanticLive.Polite`，翻页后读屏器可以在合适的时机读出新标题，键盘焦点留在按钮上。

保存[翻页示例](examples/ui-swipe-pages.scoop)，使用带有这组接口的工具链和 `lib-gui` 组件运行。Windows 将命令名写作 `sco`。

```sh
scoop run ui-swipe-pages.scoop --release
```

```scoop
{% include_relative examples/ui-swipe-pages.scoop %}
```

`PageSwipe` 在挂载时为卡片登记 `swipeGesture`，在 `scene` 中用实际矩形放置输入区域。默认识别水平轻扫。直接接触时，手指或笔尖须在 500 ms 内移动至少 48 个逻辑单位并抬起，才提交一次翻页。系统交付的离散轻扫直接提供方向。普通鼠标用户可以点击同一组按钮。

如果界面本来就需要轮播，可以直接用控件库的 `carousel`。它默认响应系统轻扫，也支持直接拖动、上一项／下一项按钮和键盘。几种操作共用当前选中项，横向轮播会按界面的阅读方向翻页。

### 给输入选择合适的行为

| 要完成的操作 | 使用的接口 | 交互方式 |
| --- | --- | --- |
| 激活控件 | `scope.press(area)` | 接受鼠标点击、轻点和聚焦后的键盘激活。手指移动超出容差或被滚动接管时取消这次轻点。 |
| 长按打开菜单 | `contextMenu`、`nativeContextMenu`，自绘区域可用 `scope.longPress(area)` | 长按成功后只执行长按动作。右键和键盘仍可以打开菜单。 |
| 拖动滑块、滚动内容 | `scope.drag(area, …)`、`scrollArea`、`virtualList` | 拖动可按鼠标和直接接触分别配置。滚动视口越过移动阈值后接管触点，沿允许的轴消费位移。 |
| 缩放、旋转内容 | `scope.transformGesture(area)` | 支持系统提供的原生手势，或从两个直接触点识别变换。把当前倍率乘以 `scaleDelta`，把当前角度加上 `rotationDelta`（顺时针弧度）。 |

缩放和旋转由应用写回自己的视图状态。可以给同一张图加上“放大”“旋转”“复位”按钮，这样只用键盘或读屏器也能调整它。Scoop 源码仓库的双窗口示例同时演示了图形变换、触摸文本选区、虚拟列表和拖放的等价操作。从仓库根目录运行 `scoop run --release sysroot/src/scoop.ui.component/examples/touch-input`。[双窗口交互示例](https://github.com/scoop-lang/scoop/tree/main/sysroot/src/scoop.ui.component/examples/touch-input)

### 让读屏器读到名称、状态和动作

普通文字按钮从可见标签取得名称，复选框从实际的 `Binding` 取得勾选状态。只有图标的按钮可以用 `semantics = ComponentSemantics(name = Some("保存"))` 补上可读名称。表单复用 `FieldTarget` 把输入控件与标签、说明和错误关联起来。对话框打开时，辅助技术的操作范围与模态焦点范围一致。[输入与表单]({{ '/ui-forms.html' | relative_url }})

可以在框架的设置示例中试一遍。用读屏器按名称找到 “Volume” 滑块并调节音量，再激活 “Announce status” 听取状态更新。该按钮会保留键盘焦点，重复激活会读出新的序号。[无障碍设置示例](https://github.com/scoop-lang/scoop/tree/main/sysroot/src/scoop.ui.component/examples/accessibility)

自绘任务行要让读屏器既能读出“Write the outline，未勾选”，又能实际切换它。可以直接运行[自绘任务行示例](examples/ui-custom-task.scoop)，对照这三步阅读源码。

1. 创建 `scope.semantics(SemanticRole.Checkbox)`，用 `bindFocus` 绑定任务行已有的焦点目标。把标签子项路由到该节点，并启用 `mergeLabels`，可见标题就成为复选框的名称。
2. 在 `update()` 中把当前任务状态映射为 `SemanticChecked.On` 或 `Off`。把 `SemanticActions.toggle` 接到轻点和空格键已经使用的 `toggle()`，下次更新时从任务模型读回结果。
3. 在 `scene()` 中将同一个矩形交给 `context.place` 和 `context.semantics`。系统据已呈现的画面进行命中测试，读屏器能定位到整行。[自绘元素]({{ '/ui-custom.html' | relative_url }})

### 在桌面上验证

| 平台 | 输入来源 | 系统无障碍接口与读屏器 |
| --- | --- | --- |
| macOS | AppKit 交付触控板的捏合、旋转和系统转交给应用的轻扫 | NSAccessibility（AX）、VoiceOver |
| Windows | 从 `WM_POINTER` 接收触屏与笔输入 | UI Automation（UIA）、讲述人 |
| Linux GNU | GTK 在 Wayland／X11 上接收触摸序列与笔尖事件 | AT-SPI、Orca |

先用键盘和读屏器找到“下一页”并激活，确认页码与标题都改变，再在设备上轻扫同一张卡片。普通滚轮用于滚动，系统保留的桌面手势由系统处理。项目已在三个平台用读屏器检查基础控件，Windows 触屏与笔的实机验证仍待补齐。[平台实施与验证记录](https://github.com/scoop-lang/scoop/blob/main/docs/ui/interaction-polish/PROGRESS.md)
