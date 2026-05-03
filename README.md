# Parallel Text Viewer

一个用于将两份逐行对应文本生成为离线查看 HTML 的工具。支持中英双语对比、Markdown 格式、图片嵌入和响应式布局。

**版本**: 0.7.0 | **许可证**: MIT | **Python**: ≥3.7

## 主要功能

- ✅ **双语对比**：将配对的文本（中文/英文或任意两种语言）并排显示
- ✅ **灵活布局**：支持垂直/水平并排、可选行级同步滚动
- ✅ **Markdown 支持**：自动解析标题、图片链接，转换为 HTML
- ✅ **图片处理**：自动识别和复制图片，支持两种策略（目录级或显式映射）
- ✅ **行对齐**：自动检测并填充不同行数的文本
- ✅ **离线浏览**：生成完全独立的 HTML，无外部依赖
- ✅ **多卷支持**：支持组织成多卷多章节的书籍结构
- ✅ **CLI + API**：提供命令行和 Python 编程接口
- ✅ **高层 API**：`build_from_data()` 函数提供端到端构建

## 快速开始

### 安装

```bash
# 从源码安装
git clone https://github.com/LoveElysia1314/parallel-text-viewer.git
cd parallel-text-viewer
pip install -e .
```

### 最简单的使用方式（推荐）

```bash
python scripts/build_from_data.py [data_path] [output_dir] [book_id]
```

示例：
```bash
# 使用默认参数
python scripts/build_from_data.py

# 自定义数据源和输出位置
python scripts/build_from_data.py data output 2930
```

打开 `output/index.html` 即可在浏览器中查看生成的书籍。

## 数据结构

组织源文件如下：

```
data/
└── chapters/
    └── 2930/                    # book_id
        ├── vol_001/             # 卷
        │   ├── cn/              # 中文文本文件 (.md 或 .txt)
        │   │   ├── 118227.md
        │   │   ├── 118228.md
        │   │   └── ...
        │   ├── en/              # 英文文本文件
        │   │   ├── 118227.md
        │   │   ├── 118228.md
        │   │   └── ...
        │   └── images/          # 该卷的图片（可选）
        │       └── *.jpg
        ├── vol_002/
        └── ...

images/                         # 全局图片库（可选）
└── 2930/
    ├── vol_001/
    │   └── *.jpg
    └── ...
```

**文件格式**：
- **纯文本**（`.txt`）：逐行读取，自动去空行
- **Markdown**（`.md`）：支持标题 `# Title`、图片 `![alt](url)`

示例 Markdown 文件：

```markdown
# 第1话 标题

这是第一行正文。

![插图-1](../../../../images/2930/vol_001/image_1.jpg)

这是带图片的一行。
```

## 项目结构

```
parallel_text_viewer/
├── __init__.py              # 公开 API 导出
├── __main__.py              # CLI 入口
├── cli.py                   # 参数解析 + 命令分发
├── core.py                  # 数据模型、文本处理、路径解析、构建 API、配置生成器
├── generators.py            # HTML 生成器（单文件、书籍索引、工厂）
├── renderer.py              # 模板渲染引擎 + 状态管理器
├── utils.py                 # 工具函数（文件、图片、路径）
└── html_templates/          # HTML 模板文件
    ├── common.css, common.js
    ├── chapter.css, chapter.html, chapter.js
    ├── index.css, index.html, index.js
    └── state_manager.js
```

## 使用示例

### 方式 1：一键构建（推荐）

```bash
python scripts/build_from_data.py data output 2930
```

自动完成 5 个步骤：
1. 发现工作目录
2. 生成配置文件
3. 验证配置
4. 生成 HTML
5. 复制图片

### 方式 2：Python 高层 API

```python
from parallel_text_viewer.core import build_from_data, BuildOptions

# 基本使用
result = build_from_data(BuildOptions(
    data_root="data",
    output_dir="output",
    book_id="2930"
))

if result.success:
    print(f"✓ 构建成功！输出位置: {result.output_dir}")
    print(f"  已复制 {result.images_copied} 张图片")
else:
    for error in result.errors:
        print(f"✗ {error}")
```

### 方式 3：CLI 分步执行

```bash
# 步骤 1: 生成配置文件
python -m parallel_text_viewer gen-config \
  --book-id 2930 \
  --title "书籍标题" \
  --working-dir ./data/chapters/2930 \
  -o output/config.json

# 步骤 2: 验证配置
python -m parallel_text_viewer validate-config output/config.json

# 步骤 3: 生成 HTML
python -m parallel_text_viewer book_index \
  --index output/config.json \
  -d output/
```

