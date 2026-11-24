---
title: 语言基础
description: 学习 Scoop 的变量、数值、字符串、函数、分支、循环与 main，编写可运行的文本统计程序。
permalink: /language-basics.html
order: 10
---

# 语言基础

本文从一个 `.scoop` 文件开始，介绍编写小程序需要的语法，最后完成一个统计命令行文本的程序。你会用到变量、数值转换、字符串、函数、分支和循环；值类型、对象、泛型与异步编程可以在掌握这些基础后继续学习。

Scoop 是静态类型语言。它采用 Kotlin 风格的语法，编译为原生程序；熟悉 Kotlin 可以帮助阅读代码，但字符串插值、数组、可选值和程序参数等细节需要按 Scoop 的规则使用。

## 1. 从一个文件开始

先按[快速开始](../docs/install.html)安装配套工具链，确保 `scoop` 命令可用。把下面的程序保存为 UTF-8 编码的 `hello.scoop`：

```scoop
fun main() {
    val name = "Scoop"
    println(f"Hello, ${name}!")
}
```

在文件所在目录运行：

```sh
scoop run hello.scoop --release
```

Windows 工具包的主驱动名为 `sco`，对应命令写作 `sco run hello.scoop --release`；本文其余的 `scoop` 命令同样替换为 `sco`。

输出：

```text
Hello, Scoop!
```

`fun` 声明函数，`main` 是程序入口，`println` 输出一行文本。单文件模式默认使用 core 与 std，不需要为这个例子编写 `Cone.toml`、`package` 或 `import`；也不会自动读取旁边的 `Cone.toml`。需要多文件和额外依赖时，再创建 Cone 项目。

代码通常每行一条语句，不必加分号。用 `//` 写行注释，用 `/* … */` 写块注释。下文没有完整 `main` 的语句片段，可以分别放入上面的 `main` 中运行；以 `fun` 开头的函数示例放在文件顶层。

## 2. 变量、类型与作用域

`val` 声明不能重新赋值的绑定，`var` 声明可以重新赋值的变量。类型写在名字后面；初始化表达式已经明确类型时，通常可以省略。

```scoop
val language: String = "Scoop"
val version = 1
var count = 0
count += 1
println(f"${language} ${version}: count=${count}")
```

这里 `version` 和 `count` 都推断为 `Int`。静态类型在声明时确定，后续赋值不会改变类型：

```scoop
val title = "Guide"
var count = 0
// title = "Book"  // Error: val cannot be reassigned.
// count = "one"   // Error: String cannot be assigned to Int.
```

局部声明只在所属块及其内部可见。优先使用 `val`，确实需要在循环等位置更新状态时使用 `var`。

`val` 限制的是重新绑定，并不保证所引用的对象不可变。例如，一个 `val` 仍然可以引用可变列表：

```scoop
val names = ArrayList<String>()
names.add("Ada")
names.add("Lin")
println(names.size)
```

输出 `2`。这里没有把 `names` 重新赋给另一个列表，而是通过列表 API 修改其内容。函数参数同样不能重新赋值。

## 3. 基本类型与数值

### 常用类型

| 类型 | 用途 |
| --- | --- |
| `Boolean` | `true` 或 `false`；用于条件和逻辑运算 |
| `Int8`、`Int16`、`Int`、`Long` | 8、16、32、64 位有符号整数 |
| `UInt8`、`UInt16`、`UInt`、`ULong` | 8、16、32、64 位无符号整数 |
| `Float`、`Double` | 32、64 位浮点数 |
| `Char` | 一个 Unicode 标量值，例如 `'A'`、`'中'` |
| `String` | 文本，例如 `"Hello"` |
| `Unit` | 没有业务返回值；值写作 `()` |

`Byte` 是 `Int8` 的别名，`Short` 是 `Int16` 的别名；`Int32`/`Int64` 与 `Float32`/`Float64` 等也是透明别名。`Int` 在所有目标上都是 32 位，`Long` 都是 64 位，不随机器位数变化。

### 写出数值

```scoop
val count = 42
val size = 42L
val mask = 0xFFu
val bits = 0b1010
val budget = 1_000_000uL
val ratio = 0.5
val weight = 0.5F
println(f"${count}, ${size}, ${mask}, ${bits}, ${budget}, ${ratio}, ${weight}")
```

