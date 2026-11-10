# scoop-lang.org

Scoop 编程语言的官方网站源码。纯静态站点，不依赖任何前端框架或 npm 包。

## 目录

- `src/layout.html` — 所有页面共用的外框（导航、页脚）。
- `src/pages/` — 页面正文片段。首行是元数据注释，例如
  `<!-- title: 语言导览; nav: tour; layout: docs; description: … -->`；
  `layout: docs` 会加上自动生成的侧边目录；`layout: reference` 另加参考文档的章节导航与上一章/下一章链接，
  章节顺序由 `tools/build.py` 中的 `REFERENCE` 定义。`redirect: 目标` 把页面变为跳转页，用于保留旧地址。
- `src/pages/reference/` — 参考文档：语言参考各章与标准库参考（核心库、库 Cone 一览、测试库）。
- `guides/` — 从 Scoop 仓库迁入的用户指南与文档大纲，使用带 YAML front matter 的 Jekyll Markdown。
  `guides/_layouts/guide.html` 提供页面布局与指南导航；`guides/examples/` 保存指南示例。
- `_config.yml`、`Gemfile`、`Gemfile.lock` — Jekyll 配置与固定的 Ruby 依赖；指南输出到 `dist/guides/`。
- `examples/` — 页面中嵌入的示例程序（唯一来源），`NAME.out` 是记录的运行输出。
  在页面中用 `{{example NAME}}` 嵌入代码和输出，`{{example NAME nooutput}}` 只嵌入代码；`examples/` 中找不到时再查找 `guides/examples/`（首页与库 Cone 一览的 UI 示例来自那里）。
- `assets/` — 样式、Scoop 语法高亮与页面脚本、logo。
- `tools/build.py` — 生成官网页面并调用 Jekyll，统一输出到 `dist/`。
- `install.sh` — macOS Apple Silicon／Linux x86-64 安装脚本，构建时原样复制到 `dist/install.sh`。
- `install.ps1` — Windows x64 PowerShell 安装脚本，构建时原样复制到 `dist/install.ps1`。
- `tools/publish_release_index.sh` — 发布打包生成的 manifest 与显式 latest 指针。
- `tools/tests/test_install.py` — 用本地 HTTP 服务和隔离用户目录验证 bootstrap 参数、PATH 配置与失败退出。
- `tools/tests/test_install_ps1.py` — 仅在 Windows 运行：用本地 HTTP 服务和隔离的 `USERPROFILE` 验证 `install.ps1`。
- `tools/check_examples.py` — 用 `scoop` 编译运行官网和指南示例，并与 `.out` 比对。
- `tools/check_reference.py` — 用 `scoop check` 检查参考文档中的每个 Scoop 代码块。
- `data/api-docs.tar.xz` — 发布用的 API 文档快照，CI 解包后复制到 `dist/api/`。

## 构建

需要 Python 3、Ruby 和 Bundler。本地使用 Ruby 4.0 与 Jekyll 4.4 验证；macOS 自带的旧 Ruby 不适用，可以通过 Homebrew 安装：

```sh
brew install ruby
export PATH="$(brew --prefix ruby)/bin:$PATH"
```

在本站目录安装依赖：

```sh
bundle config set --local path vendor/bundle
bundle install
```

构建完整站点并预览：

```sh
python3 tools/build.py --api-docs /path/to/toolchain/docs/<target>  # 生成官网、指南与该目标 API 文档
python3 tools/build.py --no-api   # 跳过 API 文档
python3 tools/build.py --api-docs /path/to/scoop-doc-output
python3 -m http.server -d dist 8000
```

API 文档由工具链的 post-install 调用 `scoop doc` 生成，位于 `~/.scoop/toolchains/<version>-<host>/docs/<target-triple>`。

## 工具链安装入口与发布索引

