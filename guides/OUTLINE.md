---
title: 用户文档大纲与编写计划
nav_title: 文档大纲
description: Scoop 用户指南的阅读路径、编写范围、优先级与完成状态。
permalink: /outline.html
order: 90
---

# 用户文档大纲与编写计划

更新日期：2026-10-29。

用户文档按“安装并运行 → 学会语言 → 组织项目 → 开发应用 → 测试调试 → 发布”的顺序组织。首批优先补齐从安装到交付一个小程序的完整路径，再扩展语言专题、库用法和进阶内容。

以下是拟编写的文章及章节范围。**当前已完成[语言基础]({{ '/language-basics.html' | relative_url }})、[registry 指南]({{ '/registry.html' | relative_url }})和 [UI 教程]({{ '/ui.html' | relative_url }})；其他文章待编写。** 未完成文章的文件名是建议名称，不创建空文件占位。已有发行说明、库 README 和示例可以作为材料，但不等于对应用户指南已经完成。

## 1. 文档定位

| 资料 | 回答的问题 | 组织方式 |
| --- | --- | --- |
| 本目录用户指南 | 我要完成一个任务，该怎么做，为什么这样写？ | 完整步骤、可运行例子、预期结果、常见错误 |
| `scoop example` | 有没有一个可以直接查看和运行的例子？ | 聚焦单个主题的完整程序与运行说明 |
| `scoop doc` 生成的 API 文档 | 某个类型或函数在哪里，签名和行为是什么？ | 从实际声明和注释生成，提供导航与搜索 |
| 官网[参考文档](../reference/index.html) | 一条语言或核心库规则的含义是什么？ | 按主题完整描述语法、语义与核心库，代码经过工具链检查 |
| `docs/specs/` | 实现必须遵守的完整合同是什么？ | 完整规则与边界，含 ABI、产物与编译器契约 |
| design / progress / acceptance 文档 | 功能如何实现，实际完成与验证到哪里？ | 开发设计与实施记录 |

指南面向使用已安装工具链的程序员。编译器构建、开发 sysroot 准备、IR 格式和 GC 算法仍放在开发文档中；遇到源码构建用户时链接对应说明。普通教程不要求读者先掌握编译器内部阶段。

优先级表示编写顺序：

- **P0：首批必需。** 安装、语言基础、项目与依赖、构建、测试和故障定位，组成完整使用路径。
- **P1：常用专题。** 丰富语言能力、应用场景、协作与发布。
- **P2：进阶与查询。** 按实际需求补充 native 互操作、性能、线程和集中参考。

## 2. 入门与开发环境

| 优先级 | 文章与建议文件名 | 主要章节 | 读者完成后的结果 |
| --- | --- | --- | --- |
| P0 | 安装、升级与选择工具链 `INSTALLATION.md` | 宿主与目标的区别；支持的平台及系统前提；安装目录和 PATH；查看版本；sysroot 选择；升级与多版本切换 | 配套命令和目标资源可用，能确认实际使用的是哪套工具链 |
| P0 | 运行第一个程序 `QUICKSTART.md` | 单文件 Hello World；`scoop new` 创建 Cone；build/run；传递参数和退出码；从示例与离线 API 文档继续学习 | 从空目录创建、编译并运行一个带测试模板的小程序 |
| P0 | 配置编辑器 `EDITOR.md` | 安装 VSIX；工具与 sysroot 路径；打开 Cone/workspace；补全、导航、重命名和格式化；测试配置；缺锁定依赖时的处理 | 编辑器能分析已准备的项目，读者能区分语法服务与完整依赖语义 |

