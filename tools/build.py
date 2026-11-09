#!/usr/bin/env python3
"""Build the static scoop-lang.org site into dist/.

Pages live in src/pages as HTML fragments. The first line is a metadata
comment, for example:

    <!-- title: 语言导览; nav: tour; layout: docs -->

``layout: docs`` adds the generated table of contents; ``layout: reference``
also adds the reference chapter list from REFERENCE and previous/next links.
``redirect: TARGET`` turns the page into a redirect to TARGET (relative to
the page). Fragments may embed verified examples from examples/ with
``{{example NAME}}`` (adds the recorded NAME.out when present) or
``{{example NAME nooutput}}``. ``{{root}}`` expands to the relative path of
the site root.
"""

from __future__ import annotations

import argparse
import html
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
PAGES = SRC / "pages"
EXAMPLES = ROOT / "examples"
ASSETS = ROOT / "assets"

META_RE = re.compile(r"^<!--(.*?)-->\s*", re.DOTALL)
EXAMPLE_RE = re.compile(r"\{\{example\s+([\w-]+)(\s+nooutput)?\s*\}\}")

NAV = [
    ("install", "docs/install.html", "快速开始"),
    ("guides", "guides/index.html", "用户指南"),
    ("tour", "docs/tour.html", "语言导览"),
    ("reference", "reference/index.html", "参考文档"),
    ("kotlin", "docs/kotlin.html", "对比 Kotlin"),
    ("internals", "docs/internals.html", "架构"),
    ("api", "api/index.html", "API 文档"),
]

# Reference chapters in reading order, grouped for the sidebar.
REFERENCE = [
    (
        "语言参考",
        [
            ("reference/index.html", "概述"),
            ("reference/lexical.html", "词法结构"),
            ("reference/types.html", "类型系统"),
            ("reference/values.html", "struct、enum 与 tuple"),
            ("reference/option.html", "Option 与空安全"),
            ("reference/expressions.html", "表达式与控制流"),
            ("reference/patterns.html", "when 与模式匹配"),
            ("reference/functions.html", "函数与闭包"),
            ("reference/classes.html", "类、接口与对象"),
            ("reference/generics.html", "泛型"),
            ("reference/operators.html", "运算符与相等"),
            ("reference/exceptions.html", "异常与资源"),
            ("reference/concurrency.html", "协程与并发"),
            ("reference/modules.html", "Cone、package 与 import"),
            ("reference/annotations.html", "注解与编译期能力"),
            ("reference/ffi.html", "原生互操作"),
        ],
    ),
    (
        "标准库",
        [
            ("reference/core.html", "核心库 scoop.core"),
            ("reference/stdlib.html", "库 Cone 一览"),
            ("reference/testing.html", "测试库 scoop.test"),
        ],
    ),
]
REFERENCE_PAGES = [page for _, pages in REFERENCE for page in pages]


def parse_meta(text: str) -> tuple[dict[str, str], str]:
    match = META_RE.match(text)
    if not match:
        raise ValueError("page is missing its metadata comment")
    meta = {}
    for item in match.group(1).split(";"):
        if item.strip():
            key, _, value = item.partition(":")
            meta[key.strip()] = value.strip()
    return meta, text[match.end() :]


def render_example(match: re.Match[str]) -> str:
    name = match.group(1)
    source = EXAMPLES / f"{name}.scoop"
    if not source.is_file():
        raise FileNotFoundError(f"unknown example: {name}")
    code = html.escape(source.read_text().rstrip())
    output = EXAMPLES / f"{name}.out"
    with_output = output.is_file() and not match.group(2)
    block = (
        f'<div class="codeblock{" has-output" if with_output else ""}">'
        f'<div class="filename">{name}.scoop</div>'
        f'<pre><code class="language-scoop">{code}</code></pre></div>'
    )
    if with_output:
        block += f'<div class="output">{html.escape(output.read_text().rstrip())}</div>'
    return block


def render_nav(active: str, root: str) -> str:
    links = []
    for key, href, label in NAV:
        cls = ' class="active"' if key == active else ""
        links.append(f'<a href="{root}{href}"{cls}>{label}</a>')
    return "\n        ".join(links)