没有其他类型约束时，无后缀整数先选能容纳它的 `Int`，再选 `Long`；`u` 后缀先选 `UInt`，再选 `ULong`。`L` 固定为 `Long`，`uL` 固定为 `ULong`。普通小数字面量默认是 `Double`，`F` 后缀表示 `Float`。整数也可以用十六进制、二进制和数字间的下划线书写，不支持八进制写法。

### 显式转换

已经确定类型的数值不会在运算或赋值时自动提升到另一种数值类型：

```scoop
val count = 3
val total = 7L
val combined = count.toLong() + total
val average = total.toDouble() / count.toDouble()
println(f"combined=${combined}, average=${average}")
```

`count + total` 会报类型错误。需要保留小数时，应先把操作数转为浮点数；`7 / 3` 得到整数 `2`，之后再调用 `toDouble()` 也无法补回已经丢失的小数部分。

字面量可以直接接受合适的期望类型，这与已有变量之间的转换不同：

```scoop
val capacity: Long = 3
val small: Byte = 12
val fraction: Double = 1.0
// val wrong: Double = 1  // Error: an integer literal is not a floating literal.
println(f"${capacity}, ${small}, ${fraction}")
```

### 算术与比较

常用算术运算符是 `+`、`-`、`*`、`/`、`%`。整数除法向零截断，余数与被除数同号；整数除零会抛出 `ArithmeticException`。整数的加减乘和窄化转换会回绕，不会自动检查是否丢失数值：

```scoop
println(Int.MAX_VALUE + 1)
println(257.toByte())
println(-7 / 3)
println(-7 % 3)
```

依次输出 `-2147483648`、`1`、`-2`、`-1`。需要拒绝溢出或超出目标类型范围的输入时，应先检查边界，再运算或转换。

`==`、`!=` 比较值，`<`、`<=`、`>`、`>=` 比较大小。`===` 比较引用身份，不能用于 `Int`、`struct` 等值类型。布尔运算使用 `!`、`&&`、`||`；后两者短路求值。条件必须是 `Boolean`，数字和字符串不会自动变成真假值。

