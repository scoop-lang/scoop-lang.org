---
title: 用户指南
nav_title: 目录
description: 按任务学习 Scoop：语言基础、项目开发与源码 registry 发布。
permalink: /index.html
order: 0
---

# 用户指南

这里整理面向 Scoop 使用者的操作指南，包含可执行的示例、使用流程和常见问题。还没有安装工具链时，先从[快速开始](../docs/install.html)准备运行环境。指南中的 `scoop` 命令在 Windows 上写作 `sco`。语言与核心库的完整规则见[参考文档](../reference/index.html)，运行时和编译产物的实现合同见[语言规范](https://github.com/windoze/scoop/tree/main/docs/specs)。

完整的拟写主题、章节范围、现有材料与优先级见[用户文档大纲与编写计划]({{ '/outline.html' | relative_url }})。以下仅列已完成的指南。

## 学习语言

- [语言基础]({{ '/language-basics.html' | relative_url }})：从变量、数值和字符串开始，掌握函数、分支、循环和程序入口，完成一个文本统计程序。
- [语言导览](../docs/tour.html)：通过现有官网的完整示例继续了解值类型、Option、泛型、对象和异步程序。

## 开发桌面 UI

- [UI 教程]({{ '/ui.html' | relative_url }})：从第一个窗口开始，依次学习布局、状态、表单、焦点与滚动、弹层与导航、数据展示、主题与样式、自绘元素、桌面集成和测试，最后完成一个综合数据应用。

## 发布与分发

- [如何组织和发布 registry]({{ '/registry.html' | relative_url }})：组织源码包与版本索引，部署静态 registry，并让消费者下载、编译和更新依赖。
