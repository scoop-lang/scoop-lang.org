---
title: 如何组织和发布 registry
nav_title: 组织和发布 registry
description: 组织源码包与版本索引，部署静态 registry，并让 Scoop 消费者下载和构建依赖。
permalink: /registry.html
order: 20
---

# 如何组织和发布 registry

Scoop 的 registry 是一组通过 HTTP(S) 提供的静态文件：`config.json` 描述格式，每个 Cone 的 JSON 索引列出版本与依赖，`tar.zst` 归档保存源码。维护者生成这些文件并部署到静态站点，`scoop-pm` 负责版本选择、下载和缓存。

本文面向 registry 维护者和库作者，说明目录组织、源码包准备、发布顺序和消费者接入。协议以[包管理规范第 8 节](https://github.com/scoop-lang/scoop/blob/main/docs/specs/SCOOP-PACKAGE-SPEC.md#8-源码-registry)为准。

## 1. 当前可用的能力

截至 2026-10-29，registry **消费端已经实现，打包和索引维护命令尚未实现**。现在可以手工生成符合协议的文件并发布，下面的完整示例使用这条路径。

| 能力 | 当前状态 |
| --- | --- |
| `scoop pm resolve/fetch/update`、普通 `scoop build/run` 消费 registry | 已实现 |
| `Cone.lock`、共享源码缓存、locked/offline/frozen、读取 yanked 状态 | 已实现 |
| `scoop pm package`、`package --list/--check` | 下一阶段设计，当前不能调用 |
| `scoop pm registry add/yank/unyank` | 下一阶段设计，当前不能调用 |
| 远端 `scoop publish`、托管账号和上传 API | 当前没有提供 |

`scoop pm …` 转发给配套的 `scoop-pm`；可以用 `scoop pm --help` 查看安装版本支持的命令。未来的发布工具见[包管理规范第 9 节](https://github.com/scoop-lang/scoop/blob/main/docs/specs/SCOOP-PACKAGE-SPEC.md#9-源码打包与静态发布)，不应把其中的计划命令作为当前操作步骤。

## 2. 组织 registry

### 2.1 选择稳定的地址和目录

例如把 registry base 定为 `https://packages.example.org/scoop/`，站点对应目录为：

```text
site/
├── config.json
├── packages/
│   └── org.example/
│       ├── answer.json
│       └── json.json
└── archives/
    └── org.example/
        ├── answer/
        │   ├── 1.0.0.tar.zst
        │   └── 1.1.0.tar.zst
        └── json/
            └── 2.0.0.tar.zst
```

`config.json` 的完整内容为 `{"format":1}`。索引路径固定为 `packages/<group>/<name>.json`，group 和 name 中的点都不拆成目录；例如 `org.example:net.http` 对应 `packages/org.example/net.http.json`。归档路径由索引的 `archive` 字段决定，上面的 `archives/` 布局只是便于维护的约定。

group/name 使用小写 ASCII，每个点分段匹配 `[a-z][a-z0-9-]*`；版本使用完整 SemVer，例如 `1.2.3`，不能写 `v1.2.3`。分发单位是 Cone；源码中的 `package` 是 namespace，不决定 registry 路径。

base 必须是 HTTP(S) 目录 URL，不能带 query、fragment 或内嵌凭据，建议始终写出末尾 `/`。相对归档 URL 按 **registry base** 解析：`archives/org.example/answer/1.0.0.tar.zst` 在上述地址下指向 `/scoop/archives/…`，不相对 `packages/org.example/answer.json` 解析。以 `/` 开头会指向域名根路径；跨站点存放归档时写完整 HTTPS URL。

registry URL 参与来源选择和缓存定位。应在首次发布前确定长期使用的地址；重定向不会自动把两个不同的 base 当成同一来源。

### 2.2 维护仓库与对外站点

可以用一个独立 Git 仓库保存 `config.json`、包索引、发布说明和部署配置。少量归档可以一起管理；归档较多时，将它们放到对象存储，通过索引中的绝对 URL 引用，索引仍按普通文本变更维护。

库的开发仓库、registry 维护仓库和对外静态目录承担不同工作：库仓库保存源码与测试，registry 维护仓库记录版本变更，部署产物只包含客户端需要的文件及可选说明页面。workspace 的每个 Cone 各有自己的索引和归档，不把整个 workspace 当成一个包发布。

同一个包索引的写入需要串行进行，例如由同一个部署任务合并变更。每次以当前完整索引为基础追加版本，避免两个任务分别写回而丢失另一方的版本。客户端不需要全局包列表、搜索页面、数据库或动态查询接口。

### 2.3 每个版本需要哪些信息

索引顶层是一个 JSON 对象，必需字段为 `format: 1`、`group`、`name`、`versions`。`versions` 是版本记录数组，可以为空；完整版本号不能重复，数组顺序不决定版本选择。格式 1 拒绝未知字段。

| 版本字段 | 内容 |
| --- | --- |
| `version` | 与归档清单相同的完整版本号 |
| `kind` | `library` 或 `executable`；只有 library 可作为依赖候选 |
| `dependencies` | 生产依赖数组，每项包含 `key`、`version`、`source` |
| `archive` | 相对 base 的归档路径，或完整 HTTP(S) URL |
| `sha256` | **压缩后的归档字节**的 SHA-256，64 位小写十六进制 |
| `yanked` | 布尔值；新发布为 `false` |

依赖 `source` 只有三种格式：

| 来源 | 索引中的 `source` |
| --- | --- |
| Registry | `{"kind":"registry","registry":"https://packages.example.org/scoop/"}` |
| Git | `{"kind":"git","git":"仓库 URL","commit":"完整 commit ID","subdir":"包目录"}` |
| 系统库 | `{"kind":"sysroot"}`，依赖 key 必须使用 `scoop` group |

版本要求与 `Cone.toml` 相同，例如 `1.0.0` 表示兼容范围，`=1.0.0` 才表示精确版本。每个非 core 包的索引必须包含 `scoop:scoop.core` 的 `=0.1.0` 依赖；即使源码清单省略了这个隐式依赖，也要在索引中展开。普通包使用 sysroot 来源即可，不必把 core 上传到 registry。

索引只记录生产依赖，不记录测试依赖，也不复制依赖包的归档地址。客户端先根据这些 metadata 求解，再下载选中的版本。已发布清单的坐标、kind、有效生产依赖必须与索引一致。

## 3. 准备可独立消费的源码包

一个源码包的 tar 根目录应直接是：

```text
Cone.toml
src/answer.scoop
README.md
LICENSE
```

不要再包一层 `answer-1.0.0/`。归档类型为 **zstd 压缩的 tar**，包含普通文件和目录；当前 reader 不接受 symlink、hardlink 等条目。打包时应把需要的文件内容写成普通文件。

先在单独的待发布目录准备独立清单和完整输入，再打包：

1. 使用 `schema = 1`，定义一个 Cone，展开所有 `{ workspace = true }` 字段和依赖。移除 `[workspace]`、`[overrides]`、`[publish]`；不携带开发者的 `Cone.lock`、`.git`、缓存和构建输出。
2. 普通依赖逐项写明 registry URL 和版本要求。仅在包里保留 `[registry].default` 而让依赖省略来源，仍不满足已发布包的要求。
3. 开发中的 path 依赖，改为已发布的 registry 依赖，或可取得的固定 Git commit。artifact 依赖需改成明确的源码来源。生产和测试依赖都要完成转换。
4. Git 依赖在清单中用 `rev` 写完整的小写 commit ID，同时给出版本要求；索引对应字段叫 `commit`。不能把 branch/tag 原样放进发布包。没有 `subdir` 时索引写 `.`。
5. Scoop 系统库可保留无显式来源的声明，例如 `"scoop:scoop.std" = "=0.1.0"`，索引中写为 sysroot 来源。
6. 纳入所有声明的平台分支需要的源码、资源、native 源码和头文件。包外 vendor 输入要复制进包，并调整相关相对路径；宿主机绝对路径不能用于发布。系统 SDK/native 库继续作为外部依赖，不复制进源码包。

这些转换目前需要维护者完成。对有 workspace、native vendor 或多平台输入的实际库，应按独立清单逐项整理，不能直接压缩开发仓库代替发布包。

## 4. 从零跑通一个 registry

以下是 macOS/Linux shell 下的独立演示，只发布 `org.example:answer:1.0.0`。需要相互匹配的 Scoop 配套命令与预编译 sysroot、Python 3 和 `zstd` 命令。开发仓库的工具构建与 sysroot 准备见[脚本说明](https://github.com/scoop-lang/scoop/blob/main/scripts/README.md)，运行开发版时显式设置 `SCOOP_SYSROOT`。

### 4.1 写一个独立库

在新目录执行，后续命令都以 `registry-demo` 为工作目录：

```sh
mkdir registry-demo
cd registry-demo
mkdir -p package/src consumer/src

cat > package/Cone.toml <<'TOML'
schema = 1

[cone]
group = "org.example"
name = "answer"
version = "1.0.0"
kind = "library"
TOML

cat > package/src/answer.scoop <<'SCOOP'
package org.example

public fun answer(): Int = 42
SCOOP
```

源码显式声明了与 group 匹配的 package。这里没有第三方依赖，隐式 core 由消费者的 sysroot 提供。

### 4.2 生成归档和索引

下面的脚本仅生成这个示例包，不承担通用清单转换。它使用显式文件清单、固定 tar 时间和模式，计算真实摘要，先写归档，再替换索引；已有同名归档或索引时退出，避免覆盖已发布版本。

```sh
python3 - <<'PY'
import hashlib
import io
import json
import subprocess
import tarfile
from pathlib import Path

source = Path("package")
site = Path("site")
relative = "archives/org.example/answer/1.0.0.tar.zst"
archive_path = site / relative
index_path = site / "packages/org.example/answer.json"
if archive_path.exists() or index_path.exists():
    raise SystemExit("This example requires a new package and index")

buffer = io.BytesIO()
with tarfile.open(fileobj=buffer, mode="w", format=tarfile.USTAR_FORMAT) as archive:
    for name in ["Cone.toml", "src/answer.scoop"]:
        content = (source / name).read_bytes()
        entry = tarfile.TarInfo(name)
        entry.size = len(content)
        entry.mode = 0o644
        entry.mtime = 0
        archive.addfile(entry, io.BytesIO(content))

compressed = subprocess.run(
    ["zstd", "-q", "-c"], input=buffer.getvalue(), capture_output=True, check=True
).stdout
archive_path.parent.mkdir(parents=True, exist_ok=True)
with archive_path.open("xb") as output:
    output.write(compressed)

index = {
    "format": 1,
    "group": "org.example",
    "name": "answer",
    "versions": [
        {
            "version": "1.0.0",
            "kind": "library",
            "dependencies": [
                {
                    "key": "scoop:scoop.core",
                    "version": "=0.1.0",
                    "source": {"kind": "sysroot"},
                }
            ],
            "archive": relative,
            "sha256": hashlib.sha256(compressed).hexdigest(),
            "yanked": False,
        }
    ],
}
index_path.parent.mkdir(parents=True, exist_ok=True)
(site / "config.json").write_text('{"format":1}\n', encoding="utf-8")
temporary = index_path.with_suffix(".json.tmp")
temporary.write_text(json.dumps(index, indent=2) + "\n", encoding="utf-8")
temporary.replace(index_path)
print(index_path)
PY
```

### 4.3 用 HTTP 提供静态文件

另开一个终端，进入同一个 `registry-demo` 目录并保持以下进程运行：

```sh
python3 -m http.server 8765 --bind 127.0.0.1 --directory site
```

此时 base 是 `http://127.0.0.1:8765/`。客户端请求 `/config.json`、`/packages/org.example/answer.json` 和索引指定的归档。registry 不接受 `file://` base，本地目录也需要通过 HTTP 暴露。Python 的这个服务用于本地演示；正式托管可用第 6 节的方式。[Python 官方说明](https://docs.python.org/3/library/http.server.html)

### 4.4 由消费者下载并编译

回到原终端，创建独立消费者：

```sh
cat > consumer/Cone.toml <<'TOML'
schema = 1

[cone]
group = "dev.demo"
name = "app"
version = "0.1.0"
kind = "executable"

[dependencies]
"org.example:answer" = { version = "1.0.0", registry = "http://127.0.0.1:8765/" }
TOML

cat > consumer/src/main.scoop <<'SCOOP'
package dev.demo

import org.example.answer

fun main() {
    if (answer() != 42) throw IllegalStateException()
    println("registry ok")
}
SCOOP

export SCOOP_PACKAGE_CACHE_DIR="$PWD/package-cache"
scoop run consumer --release
scoop pm deps consumer --why org.example:answer
scoop run consumer --release --frozen
```

首次 `run` 自动解析、下载、生成 `consumer/Cone.lock` 并编译，程序输出 `registry ok`；不要求先手动 resolve。再次 frozen 运行使用同一锁定版本及本地输入，仍输出 `registry ok`。源码、工具和 HTTP 服务均保持原位；可从服务访问日志确认第二次运行没有下载请求。

示例使用独立包缓存，便于观察首次下载；日常不设置该环境变量时默认共享 `~/.scoop/packages/`。若本机代理把回环地址也转发出去，请在现有 `NO_PROXY`/`no_proxy` 中加入 `127.0.0.1`。

## 5. 发布新版本与撤回版本

### 5.1 发布顺序

每次发布一个新的完整版本，例如 `1.1.0`：

1. 在库仓库完成正常测试，在待发布目录生成独立清单与归档。依赖的新版本应先发布，使消费者能解出完整依赖图。
2. 从待发布归档创建一个临时静态目录和独立消费者，执行与上节相同的 resolve/build/run；有测试时另验收测试用途。保留原始源码和工具。一次宿主验证只说明该 target 可用，多平台声明仍需在相应目标验证。
3. 将最终归档上传到正式、稳定的 URL；校验上传后的字节与本地摘要一致。**计算摘要后不要重新压缩归档**。
4. 保留原索引的全部版本记录，追加新版本，确认正式 URL 已可读取，再原子替换对应包的 JSON。本地文件可先写同目录临时文件再 rename；远端使用托管服务的完整文件/对象发布方式。避免直接写入正在提供服务的 JSON 文件。
5. 如果使用 CDN，更新对应索引的缓存；再用面向正式 base 的独立消费者确认新版本可选、可下载、可构建。

归档与索引分开托管时，必须先发布归档，再发布索引。整站部署时，部署产物必须保留旧版本的索引条目及归档；单包更新不要求全 registry 事务。

当前手工维护多版本索引时，上节的单包演示脚本不能直接重复运行。应追加新的版本记录，保持已有记录不变，并采用同样的临时文件替换方式。

### 5.2 版本不可变

已经发布的版本不能替换源码、修改依赖 metadata、更换 `archive` 或重写 `sha256`。修复代码、清单、资源遗漏和打包错误都应使用新版本。即使解压内容相同，重新压缩也可能产生不同摘要，不能覆盖旧 URL。

索引记录只有 `yanked` 状态可以改变。归档位置需要迁移时，应继续让旧 URL 返回原始字节，后续新版本再使用新的归档地址。整体更换 registry base 则是消费者的来源变更，应显式处理清单与 lock。

### 5.3 撤回与恢复

当前通过编辑指定版本的 `yanked` 字段并重新部署索引来撤回或恢复：

| 操作或消费者状态 | 结果 |
| --- | --- |
| 把 `yanked` 改为 `true` | 新的版本选择排除该版本 |
| 已有有效 `Cone.lock` 锁定该版本 | 仍可继续使用，locked fetch 仍可获取 |
| 新选择时使用 `update --precise` 指向撤回版本 | 不会绕过撤回限制 |
| 把 `yanked` 改回 `false` | 后续取得该索引的解析可以再次选择 |

不要删除被撤回版本的索引记录或归档：新机器执行旧 lock 的 fetch 时，仍可能需要索引中的完整依赖 metadata。撤回不主动替换已锁定选择，也不会让已有本地缓存失效。

## 6. 部署到正式站点

只要普通 GET 能返回原始 JSON 和归档字节，托管方式就满足读取协议。不需要 HEAD、Range、POST、目录浏览或服务端版本求解。缺失文件应返回 404，不能套用单页应用的规则回退到 `index.html`。

### 6.1 已有 HTTPS 站点或对象存储

最直接的方案是把 `site/` 的内容部署到现有 HTTPS 静态目录。以 Nginx 为例，文件放在 `/srv/www/scoop/`，在已有 HTTPS `server` 中增加：

```nginx
location /scoop/ {
    root /srv/www;
    try_files $uri =404;
}
```

这样 `/scoop/config.json` 对应 `/srv/www/scoop/config.json`。`root` 后面不再重复 `/scoop`；目录映射方式见 [Nginx 静态文件说明](https://nginx.org/en/docs/beginners_guide.html#static)。

对象存储也使用相同的文件 key 和读取地址，可以通过现有 HTTPS 域名/CDN 提供。将 `config.json` 和 `packages/` 下的 JSON 作为可更新文件，采用较短缓存或部署后刷新；不可变归档可以长期缓存。HTTP 缓存策略由站点设置，不是 Scoop 协议的新字段。

当前 registry 客户端没有登录命令、Bearer token 配置或专用认证头接口。受限 registry 应选择客户端所在网络可直接读取的 HTTP(S) 端点；Git 私有依赖则使用既有系统 Git 配置。上传仍用站点原有的部署工具。

### 6.2 小规模 GitHub Pages 托管

小规模公开 registry 可以将静态目录通过 Pages 发布：

1. 在 registry 仓库的 Pages 设置中选择 GitHub Actions 发布方式。
2. 按官方自定义工作流配置 `configure-pages`、`upload-pages-artifact` 和 `deploy-pages`，将 `site/` 作为部署内容，而不是把包含 `site/` 的上层目录直接上传。部署 job 的权限与 environment 使用官方模板。[自定义工作流说明](https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages)
3. 在部署内容顶层加一个简单的 `index.html` 作为站点入口；Scoop 客户端仍只读取 registry 文件。Pages 的入口要求见[建站说明](https://docs.github.com/en/pages/getting-started-with-github-pages/creating-a-github-pages-site)。
4. 将实际发布目录 URL 用作 base，例如 `https://example.github.io/scoop-registry/`，并检查其下的 `config.json` 和包索引可直接读取。依赖包的发布清单也必须使用正式来源 URL。

Pages 有站点容量、带宽及部署限制，选型时核对[官方限制](https://docs.github.com/en/pages/getting-started-with-github-pages/github-pages-limits)。大量归档可以放到适合文件分发的存储，仅在 Pages 保留索引；首次发布时就确定归档位置，避免以后改动已发布记录。

## 7. 消费者接入与更新

单个依赖可以像示例一样写显式 `registry`。同一个项目大部分依赖使用同一 registry 时，也可在开发清单中配置：

```toml
[registry]
default = "https://packages.example.org/scoop/"

[dependencies]
"org.example:answer" = "1.0.0"
```

未显式指定来源的普通依赖依次采用当前 Cone、workspace 根、用户配置的默认 registry；没有默认值就报错，不假设存在官方站点。`scoop` group 的无显式来源依赖使用系统库。发布源码包时仍须将普通依赖的默认 URL 展开到各条声明中。

```sh
scoop pm resolve consumer
scoop pm fetch consumer
scoop pm update consumer --package org.example:answer
scoop pm deps consumer --why org.example:answer
scoop build consumer --release --locked
```

resolve 可创建或更新 lock；fetch 要求已有适用的 lock，只准备锁定来源；update 才主动尝试新的兼容版本。针对一个确定版本可以追加 `--precise 1.1.0`，但该版本仍须满足清单和完整依赖图的要求。`--package` 在 update 中选择待更新的依赖，`-p` 选择 workspace 根成员。

建议将 `Cone.lock` 提交到消费者仓库。默认构建保留有效选择，不因站点发布新版本就自动更新；`--locked` 允许下载缺少的锁定源码，`--offline` 仅使用本地信息，`--frozen` 等于二者同时启用。初次离线使用前要为实际 target 和用途完成 fetch；生产与测试分别准备，测试可用 `scoop pm resolve consumer --purpose test`。

PM 与构建共用 `SCOOP_PACKAGE_CACHE_DIR` 环境变量。命令行覆盖的名字有区别：`scoop pm … --package-cache-dir <目录>`，而 `scoop build/run … --package-cache <目录>`。包源码缓存与编译缓存是两个目录；不要修改 PM 共享源码来开发修复，应使用本地 path 或根 overrides。

## 8. 常见问题

| 现象 | 检查内容 |
| --- | --- |
| `config.json` 或索引 404 | base 是否包含部署子路径；group 中的点是否被错误拆成目录 |
| JSON 解析失败或 unknown field | 返回的是不是 HTML 首页/登录页；字段是否严格符合格式 1 |
| `missing the exact implicit core edge` | 索引是否展开了 `scoop:scoop.core` 的 `=0.1.0` 生产依赖 |
| 找不到归档根目录的 `Cone.toml` | tar 是否额外包了一层目录 |
| `SHA-256 mismatch` | 摘要是否来自最终压缩字节；上传后内容是否被重新生成或替换 |
| `archive manifest does not match registry metadata` | 坐标、kind、依赖要求、来源 URL、Git commit/subdir 是否与清单一致 |
| 已发布清单仍要求 workspace/path/default 来源 | 是否展开了继承和普通依赖 URL，是否同时处理了测试依赖 |
| `immutable registry version metadata changed` | 是否修改了已发布版本；修复应发新版本，不能要求消费者清缓存来接受覆盖 |
| 新版本发布后普通 build 仍使用旧版本 | 有效 lock 优先；显式 update，并检查版本范围与索引缓存 |
| 单机可用，新机器 locked fetch 失败 | 旧版本的索引/归档是否还在，来源 URL 和系统库是否可用 |
| 离线缺少包或索引 | 先在线 fetch/resolve 对应 target 与用途，不把 offline 当作自动获取 |
| 更换 registry 后出现同包来源冲突 | 检查根与传递依赖中的显式 URL；同名同版本不会自动合并不同来源 |

## 9. 实现与验证入口

- [包管理规范](https://github.com/scoop-lang/scoop/blob/main/docs/specs/SCOOP-PACKAGE-SPEC.md)：第 4 节来源、第 6 节 lock、第 8 节读取协议、第 9 节后续发布工具。
- [CLI 命令定义](https://github.com/scoop-lang/scoop/blob/main/compiler/pm/src/cli.rs)与[解析命令参数](https://github.com/scoop-lang/scoop/blob/main/compiler/pm/src/cli/resolve.rs)：当前实际可调用的命令。
- [索引结构](https://github.com/scoop-lang/scoop/blob/main/compiler/pm/src/sources/registry.rs)、[索引读取](https://github.com/scoop-lang/scoop/blob/main/compiler/pm/src/sources/registry/index.rs)、[已发布清单检查](https://github.com/scoop-lang/scoop/blob/main/compiler/pm/src/sources/registry/manifest.rs)、[下载与匹配](https://github.com/scoop-lang/scoop/blob/main/compiler/pm/src/sources/registry/fetch.rs)：格式和首次获取行为。
- [静态 registry 正式 fixture](https://github.com/scoop-lang/scoop/blob/main/tests/fixtures/driver/pm-registry/consume.py)：普通 HTTP 文件服务、传递依赖、共享下载、更新与 frozen 构建的完整示例。
- [M63 实施记录](https://github.com/scoop-lang/scoop/blob/main/docs/package-manager/PROGRESS.md)：已完成范围及已有验收边界。