官网脚本只探测宿主、下载独立的 [scoop-install](https://github.com/scoop-lang/scoop-install)，并把参数传给 `scoop-install toolchain install`。组件选择、版本管理和文档生成由安装器负责。

```sh
curl -fsSL https://scoop-lang.org/install.sh | sh
curl -fsSL https://scoop-lang.org/install.sh | sh -s -- 0.0.0-dev.20261111 --target x86_64-unknown-linux-musl
```

```powershell
irm https://scoop-lang.org/install.ps1 | iex
& ([scriptblock]::Create((irm https://scoop-lang.org/install.ps1))) --target x86_64-w64-windows-llvm-mingw-ucrt
```

默认安装目录为 `~/.scoop`；`--home DIR` 或 `SCOOP_HOME` 可覆盖。`SCOOP_NO_MODIFY_PATH=1` 跳过持久化 PATH。`SCOOP_INSTALL_URL` 可指定 bootstrap 下载的安装器文件 URL，`SCOOP_DIST_SERVER` 指定安装器读取的发行镜像根。详细使用方式见 [快速开始页面](src/pages/docs/install.html)。

打包仓库生成完整 TOML manifest，显式关联 host、target、bin、base、GUI、native、sources 和 vendor，含各归档的大小与 SHA-256。格式见 [发行索引合同](https://github.com/scoop-lang/scoop/blob/main/docs/distribution/MANIFEST.md)。先把三平台组件上传到 R2 的 `<release-dir>/{macos,linux,windows}/`，全局 sources／vendor 以 macOS 产物为准，再发布索引：

```sh
python3 tools/publish_release_index.py /path/to/manifest.toml --release-dir 2026-11-11 --latest --dry-run
python3 tools/publish_release_index.py /path/to/manifest.toml --release-dir 2026-11-11 --latest
```

需要 Python 3.11+。`tools/publish_release_index.sh` 是同一命令的 shell 入口。脚本按 manifest 中的关系改写归档 URL，不扫描 bucket 或从文件名推断组件；不会代为上传归档。固定入口为 `versions/<version>.toml`，只有显式 `--latest` 才更新 `latest.toml`。固定索引使用条件写入：内容相同可以重试，版本已指向其他构建时拒绝覆盖，并保留 latest。重打包必须使用新版本。

`--dry-run` 只在 `tmp/release-index/` 生成结果，不读取凭据、不访问网络。实际发布沿用 `SCOOP_RELEASE_R2_KEY_ID`、`SCOOP_RELEASE_R2_SECRET`、`SCOOP_RELEASE_R2_ENDPOINT`，bucket 默认为 `scoop-releases`。正式发布顺序为组件归档、固定 manifest、latest，官网 bootstrap 切换前还须发布三个宿主的安装器可执行文件。

```sh
sh -n install.sh tools/publish_release_index.sh
python3 -m unittest discover -s tools/tests -v
```

测试使用仓库 `tmp/`、隔离用户目录、真实 curl／PowerShell 和本地 HTTP 服务，覆盖 bootstrap 参数、PATH、失败退出与发布索引；不下载真实工具链。安装器自己的组件与代理验收位于独立仓库，最终真实发行验收在 Scoop 仓库记录。Windows 测试保存并恢复测试涉及的用户 PATH。

指南入口为 `http://localhost:8000/guides/index.html`。单独修改指南时，可以在完成一次完整构建后运行 `bundle exec jekyll build`，或用 `bundle exec jekyll build --watch` 持续更新 `dist/guides/`；保留上述 HTTP 服务即可预览。Jekyll 单独构建只输出指南，官网页面、共享 assets 和 API 仍由 `tools/build.py` 准备。

## 编写指南

在 `guides/` 下新建 Markdown 文件，正文前写 YAML front matter：

```yaml
---
title: 指南标题
description: 一句话说明本文能帮助读者完成什么。
permalink: /topic.html
order: 30
---
```

`layout: guide` 由配置默认提供。`order` 控制侧边导航顺序；需要简短的导航名称时，增加 `nav_title`。所有指南页面使用平级 `/guides/*.html` 地址，`permalink` 不要再次加 `/guides`。

正文使用普通 Markdown，保留自己的一级标题。链接其他指南时使用 `{{ '/topic.html' | relative_url }}`，生成的链接会带上配置中的 `/guides` 前缀；链接编译器文档时使用 Scoop 仓库的 GitHub 地址。计划中的文章只记录在 `guides/OUTLINE.md`，完成后再添加页面与目录入口。

完整示例放在 `guides/examples/`，在代码围栏内用 `{% include_relative examples/NAME.scoop %}` 引用同一份源码，避免网页和可下载示例不一致。需要运行比对的示例增加 `.out`，所需参数在 `tools/check_examples.py` 的 `ARGS` 中配置。

## 验证示例

修改示例或升级工具链后：

```sh
export PATH="$HOME/.scoop/bin:$PATH"
python3 tools/check_examples.py            # 全部示例
python3 tools/check_examples.py json math  # 指定示例
python3 tools/check_examples.py word-stats # 指南中的文本统计程序
python3 tools/check_examples.py --update   # 用实际输出重写 .out
```

没有 `.out` 的示例（如会一直运行的 HTTP 服务）只检查能否编译。

参考文档中的代码块直接写在页面里，修改参考文档或升级工具链后运行：

```sh
python3 tools/check_reference.py              # 全部参考页
python3 tools/check_reference.py types ffi    # 指定页面
```

每个代码块作为独立的单文件程序检查：含 `fun main` 的按原样检查，否则依次尝试作为顶层声明、作为 `main` 中的语句。演示编译错误的代码块在 `<pre>` 上标注 `data-check="error"`，需要 `Cone.toml`、多文件或额外文件的片段标注 `data-check="skip"`。

更新技术说明时，以 Scoop 仓库当前 `docs/specs/`、CLI 定义和内置库源码为依据，区分已实现能力与后续设计；历史里程碑中的后端名称和旧工具包说明可能已经过时。修改共享示例后重新验证，构建时嵌入源码与实际预期输出。API 页面由 `scoop doc` 生成，应从匹配工具链的文档目录复制，不直接修改 `dist/api/`。

## 部署

本站通过 [Release website](.github/workflows/release.yml) 工作流发布到 GitHub Pages，正式地址为 <https://scoop-lang.org>。以下事件会发布网站：

- 推送到 `main`。
- 发布正式 GitHub Release，构建该 Release 的 tag；预发布版本不会上线。
- 在 Actions → Release website → Run workflow 中选择分支并手动运行。

工作流使用 Python 3.13、Ruby 4.0 和 `Gemfile.lock` 安装依赖，执行 `tools/build.py`，将完整的 `dist/` 上传并部署。构建与部署是两个 job，构建失败不会替换线上网站。发布串行执行，不中断已经开始的部署。无需 PAT、部署密钥或 `gh-pages` 分支。

### 发布用的 API 文档

CI 使用仓库内的 `data/api-docs.tar.xz`，不依赖 runner 上预装 Scoop。压缩包顶层就是 `scoop doc` 生成的站点，包含 `index.html`、`assets/` 和 `c/`，不套额外的目录。当前快照更新于 2026-11-09，由 release `2026-11-09`（Scoop `0.0.0-dev.20261109`，revision `10a20c6c78c9b754357bb02d964dd69d26be1bf9`）的 post-install 生成，安装了 lib-base 与 lib-gui 包，覆盖 `aarch64-apple-darwin` 的 44 个系统库；API 内容中的条件声明与该目标平台一致。

更新工具链、生成并检查新的 API 文档后，在网站仓库根目录执行：

```sh
# 可替换为 scoop doc --output-dir 指定的目录。
# scoop-install show 可查看已选版本的 Root。
api_docs="/path/to/toolchain/docs/aarch64-apple-darwin"
test -f "$api_docs/index.html" && COPYFILE_DISABLE=1 tar \
  --exclude='.DS_Store' --exclude='._*' --exclude='.scoop-doc.json' \
  -cJf data/api-docs.tar.xz -C "$api_docs" .
```

将快照和对应的页面修改一起提交；在提交说明中记录工具链版本或 Scoop commit，以及文档目标平台。无需提交展开后的数千个 HTML 文件。若切换目标平台或升级生成器后文档路径变化，检查官网中指向具体 API 页面的链接。

本地复现 CI 构建（先按上文安装 Ruby 依赖）：

```sh
mkdir -p tmp
api_dir="$(mktemp -d "$PWD/tmp/api.XXXXXX")"
tar -xJf data/api-docs.tar.xz -C "$api_dir"
python3 tools/build.py --api-docs "$api_dir"
rm -rf "$api_dir"
```

### 首次配置 GitHub Pages

1. 将包含工作流的代码推送到 `scoop-lang/scoop-lang.org` 的 `main` 分支。
2. 打开仓库的 [Settings → Pages](https://github.com/scoop-lang/scoop-lang.org/settings/pages)，在 **Build and deployment → Source** 中选择 **GitHub Actions**。
3. 在同页的 **Custom domain** 中填写 `scoop-lang.org` 并保存，然后再修改下文的 DNS 记录。Actions 发布使用此设置绑定域名，仓库里的 `CNAME` 文件不起绑定作用，因此这里不添加该文件。
4. 检查 **Settings → Environments → github-pages** 的部署分支规则：允许 `main`；如果使用 Release 发布，还需要允许相应的 tag，例如 tag 规则 `v*`。手动运行也必须选择允许部署的分支。
5. 打开 [Actions](https://github.com/scoop-lang/scoop-lang.org/actions/workflows/release.yml) 手动运行一次。若首次推送发生在启用 Pages 之前，配置完成后重新运行失败的工作流即可。

仓库默认的 Actions 权限即可；工作流已为部署 job 声明 `pages: write` 和 `id-token: write`。若仓库限制了允许使用的 Actions，需要允许 `actions/*` 与 `ruby/setup-ruby`。

以上流程使用 GitHub 官方的[自定义 Pages 工作流](https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages)，不会对生成后的 HTML 再执行默认 Jekyll 构建。

### 配置域名 DNS

在域名服务商处为 `scoop-lang.org` 添加以下记录；`@` 表示根域名，每个 IP 各建一条记录：

| 类型 | 主机名 | 值 |
| --- | --- | --- |
| A | `@` | `185.199.108.153` |
| A | `@` | `185.199.109.153` |
| A | `@` | `185.199.110.153` |
| A | `@` | `185.199.111.153` |
| CNAME | `www` | `scoop-lang.github.io` |

`www` 指向组织对应的 Pages 域名，不带仓库名或路径；GitHub 会将 `www.scoop-lang.org` 重定向到配置的 `scoop-lang.org`。替换服务商为 `@`、`www` 创建的冲突停车记录，保留邮件等其他用途的 DNS 记录。

需要 IPv6 时，再添加以下四条 `AAAA` 记录，并保留上面的 `A` 记录：

| 类型 | 主机名 | 值 |
| --- | --- | --- |
| AAAA | `@` | `2606:50c0:8000::153` |
| AAAA | `@` | `2606:50c0:8001::153` |
| AAAA | `@` | `2606:50c0:8002::153` |
| AAAA | `@` | `2606:50c0:8003::153` |

DNS 生效、GitHub 签发证书后，在 Settings → Pages 勾选 **Enforce HTTPS**。DNS 传播和 HTTPS 选项出现可能需要最多 24 小时。记录值与域名绑定规则见 GitHub 的[自定义域名说明](https://docs.github.com/en/pages/configuring-a-custom-domain-for-your-github-pages-site/managing-a-custom-domain-for-your-github-pages-site)。

可以用以下命令检查解析：

```sh
dig +short scoop-lang.org A
dig +short www.scoop-lang.org CNAME
```

发布后检查首页、`/guides/index.html`、`/guides/registry.html` 与 `/api/index.html`。本站按自定义域名的根路径发布；`_config.yml` 中的 `baseurl: /guides` 是指南路径，绑定域名时不需要修改它。

`dist/` 也可以部署到其他静态文件服务器；应上传完整目录，包含官网、指南、assets 与 API 文档。