可复用材料：[工具包说明](https://github.com/scoop-lang/scoop/blob/main/scripts/distribution/README.md)、[VS Code 扩展说明](https://github.com/scoop-lang/scoop/blob/main/tooling/vscode-scoop/README.md)、[LSP 配置](https://github.com/scoop-lang/scoop/blob/main/compiler/lsp/README.md)、[入门示例](https://github.com/scoop-lang/scoop/tree/main/sysroot/share/scoop/examples/topics/start)。安装指南只指向实际提供的发行入口，不虚构下载地址或版本支持范围。

## 3. 语言学习

| 优先级 | 文章与建议文件名 | 主要章节 | 核心例子或易错点 |
| --- | --- | --- | --- |
| P0 · 已完成 | [语言基础]({{ '/language-basics.html' | relative_url }}) `LANGUAGE-BASICS.md` | 声明与类型推断；基本类型、数值和转换；字符串插值；表达式、分支、循环与区间；main；与 Kotlin 的关键差异 | 小型统计程序；`f"…"`、Long 索引、块体 return、程序 argv |
| P0 | 值类型、Option 与模式匹配 `VALUES.md` | struct、enum、tuple；构造、解构与副本更新；值复制与引用字段；Option；when 与穷尽性；安全访问 | 带不同载荷的查询结果；区分 `None`、嵌套 Option 与引用身份 |
| P1 | 函数、扩展与闭包 `FUNCTIONS.md` | 函数和重载；命名/默认参数与 vararg；扩展函数和属性；函数类型与引用；lambda、标签返回和捕获 | 带回调的集合处理；函数值调用与普通函数调用的差别；不能捕获局部 var |
| P1 | 对象、接口与可见性 `OBJECTS-AND-INTERFACES.md` | class 与构造初始化；属性与访问器；继承、override 和接口；object/companion；委托；公开 API | 一组可替换的实现；public 类型与成员/构造器的可见性；相等、Hash、ToString 能力 |
| P1 | 泛型与约束 `GENERICS.md` | 类型和函数泛型；推断、不变性与上界；value/ref 约束；函数条件、成员要求与条件接口实现；常见约束诊断 | 泛型容器和受约束算法；区分有同名方法与实现名义接口 |
| P1 | 错误处理与资源释放 `ERRORS-AND-RESOURCES.md` | Option 与异常的选用；throw/try/catch/finally；异常信息与重抛；Closeable/use/useAsync；成功、失败和取消时的收尾 | 文件转换在成功和失败时都关闭资源；GC 与确定性释放的区别 |

可复用材料：[语言规范](https://github.com/scoop-lang/scoop/blob/main/docs/specs/SCOOP-SPEC.md)、[语言主题示例](https://github.com/scoop-lang/scoop/tree/main/sysroot/share/scoop/examples/topics/language)、[core 示例](https://github.com/scoop-lang/scoop/blob/main/sysroot/src/scoop.core/examples/README.md)。Kotlin 差异集中在基础指南中列出，并链接对应专题，不为每个差异再建立一套重复教程。

## 4. 项目、依赖与构建

| 优先级 | 文章与建议文件名 | 主要章节 | 核心例子或易错点 |
| --- | --- | --- | --- |
| P0 | 组织 Cone 与源码 package `PROJECTS.md` | executable/library；目录与源码选择；group/name/version；package 与 import；文件和块作用域；可见性与 re-export；单文件迁入 Cone | 一个应用加一个本地库；传 `src/main.scoop` 与传 Cone 目录的区别 |
| P0 | 添加、锁定与更新依赖 `DEPENDENCIES.md` | 系统库、path、Git/GitHub、registry、artifact；版本范围；add/remove；resolve/fetch/update；Cone.lock；locked/offline/frozen；overrides 与 deps --why | 从本地库切换到 Git/registry；复现锁定选择；解释版本与来源冲突 |
| P1 | 组织多项目 workspace `WORKSPACES.md` | 根与成员；virtual workspace；default-members；字段与依赖继承；`-p`/`--workspace`；共享 lock；不同程序的独立依赖图 | 两个应用共享一个库，同时保留各自需要的依赖版本 |
| P0 | 构建、运行与选择目标 `BUILDING.md` | check/build/run 的结果；debug/release 与调试信息；产物和输出目录；目标与 native 前提；增量构建；源码缓存与编译缓存；clean 的范围 | 对同一项目完成检查、运行和 release 构建，知道输出在哪里以及何时会重建 |
| P2 | 嵌入资源与构建时配置 `COMPILE-TIME-INPUTS.md` | includeStr/includeBytes/includeDir；文件选择与相对路径；编译期 env；常量要求；嵌入输入变化；发布时携带资源 | 嵌入帮助文本、模板目录和构建版本，区分编译期配置与运行期输入 |

可复用材料：[包管理规范](https://github.com/scoop-lang/scoop/blob/main/docs/specs/SCOOP-PACKAGE-SPEC.md)、[编译与构建规范](https://github.com/scoop-lang/scoop/blob/main/docs/specs/SCOOP-IMPL-SPEC.md)、[多文件示例](https://github.com/scoop-lang/scoop/blob/main/sysroot/share/scoop/examples/topics/start/cone.md)、[跨 Cone 可见性示例](https://github.com/scoop-lang/scoop/blob/main/sysroot/share/scoop/examples/topics/language/visibility.md)、[编译期输入示例](https://github.com/scoop-lang/scoop/blob/main/sysroot/share/scoop/examples/topics/language/compiler-inputs.md)。

这里讲依赖消费；维护 registry 的目录、索引和部署继续放在已有 registry 指南中。构建指南解释用户会遇到的目标、工具链和产物兼容问题，不展开 `.slib` 二进制格式。

## 5. 常用库与应用开发

| 优先级 | 文章与建议文件名 | 主要章节 | 读者要完成的任务 |
| --- | --- | --- | --- |
| P0 | 查找和使用标准库 `LIBRARIES.md` | 按任务选择 Cone；依赖与 import；示例和离线 API 搜索；数组、列表、字典；文本、字节、日期与时长；其他库入口 | 查到并正确使用一个真实 API；完成词频统计、文本处理和日期运算 |
| P1 | 文件、系统与 I/O `FILES-AND-SYSTEM.md` | Path、目录与 metadata；文本/字节读写；流与缓冲；时钟和系统随机源；资源关闭；错误路径 | 遍历目录并生成报告，正确处理路径、编码和写入失败 |
| P1 | JSON 与类型化序列化 `SERIALIZATION.md` | JSON 值与 DTO；编解码协议；companion codec 与生成能力；字段、缺省和 Option；泛型数据；错误路径 | 从 JSON 读取配置并输出结构化结果，解释缺失字段与无效数据 |
| P1 | 异步任务与 I/O `ASYNC.md` | suspend 与事件循环；结构化 scope；launch/async；await/join；取消、超时和 finally；Context；异步资源与 TCP | 并发执行两个任务并取消其中一个；完成一个可正常收尾的 TCP 程序 |
| P2 | 线程、共享状态与同步 `THREADS.md` | 线程启动和 join；可用同步原语与原子类型；共享引用；任务与线程的区别；跨线程资源寿命 | 用真实同步完成共享计数，不把 GC、val 或 suspend 当作线程安全保证 |
| P1 | 调用 HTTP 服务 `HTTP-CLIENT.md` | client 与连接复用；GET/JSON/上传下载；响应和 body 寿命；超时、取消、重试；TLS/代理；SSE/WebSocket 入口 | 请求本地服务、处理非成功状态、下载文件并正确关闭响应 |
| P1 | 编写 HTTP 服务 `HTTP-SERVER.md` | 启动与停机；路由和 middleware；query/JSON 提取；错误响应；流式响应；静态文件/SPA；TLS、SSE 与 WebSocket 入口 | 从一个端点扩展成带 JSON API 的小服务，并完成优雅停机 |
| P1 | 编写命令行与终端程序 `CLI-AND-TERMINAL.md` | argv 与退出码；位置参数、选项、重复参数和帮助；stdout/stderr；日志；终端检测、输入与行编辑；退出恢复 | 构建可脚本化的 CLI，再按需加入交互式输入 |

可复用材料：[示例目录](https://github.com/scoop-lang/scoop/blob/main/sysroot/share/scoop/examples/catalog.toml)、[stdlib 示例](https://github.com/scoop-lang/scoop/blob/main/sysroot/src/scoop.std/examples/README.md)、[platform 示例](https://github.com/scoop-lang/scoop/blob/main/sysroot/src/scoop.platform/examples/README.md)、[JSON](https://github.com/scoop-lang/scoop/blob/main/sysroot/src/scoop.json/README.md)、[异步示例](https://github.com/scoop-lang/scoop/blob/main/sysroot/src/scoop.asyncio/examples/README.md)、[HTTP client](https://github.com/scoop-lang/scoop/blob/main/sysroot/src/scoop.http.client/README.md)、[HTTP server](https://github.com/scoop-lang/scoop/blob/main/sysroot/src/scoop.http.server/README.md)、[CLI 示例](https://github.com/scoop-lang/scoop/blob/main/sysroot/src/scoop.cli/examples/README.md)。

库指南不按每个 Cone 机械建立一篇文章。下面的现有能力先在 `LIBRARIES.md` 中给出选择依据、最小用法和材料入口；有足够的独立任务内容时再拆成专题：

| 能力 | 覆盖位置与现有材料 |
| --- | --- |
| 正则、字符集和 Unicode/IDNA | 文本处理章节；[regex](https://github.com/scoop-lang/scoop/blob/main/sysroot/src/scoop.regex/README.md)、[charset](https://github.com/scoop-lang/scoop/blob/main/sysroot/src/scoop.charset/README.md)、[IDNA](https://github.com/scoop-lang/scoop/blob/main/sysroot/src/scoop.idna/README.md) |
| URL 解析与构造 | 标准库地图及 HTTP 指南；[URL](https://github.com/scoop-lang/scoop/blob/main/sysroot/src/scoop.url/README.md) |
| 数学、大整数与十进制 | 数值章节；[math](https://github.com/scoop-lang/scoop/blob/main/sysroot/src/scoop.math/README.md) |
| 压缩与流组合 | 文件和 HTTP 指南；[compression](https://github.com/scoop-lang/scoop/blob/main/sysroot/src/scoop.compression/README.md) |
| 密码、证书与 TLS | 库选择及 TLS 专节；[crypto 示例](https://github.com/scoop-lang/scoop/blob/main/sysroot/src/scoop.crypto/examples/README.md)、[TLS 示例](https://github.com/scoop-lang/scoop/blob/main/sysroot/src/scoop.tls/examples/README.md)、[异步 TLS 示例](https://github.com/scoop-lang/scoop/blob/main/sysroot/src/scoop.tls.asyncio/examples/README.md) |
| 日志配置与控制台输出 | CLI 和故障定位指南；[log](https://github.com/scoop-lang/scoop/blob/main/sysroot/src/scoop.log/README.md)、[console provider](https://github.com/scoop-lang/scoop/blob/main/sysroot/src/scoop.log.console/README.md) |
| 终端与交互行编辑 | CLI/终端指南；[terminal](https://github.com/scoop-lang/scoop/blob/main/sysroot/src/scoop.terminal/README.md)、[异步终端示例](https://github.com/scoop-lang/scoop/blob/main/sysroot/src/scoop.terminal.asyncio/examples/README.md)、[readline](https://github.com/scoop-lang/scoop/blob/main/sysroot/src/scoop.readline/README.md) |
| HTTP 协议层与异步适配 | HTTP 指南的进阶阅读；[HTTP](https://github.com/scoop-lang/scoop/blob/main/sysroot/src/scoop.http/README.md)、[HTTP asyncio](https://github.com/scoop-lang/scoop/blob/main/sysroot/src/scoop.http.asyncio/README.md) |

## 6. 测试、调试与持续集成

| 优先级 | 文章与建议文件名 | 主要章节 | 核心例子或易错点 |
| --- | --- | --- | --- |
| P0 | 编写和运行测试 `TESTING.md` | 测试源码与依赖；测试容器和用例；断言；准备/清理；预期异常；list/filter/ignore；输出捕获与 no-run；测试用途 | 给一个库写正常、边界和异常测试，并只运行指定用例 |
| P1 | 源码调试与异常栈 `DEBUGGING.md` | 调试信息级别；VS Code/LLDB 启动和 attach；断点与变量；调试测试；优化程序；源码映射；dSYM/.debug；异常历史栈 | 在应用和测试中定位失败；理解变量不可用及当前协程物理栈的限制 |
| P0 | 常见错误与排查 `TROUBLESHOOTING.md` | 读取主诊断和关联位置；源码/类型/import；依赖/lock；工具链/sysroot；native 链接；运行期异常；编辑器问题；最小复现 | 根据错误所属环节找到下一步，不靠删除缓存或乱改版本碰运气 |
| P1 | 在 CI 中检查和构建 `CI.md` | 配套工具链准备；fmt → check → test → build；提交 lock；locked/frozen；测试与生产用途；目标矩阵；保留报告与产物 | 用普通命令复现本地流程，明确检查、测试运行和跨目标验证的区别 |

可复用材料：[测试示例](https://github.com/scoop-lang/scoop/blob/main/sysroot/share/scoop/examples/topics/test/assertions.md)、[测试库示例](https://github.com/scoop-lang/scoop/blob/main/sysroot/src/scoop.test/examples/README.md)、[调试器使用说明](https://github.com/scoop-lang/scoop/blob/main/tooling/vscode-scoop/README.md#原生调试)、[调试实施边界](https://github.com/scoop-lang/scoop/blob/main/docs/debugging/IMPLEMENTATION.md)、[当前 CLI](https://github.com/scoop-lang/scoop/blob/main/compiler/scoop/src/cli/args.rs)。测试指南以 `scoop.test` 为入口；编译器仓库的 fixture runner 不作为应用开发者的默认测试方式。

## 7. 库开发、文档与发布

| 优先级 | 文章与建议文件名 | 主要章节 | 核心例子或易错点 |
| --- | --- | --- | --- |
| P1 | 开发一个供他人使用的库 `LIBRARY-AUTHORING.md` | library Cone；公开类型与构造器；接口和泛型约束；API 命名；re-export；测试与实际消费者；版本变更；可移植源码输入 | 从本地 library 开发到被另一个项目正确消费，为源码发布做好准备 |
| P1 | 编写和生成 API 文档 `API-DOCUMENTATION.md` | 文档注释、标签和链接；README；DocHidden/DocAlias；scoop doc；多 Cone 与 no-deps；warning；离线浏览和站点部署 | 为库生成可搜索、可导航、示例完整的 API 站点 |
| 已完成 | [如何组织和发布 registry]({{ '/registry.html' | relative_url }}) `REGISTRY.md` | 静态目录与索引；独立清单；手工归档；部署顺序；不可变版本与撤回；消费者配置 | 在当前已实现消费协议上发布并下载源码包 |
| P1 | 分发原生应用与库产物 `DISTRIBUTION.md` | executable 与源码包/.slib 的用途；目标与系统依赖；GNU/musl 链接选择；伴随资源和调试文件；预编译库消费；已有产物链接 | 在声明的目标环境运行交付程序，理解产物与工具链/ABI 的配套要求 |

可复用材料：[库 API 风格](https://github.com/scoop-lang/scoop/blob/main/docs/specs/SCOOP-API-STYLE.md)、[包管理规范](https://github.com/scoop-lang/scoop/blob/main/docs/specs/SCOOP-PACKAGE-SPEC.md)、[文档命令设计](https://github.com/scoop-lang/scoop/blob/main/docs/milestone60/DESIGN.md)、[产物与链接规范](https://github.com/scoop-lang/scoop/blob/main/docs/specs/SCOOP-IMPL-SPEC.md)、[工具包使用前提](https://github.com/scoop-lang/scoop/blob/main/scripts/distribution/README.md)。

库开发指南负责 API 和消费者使用，registry 指南负责源码发布与托管，分发指南负责交付原生产物。三者共用明确的版本与来源说明，不各自重复完整的包管理教程。

## 8. 进阶与集中参考

| 优先级 | 文章与建议文件名 | 主要章节 | 核心例子或使用边界 |
| --- | --- | --- | --- |
| P2 | 调用 native 库 `NATIVE-INTEROP.md` | native 输入与链接配置；Extern/CallingConvention/CLayout；Ptr/FunPtr；数据指针借用；回调与生命周期；Unsafe/NoGC 边界 | 调用一个简单 C 库，处理字符串/数组和资源；只讲实际互操作所需契约 |
| P2 | 测量与改善性能 `PERFORMANCE.md` | release 与测量条件；启动和吞吐；分配与值复制；native 采样和符号；针对性优化输出；测量前后比较 | 找出一个真实热点并验证修改，不把编译器优化实现当作 API 保证 |
| P2 | 命令与配置速查 `COMMAND-REFERENCE.md` | 命令任务索引；常用选项；sysroot/target/profile；环境变量；路径基准；退出状态；低层工具和外部子命令入口 | 快速找到命令和 `--help`；说明 PM 与 build 中同类选项的命名差别 |
| P1 | Cone.toml 与 workspace 速查 `MANIFEST-REFERENCE.md` | 最小完整清单；cone/source/test/native 字段；依赖来源；registry；workspace 继承；overrides；路径与默认值 | 查询一个字段的写法和适用位置，链接对应操作指南 |

可复用材料：[语言规范 FFI 部分](https://github.com/scoop-lang/scoop/blob/main/docs/specs/SCOOP-SPEC.md#13-核心注解与-ffi)、[runtime 契约](https://github.com/scoop-lang/scoop/blob/main/docs/specs/SCOOP-RUNTIME-SPEC.md)、[构建与链接规范](https://github.com/scoop-lang/scoop/blob/main/docs/specs/SCOOP-IMPL-SPEC.md)、[包管理清单](https://github.com/scoop-lang/scoop/blob/main/docs/specs/SCOOP-PACKAGE-SPEC.md)、[Scoop CLI](https://github.com/scoop-lang/scoop/blob/main/compiler/scoop/src/cli/args.rs)、[PM CLI](https://github.com/scoop-lang/scoop/blob/main/compiler/pm/src/cli.rs)。

参考页提供字段和任务的导航，不手工复制全部 `--help` 或 API 签名。涉及生成器的常规用法放在序列化和构建章节；自定义生成器协议继续链接现有开发文档，暂不单独扩成用户教程系列。

## 9. 建议编写顺序

第一批完成全部 P0，共 11 篇：

1. **建立运行入口：** 安装 → 第一个程序 → 编辑器。
2. **掌握最小语言与项目：** 语言基础 → 值类型与 Option → Cone 与源码 package。
3. **完成实际开发：** 依赖管理 → 构建运行 → 标准库查找与使用。
4. **闭合验证与排错：** 测试 → 常见错误。

这批共用一个逐步扩展的小项目：从文本统计开始，拆出 library，添加依赖和测试，构建可执行程序。每篇仍提供独立可运行的起点，不要求读者执行所有前文才能操作。

第二批补齐 P1：先完成函数、对象、泛型、资源释放与 workspace，再写文件/JSON/异步/HTTP/CLI 场景，最后补上调试、CI、库开发、API 文档、产物分发与清单速查。已有 registry 指南接在依赖管理和库开发之后使用。

第三批按需求补齐 P2。线程、FFI、性能和编译期输入各自使用聚焦案例；不为完善目录而先建立新的示例框架、站点生成器或自动发布流程。

## 10. 每篇指南的编写约定

一篇文章至少交代以下内容，短文可以合并章节：

1. **要完成的任务：** 结果是什么，适合什么读者。
2. **运行前提：** 工具链、目标、依赖、工作目录和外部服务；普通安装用户无需编译 sysroot。
3. **完整示例：** 所有必需源码、Cone.toml 和资源；标清文件路径，不让读者补猜 import、依赖或生命周期。
4. **操作与结果：** 可复制的命令、预期输出或生成位置；解释选择关键参数的原因。
5. **规则与常见错误：** 只解释当前任务会遇到的语言/库行为，链接完整规范。
6. **继续阅读：** 相关指南、`scoop example` 主题和配套 API 文档。

示例优先复用已有程序和 Cone 测试。新示例按实际用途验证格式、检查、运行或测试；普通例子使用 release，调试文章按目的选择 profile，不把 GC stress 作为日常运行条件。网络例子优先提供本地服务及明确收尾方式。只记录实际验证过的目标，避免把单机成功写成全平台保证。

正文中的“已支持”以当前实现和验证为准。`package`、registry 维护命令等尚未交付的能力明确标为计划，不给出冒充可执行步骤的命令。文档示例测试、完整 Scoop 调试表达式等能力也不能因为出现在设计中就写成现有功能。

文章完成后再加入 [用户指南目录]({{ '/index.html' | relative_url }})；目录按阅读路径组织，大纲保留文章状态和尚缺内容。现有库 README 保留各库入口和专门限制，用户指南负责把跨命令、跨库的任务串起来。