### 方式 4：Python 低层 API

**单文件生成**：

```python
from parallel_text_viewer import SingleFileGenerator

gen = SingleFileGenerator(
    main_file="data/chapter_cn.md",
    side_file="data/chapter_en.md",
    title="My Book",
    orientation="vertical"
)
gen.generate(output_dir="output/")
```

**书籍索引生成**：

```python
from parallel_text_viewer import BookIndexGenerator

gen = BookIndexGenerator(config_file="output/config.json")
gen.generate(output_dir="output/")
```

**工厂模式**：

```python
from parallel_text_viewer import GeneratorFactory

factory = GeneratorFactory()

single = factory.create_single_file_generator(
    main_file="main.md",
    side_file="side.md"
)

book = factory.create_book_index_generator(
    config_file="config.json"
)
```

## 配置文件（Config v2.0）

自动生成的 `config.json` 示例：

```json
{
  "meta": {
    "book_id": "2930",
    "title": "示例书名",
    "images": {
      "base_path": "images",
      "strategy": "directory"
    }
  },
  "works": [
    {
      "work_id": "work_1",
      "volumes": [
        {
          "volume_id": "vol_001",
          "chapters": [
            {
              "chapter_id": "118227",
              "title": "第1话",
              "main_text": "data/chapters/2930/vol_001/cn/118227.md",
              "side_text": "data/chapters/2930/vol_001/en/118227.md",
              "images": {
                "files": {}
              }
            }
          ]
        }
      ]
    }
  ]
}
```

## 输出说明

```
output/
├── index.html               # 书籍索引主页
├── config.json              # 使用的配置文件
├── volumes/
│   └── vol_001/
│       ├── chapter_1.html   # 章节页面（双语对比）
│       └── ...
└── images/
    └── 2930/
        └── vol_001/
            └── *.jpg        # 自动复制的图片
```

打开 `index.html` 查看完整的书籍索引和导航。

## 核心 API

### 文本处理

```python
from parallel_text_viewer.core import parse_lines, parse_md_lines, validate_line_counts

# 读取纯文本行
lines = parse_lines(Path("file.txt"))

# 读取 Markdown 并提取标题
title, lines = parse_md_lines(Path("file.md"))

# 验证和对齐行数
main_lines, side_lines = validate_line_counts(
    main_lines, side_lines,
    main_identifier="cn",
    side_identifier="en"
)
```

### 生成器

```python
from parallel_text_viewer import SingleFileGenerator, BookIndexGenerator

# 单文件
gen = SingleFileGenerator(
    main_file=Path("main.md"),
    side_file=Path("side.md"),
    title="Title",
    primary="a",              # 主文本为 a 或 b
    orientation="vertical",   # 垂直或水平
    sync=False,               # 是否同步滚动
)
gen.generate(output_dir=Path("output"))

# 书籍
gen = BookIndexGenerator(config_file=Path("config.json"))
gen.generate(output_dir=Path("output"))
```

## 常见问题

**Q: 图片为什么不显示？**

A: 确保：
- 图片文件在 `data/images/` 或对应卷的 `images/` 目录
- `output/images/` 包含图片副本
- 检查浏览器控制台查看 404 错误

**Q: 中英文行数不对齐怎么办？**

A: 生成器会自动用空行填充较短的文本。可在 HTML 中手动编辑行对应关系。

**Q: 能否自定义样式？**

A: 修改 `parallel_text_viewer/html_templates/` 中的模板文件，重新生成 HTML 即可应用新样式。

**Q: 支持哪些格式？**

A: 
- 输入：`.md`（Markdown）、`.txt`（纯文本）
- 图片：`.jpg`、`.png`、`.gif` 等常见格式

## 技术细节

- **语言**：Python 3.7+
- **依赖**：仅使用标准库（pathlib、json、re、logging、abc、dataclasses）
- **模板**：内置 HTML 生成（无 Jinja2 等依赖）

## 许可证

MIT License © 2025 Elysia - 详见 [LICENSE](LICENSE)

## 更新日志

### v0.7.0 (2026-05-04)
- ✅ 架构扁平化：6 个子包合并为 6 个顶层模块
- ✅ 删除 600+ 行过时代码和遗留文档
- ✅ 35 个测试全部通过
- ✅ 保留完整的 API 兼容性

### v0.6.0 (2025-12-04)
- ✅ 首个稳定发布版本
- ✅ Config v2.0 配置格式
- ✅ 改进的图片路径处理（仅保留文件名）
- ✅ 完整行对齐和填充
- ✅ 支持 CLI 和 Python API
- ✅ 安全的项目清理（构建产物归档）