浮点数遵守自己的规则：除零可产生无穷大或 NaN，不抛整数除零异常。Scoop 的默认浮点比较把所有 NaN 视为相等，并排在正无穷之后；正负零相等。检测 NaN 应调用 `isNaN()`，不要沿用 `x != x` 的写法。完整边界见[参考文档中的浮点数](../reference/types.html#floats)。

## 4. 字符、字符串与插值

字符用单引号，字符串用双引号。**只有带 `f` 前缀的字符串才进行插值，而且必须写 `${…}`。**

```scoop
val name = "Ada"
val initial = 'A'
println(f"Hello, ${name}!")
println("Hello, ${name}!")
println(f"initial=${initial}, next=${1 + 2}")
```

输出：

```text
Hello, Ada!
Hello, ${name}!
initial=A, next=3
```

普通字符串中的 `$` 是普通字符。`f"Hello, $name"` 则是错误写法，插值的花括号不能省略。

普通字符串支持 `\n`、`\t`、`\"` 和 `\\` 等转义。三引号字符串保留其中的换行和反斜杠；需要插值时仍然加 `f`：

```scoop
val directory = "docs"
val path = """C:\work\scoop"""
val message = f"""Input: ${directory}
Keep \n as two characters."""
println(path)
println(message)
```

`String.charLength` 返回 Unicode 标量数量，类型为 `Long`；UTF-8 字节数需要通过字节表示取得：

```scoop
val text = "A中"
println(f"scalars=${text.charLength}, bytes=${text.toByteArray().size}")
for (character in text) {
    println(character)
}
```

第一行输出 `scalars=2, bytes=4`，后面分别输出 `A` 和 `中`。标量数量不等于用户看到的字形数量：组合字符和部分 emoji 可能包含多个标量。本文的统计程序计算标量数量。

## 5. 函数与返回值

参数类型写在参数名后，返回类型写在参数列表后：

```scoop
fun twice(value: Int): Int = value * 2

fun add(left: Int, right: Int): Int {
    return left + right
}

fun main() {
    println(twice(3))
    println(add(4, 5))
}
```

输出 `6` 和 `9`。`=` 后的表达式直接提供函数结果；这种表达式体也可以省略返回类型，由定义处的表达式推断，例如 `fun twice(value: Int) = value * 2`。

`{ … }` 块体需要显式 `return` 才能返回业务值，最后一个表达式不会自动变成函数返回值。块体省略返回类型时，函数的返回类型是 `Unit`；要返回 `Int`，就同时写出 `: Int` 和 `return`。所有可能正常结束的路径都必须符合声明的返回类型。

## 6. 分支也是表达式

### if

`if` 可以控制是否执行语句，也可以产生一个值。作为值使用时，需要 `else`：

```scoop
val score = 82
val result = if (score >= 60) "pass" else "retry"
if (score >= 80) {
    println("Good work")
}
println(result)
```

分支内有多条语句时，用块的最后一个表达式提供分支结果。这与上一节“具名函数的块体必须显式 `return`”不同：这里返回的是 `if` 表达式的结果。

### when

`when` 适合多分支判断。带 subject 时，各分支和这个值比较：

```scoop
val command = "build"
val action = when (command) {
    "build" -> "compile"
    "run" -> "compile and execute"
    else -> "show help"
}
println(action)
```

没有 subject 时，分支条件直接写布尔表达式：

```scoop
val score = 82
val grade = when {
    score >= 90 -> "A"
    score >= 60 -> "B"
    else -> "C"
}
println(grade)
```

两种写法都只执行第一个匹配的分支，没有向下一分支继续执行的行为，也不需要在分支末尾加 `break`。用作值的 `when` 必须覆盖所有情况；以上例子通过 `else` 保证这一点。针对 enum、tuple 和 struct 的 `case` 模式匹配见[语言导览](../docs/tour.html#enums)。

## 7. 数组、循环与区间

### 从元素或下标遍历

数组字面量写作 `[…]`，得到只读的 `Array<T>`。数组长度和下标都是 `Long`：

```scoop
val names = ["Ada", "Lin", "Sam"]
println(names[0L])
for (name in names) {
    println(name)
}
for (index in 0L until names.size) {
    println(f"${index}: ${names[index]}")
}
```

`names` 的类型是 `Array<String>`。`for` 的迭代变量在每次迭代中只读；需要累计结果时，在循环外声明一个 `var`。不能通过 `names[0L] = "New"` 修改只读数组；需要添加、移除元素时，可以使用前文的 `ArrayList`。

### 区间的端点与步长

| 写法 | 依次产生的值 |
| --- | --- |
| `1..3` | `1, 2, 3`，包含右端点 |
| `1..<3` 或 `1 until 3` | `1, 2`，不包含右端点 |
| `3 downTo 1` | `3, 2, 1`，降序且包含右端点 |
| `(1..5) step 2` | `1, 3, 5` |
| `3..1` | 空区间，不自动改成降序 |
| `'a'..'e'` | `'a', 'b', 'c', 'd', 'e'`，按 Unicode 标量顺序 |

例如：

```scoop
var total = 0
for (value in (1..5) step 2) {
    total += value
}
println(total)
```

输出 `9`。`step` 必须大于零，它改变步长而不改变方向；降序用 `downTo`。`Long` 区间应配合 `Long` 操作数和步长，例如 `(1L..5L) step 2L`。遍历数组下标时用 `0L until names.size`，不要把等于长度的下标包含进来。字符区间的 `step` 参数是 `Int`，例如 `('a'..'z') step 2`；规则见参考文档的[字符区间](../reference/expressions.html#char-ranges)。

### while、do/while 与循环控制

`while` 在执行前检查条件，`do/while` 至少执行一次循环体。`continue` 跳过本轮剩余语句，`break` 结束当前循环：

```scoop
var remaining = 3
while (remaining > 0) {
    println(remaining)
    remaining -= 1
}
do {
    remaining += 1
} while (remaining < 1)
println(f"after=${remaining}")

for (value in 1..5) {
    if (value == 2) continue
    if (value == 4) break
    println(value)
}
```

前半段输出 `3`、`2`、`1`、`after=1`，后半段输出 `1`、`3`。嵌套循环中的普通 `break`/`continue` 作用于最近一层循环。

## 8. 程序入口、参数与退出码

入口是顶层、非泛型、非 `suspend` 的 `main` 函数。根据是否需要命令行参数和退出码，选择下面四种签名之一：

| 签名 | 正常结束的退出码 |
| --- | --- |
| `fun main()` | `0`，返回类型默认为 `Unit` |
| `fun main(args: Array<String>)` | `0` |
| `fun main(): Int` | 返回的 `Int` |
| `fun main(args: Array<String>): Int` | 返回的 `Int` |

**`args[0L]` 是程序自身的启动路径，用户参数从 `args[1L]` 开始。** 没有用户参数时，`args.size` 仍为 `1L`。参数中的空字符串也会保留，不会再次按空格拆分。

```scoop
fun main(args: Array<String>): Int {
    println(f"arguments=${args.size - 1L}")
    for (index in 1L until args.size) {
        println(f"${index}: ${args[index]}")
    }
    return 0
}
```

保存为 `arguments.scoop`，用 `--` 分隔 Scoop 选项和程序参数：

```sh
scoop run arguments.scoop --release -- Ada "hello world"
```

输出：

```text
arguments=2
1: Ada
2: hello world
```

返回 `0` 通常表示成功，非零值用于表示错误。Scoop 接受任意 `Int` 退出码；在 macOS/Linux 的 shell 中，通常只能观察正常退出值的低 8 位；Windows 保留完整的 32 位退出码。普通 CLI 使用较小的非零退出码即可。

## 9. 完整示例：统计输入的文本

把下面的程序保存为 `word-stats.scoop`，也可以[下载同一份源码](examples/word-stats.scoop)。它统计非空参数的数量、Unicode 标量总数和平均长度，并选择最长的参数；长度相同时保留先出现的一个。

```scoop
{% include_relative examples/word-stats.scoop %}
```

在文件所在目录执行：

```sh
scoop run word-stats.scoop --release -- Scoop 中文 ""
```

输出：

```text
{% include_relative examples/word-stats.out %}
```

这里 `Scoop` 有 5 个标量，`中文` 有 2 个；空字符串通过 `continue` 跳过。总数和下标使用 `Long`，计算平均值前显式转成 `Double`，所以得到 `3.5`。

再验证两个错误输入：

```sh
scoop run word-stats.scoop --release
echo $?

scoop run word-stats.scoop --release -- ""
echo $?
```

第一条程序命令输出 `Usage: word-stats <word> [word ...]`，第二条输出 `No non-empty words.`；各自紧随的 `echo $?` 都应输出 `2`。程序在除法前检查数量，避免对空输入计算平均值。

## 10. 常见误解与继续阅读

以下几条尤其容易与 Kotlin 或其他语言混淆：

| 容易写错的地方 | Scoop 的写法或语义 |
| --- | --- |
| 在普通 `"…"` 中插值，或写 `f"$name"` | 使用 `f"${name}"` |
| 直接把已有的 `Int` 和 `Long` 相加 | 先显式转换，例如 `count.toLong() + size` |
| 认为数组下标和长度都是 `Int` | 使用 `Long`，循环从 `0L` 开始 |
| 认为 `val` 保证对象内容不可变 | `val` 只禁止重新绑定；内容能否修改取决于类型和 API |
| 用具名函数块体的最后一个表达式返回值 | 声明返回类型，并写 `return` |
| 把 `args[0L]` 当成第一个用户参数 | 第一项是程序路径，用户参数从 `1L` 开始 |
| 用 `null` 表示缺失值 | Scoop 没有运行期 `null`；`T?` 是 `Option<T>`，用 `Some(value)` 或 `None` |
| 默认公开项目中的所有声明 | 默认可见性规则与 Kotlin 不同；跨 Cone API 需按规则显式声明 `public` |
| 直接使用 Java 或 `kotlinx` API | Scoop 使用自己的 core 和标准库，没有 JVM 依赖 |

例如，一个缺省的可选名字可以这样处理：

```scoop
val nickname: String? = None
val displayName = nickname ?: "anonymous"
println(displayName)
```

这里的 `?:` 在值为 `None` 时使用右侧缺省值。下一步可以阅读[语言导览中的值类型与 Option](../docs/tour.html#structs)、[库 Cone 一览](../reference/stdlib.html)和 [Kotlin 差异](../docs/kotlin.html)。完整规则见[参考文档](../reference/index.html)；后续专题的范围和进度见[用户文档大纲]({{ '/outline.html' | relative_url }})。