def render_reference(rel: str, root: str, body: str) -> str:
    groups = []
    for title, pages in REFERENCE:
        items = []
        for href, label in pages:
            cls = ' class="active" aria-current="page"' if href == rel else ""
            items.append(f'<li><a href="{root}{href}"{cls}>{html.escape(label)}</a></li>')
        groups.append(f"<h4>{title}</h4>\n<ul>\n" + "\n".join(items) + "\n</ul>")
    index = [href for href, _ in REFERENCE_PAGES].index(rel)
    pager = []
    if index > 0:
        href, label = REFERENCE_PAGES[index - 1]
        pager.append(
            f'<a class="prev" href="{root}{href}"><small>上一章</small>{html.escape(label)}</a>'
        )
    if index + 1 < len(REFERENCE_PAGES):
        href, label = REFERENCE_PAGES[index + 1]
        pager.append(
            f'<a class="next" href="{root}{href}"><small>下一章</small>{html.escape(label)}</a>'
        )
    return (
        '<div class="docs reference">\n<aside>\n'
        + "\n".join(groups)
        + '\n<h4>本页内容</h4><ul class="toc"></ul>\n</aside>\n'
        f'<article>\n{body}\n<nav class="pager">{"".join(pager)}</nav>\n</article>\n</div>'
    )


def build_page(page: Path, layout: str, out_dir: Path) -> None:
    rel = page.relative_to(PAGES)
    meta, body = parse_meta(page.read_text())
    depth = len(rel.parts) - 1
    root = "../" * depth
    if "redirect" in meta:
        target = html.escape(meta["redirect"])
        body = (
            f'<meta http-equiv="refresh" content="0; url={target}">\n'
            f'<div class="docs"><article><p>本页已移至 <a href="{target}">{target}</a>。</p></article></div>'
        )
    body = EXAMPLE_RE.sub(render_example, body)
    if meta.get("layout") == "docs":
        body = (
            '<div class="docs">\n<aside><h4>本页内容</h4><ul class="toc"></ul></aside>\n'
            f"<article>\n{body}\n</article>\n</div>"
        )
    elif meta.get("layout") == "reference":
        body = render_reference(rel.as_posix(), root, body)
    title = meta["title"]
    full_title = "Scoop 编程语言" if title == "Scoop" else f"{title} · Scoop 编程语言"
    text = (
        layout.replace("{{title}}", html.escape(full_title))
        .replace("{{description}}", html.escape(meta.get("description", "")))
        .replace("{{nav}}", render_nav(meta.get("nav", ""), root))
        .replace("{{content}}", body)
        .replace("{{root}}", root)
    )
    target = out_dir / rel
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text)


def default_api_docs() -> Path | None:
    home = Path(os.environ.get("SCOOP_HOME", Path.home() / ".scoop")) / "docs"
    if not home.is_dir():
        return None
    candidates = sorted(p for p in home.iterdir() if (p / "index.html").is_file())
    return candidates[0] if candidates else None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out", type=Path, default=ROOT / "dist")
    parser.add_argument(
        "--api-docs",
        type=Path,
        help="scoop doc output to publish under api/ (default: ~/.scoop/docs/<target>)",
    )
    parser.add_argument("--no-api", action="store_true", help="skip copying the API docs")
    args = parser.parse_args()

    bundle = shutil.which("bundle")
    if bundle is None:
        print(
            "error: Bundler is required; see README.md for Jekyll setup",
            file=sys.stderr,
        )
        return 1
    result = subprocess.run([bundle, "check"], cwd=ROOT, check=False)
    if result.returncode != 0:
        print("error: run `bundle install` before building the site", file=sys.stderr)
        return result.returncode

    out_dir: Path = args.out
    if out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True)

    layout = (SRC / "layout.html").read_text()
    for page in sorted(PAGES.rglob("*.html")):
        build_page(page, layout, out_dir)
    shutil.copytree(ASSETS, out_dir / "assets")
    shutil.copy2(ROOT / "install.sh", out_dir / "install.sh")
    shutil.copy2(ROOT / "install.ps1", out_dir / "install.ps1")
    shutil.copytree(EXAMPLES, out_dir / "examples", ignore=shutil.ignore_patterns("*.out"))

    result = subprocess.run(
        [
            bundle,
            "exec",
            "jekyll",
            "build",
            "--destination",
            str((out_dir / "guides").resolve()),
        ],
        cwd=ROOT,
        check=False,
    )
    if result.returncode != 0:
        return result.returncode

    if not args.no_api:
        api = args.api_docs or default_api_docs()
        if api is None:
            print("warning: no API docs found; api/ links will be broken", file=sys.stderr)
        else:
            shutil.copytree(api, out_dir / "api")
            print(f"copied API docs from {api}")

    print(f"built site into {out_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
