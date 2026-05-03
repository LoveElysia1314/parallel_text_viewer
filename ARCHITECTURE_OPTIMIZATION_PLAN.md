# 项目架构优化计划书

## 概述

本文档基于对 `parallel-text-viewer` 项目的全面分析，识别冗余文件和过时代码，并提出架构扁平化与清理方案。当前项目核心功能稳定（28 个测试全部通过），但存在大量历史遗留问题。

---

## 一、可安全删除的冗余文件

### 1.1 已弃用的模板 Python 模块

这四个 `.py` 文件中的 CSS/JS/HTML 内容已迁移至 `templates/html/` 目录下的独立文件（`.css`、`.js`、`.html`），`renderer.py` 已从独立文件读取。这些 `.py` 文件未被任何外部模块导入，可以安全删除。

| 文件 | 原因 | 内部引用关系 |
|------|------|-------------|
| `parallel_text_viewer/templates/chapter_template.py` | 自身标注"已弃用" | 仅内部引用 common_template |
| `parallel_text_viewer/templates/common_template.py` | 自身标注"已弃用" | 被上两者引用，无外部引用 |
| `parallel_text_viewer/templates/html_template.py` | 被 renderer 取代 | 无任何引用 |
| `parallel_text_viewer/templates/index_template.py` | 自身标注"已弃用" | 仅内部引用 common_template |

**预计释放**: ~750 行代码

### 1.2 历史清理记录文档

这些文档来自之前的清理迭代，对当前用户和开发者无参考价值。

| 文件 | 原因 |
|------|------|
| `CLEANUP_PLAN.md` | 上一次清理的计划，已完成 |
| `COMPLETION_SUMMARY.md` | 上一次清理的总结 |
| `FINAL_STATUS_REPORT.md` | 项目状态报告，内容已过时 |
| `API_REFERENCE.md` | API 文档与 README 和代码 docstring 大量重复 |

> ⚠️ `API_REFERENCE.md` 的保留与否取决于策略：若需对外提供详细 API，可保留；若追求精简可删除，因 README.md 已涵盖主要用法。

### 1.3 v1.0 遗留概念文件

| 文件 | 原因 |
|------|------|
| `naming_rule_demo_2930.json` | v1.0 概念验证配置文件，已不再使用 |
| `scripts/verify_config_v2.py` | v1→v2 迁移的一次性验证脚本，不再需要 |
| `scripts/README.md` | 引用的脚本多数已被删除（check_catalog_images.py 等） |

---

## 二、含冗余/可精简的代码模块

### 2.1 `generators/base.py` — 最小基类

```python
class Generator(ABC):
    @abstractmethod
    def generate(self, output_path: Path) -> None:
        pass
```

仅 4 行有效的抽象基类。`SingleFileGenerator` 和 `BookIndexGenerator` 是本项目仅有的两个生成器，且不共享任何其他接口。建议：

- **方案 A**：删除 `base.py`，让生成器直接实现各自接口（最轻量）
- **方案 B**：保留但合并到 `factory.py` 中

### 2.2 `generators/navigation.py` — 功能过于简单

```python
class NavigationGenerator:
    def generate_navigation(self, nav_info: Dict) -> str:
        html = f"""..."""
        return html
```

仅 ~20 行、1 个方法、1 个使用方（`BookIndexGenerator`）。建议直接内联到 `book_index.py` 的对应方法中。

### 2.3 `utils/file_utils.py` — 函数过于微小

两个函数分别只有 2 行和 6 行有效代码。考虑到仅被 `book_index.py` 引用，可以内联或合并。

### 2.4 `core/validator.py` vs `core/config_v2.py` — 重复验证逻辑

- `core/validator.py`: `ConfigValidator` 类，基于 dict 的验证
- `core/config_v2.py`: `ConfigLoader.validate()` 静态方法，基于 dataclass 的验证

两者功能重叠，但 `validator.py` 的 `ConfigValidator` 不在 `build.py` 的流程中使用（后者使用 `ConfigLoader.validate()`）。**`ConfigValidator` 已事实上被取代**。

### 2.5 `core/image_placeholder.py` — 未使用的特性

实现 `{IMG:chapter_id_index}` 占位符系统（~200 行），但：
- `text_processor.py` 中的 `parse_md_lines()` 已处理标准 Markdown 图片 `![alt](url)`
- `image_placeholder.py` 未被任何核心生成流程导入
- 测试文件对该模块的测试也是概念性的（无实际文件结构）

### 2.6 `config/generator.py` — 臃肿且部分未使用

`CrawlerOutputGenerator` 和 `CSVConfigGenerator` 两个生成器类以及 `GeneratorRegistry` 注册表模式，合计 ~200 行。实际流程中仅使用 `StandardConfigGenerator`。

---

## 三、架构扁平化方案

### 当前目录结构（5 个子包 + 模板子目录）

```
parallel_text_viewer/
├── __init__.py
├── __main__.py
├── cli/           → 2 文件 (parser.py, dispatcher.py)
├── config/        → 1 文件 (generator.py)
├── core/          → 6 文件
├── generators/    → 5 文件 (含 4 行 base.py, 20 行 navigation.py)
├── templates/     → 5 py + 9 html 文件
└── utils/         → 3 文件
```

### 建议的扁平化方案

**方案：压缩为 3 个子包 + 1 模板目录**

```
parallel_text_viewer/
├── __init__.py          # 公开 API 导出
├── __main__.py          # CLI 入口（吸收 cli/ 功能）
├── cli.py               # 合并 parser + dispatcher（或保留 cli/ 但扁平）
├── core.py              # 合并 core/* + config/generator.py
├── generators.py        # 合并 generators/*（除 templates 外的生成器代码）
├── utils.py             # 合并 utils/*
├── html_templates/      # 重命名 templates/html/，删除冗余 .py
│   ├── chapter.css, chapter.html, chapter.js
│   ├── common.css, common.js
│   ├── index.css, index.html, index.js
│   └── state_manager.js
└── renderer.py          # 从 templates/ 提出，负责模板渲染
```

### 具体合并映射

| 当前 | 目标 | 说明 |
|------|------|------|
| `cli/parser.py` | `cli.py` 中的 `ArgumentParser` | 直接移入 |
| `cli/dispatcher.py` | `cli.py` 中的 `CommandDispatcher` | 直接移入 |
| `core/build.py` | `core.py` 中的 `BuildExecutor` + `build_from_data` | 保留 |
| `core/config_v2.py` | `core.py` 中的 `ConfigV2` + `ConfigLoader` | 保留 |
| `core/text_processor.py` | `core.py` 中的 `parse_lines` 等 | 保留 |
| `core/path_resolver.py` | `core.py` 中的 `PathResolver` | 保留 |
| `core/validator.py` | **删除** (被 `ConfigLoader.validate()` 取代) | 删除 |
| `core/image_placeholder.py` | **删除** (未使用) | 删除 |
| `config/generator.py` | `core.py` 中的生成器类 | 仅保留 `StandardConfigGenerator` |
| `generators/base.py` | **删除** | 合并入 `generators.py` |
| `generators/navigation.py` | **删除** | 内联到 `book_index.py` |
| `generators/single_file.py` | `generators.py` | 保留 |
| `generators/book_index.py` | `generators.py` | 保留 |
| `generators/factory.py` | `generators.py` | 保留 |
| `templates/renderer.py` | `renderer.py` | 提升到顶层 |
| `templates/state_manager.py` | `renderer.py` | 合并入渲染器 |
| `templates/html/*` | `html_templates/*` | 重命名目录，内容不变 |
| `templates/*.py` (废弃) | **删除** | 已迁移到 html/ |
| `utils/file_utils.py` | `utils.py` | 合并 |
| `utils/image_utils.py` | `utils.py` | 合并 |
| `utils/path_utils.py` | `utils.py` | 合并 |

### 扁平化后的项目结构

```
parallel_text_viewer/
├── __init__.py          # 公开 API
├── __main__.py          # CLI 入口 (精简)
├── cli.py               # 参数解析 + 命令分发
├── core.py              # 核心：数据模型、配置、文本处理、路径解析、构建API
├── generators.py        # HTML 生成器：单文件、书籍索引、工厂
├── renderer.py          # 模板渲染引擎 + 状态管理器
├── utils.py             # 工具函数：文件、图片、路径
└── html_templates/      # 独立模板文件
    ├── chapter.css, chapter.html, chapter.js
    ├── common.css, common.js
    ├── index.css, index.html, index.js
    └── state_manager.js
```

从 **5 子包 + 1 模板目录** 减少到 **1 子目录 + 6 顶层模块**。

---

## 四、脚本清理

| 文件 | 建议 |
|------|------|
| `scripts/build_from_data.py` | ✅ 保留（主要入口脚本） |
| `scripts/verify_config_v2.py` | ❌ 删除（一次性验证脚本） |
| `scripts/README.md` | ❌ 删除（引用的脚本已不存在） |

用户示例 `examples/build_api_usage.py` 和 `demo/` 目录可根据需要保留或删除（非核心功能）。

---

## 五、测试文件调整

| 当前 | 建议 |
|------|------|
| `tests/test_build_api.py` | ✅ 保留（核心 API 测试） |
| `tests/test_config_v2_integration.py` | 需要更新引用路径 |
| `tests/test_image_copy.py` | 需要检查是否仍相关 |

---

## 六、分阶段执行计划

### 第一阶段：安全删除（无风险）

1. 删除 4 个已弃用的模板 `.py` 文件
2. 删除 3 个历史清理文档（CLEANUP_PLAN 等）
3. 删除 `naming_rule_demo_2930.json`
4. 删除 `scripts/verify_config_v2.py` 和 `scripts/README.md`

### 第二阶段：代码精简（低风险）

1. 删除 `generators/base.py`，抽象接口内联
2. 删除 `generators/navigation.py`，内联到 `book_index.py`
3. 删除 `core/validator.py`（已被取代）
4. 删除 `core/image_placeholder.py`（未使用）
5. 清理 `config/generator.py`：仅保留 `StandardConfigGenerator`

### 第三阶段：架构扁平化（中等风险）

1. 创建 `cli.py` → 合并 `cli/` 下所有内容
2. 创建 `core.py` → 合并 `core/*` + `config/generator.py`
3. 创建 `generators.py` → 合并 `generators/*`（已精简后的）
4. 创建 `utils.py` → 合并 `utils/*`
5. 提升 `renderer.py` 到顶层 + 合并 `state_manager.py`
6. 重命名 `templates/html/` → `html_templates/`

### 第四阶段：验证与修复

1. 更新 `__init__.py` 导出路径
2. 更新 `__main__.py` 导入路径
3. 更新 `setup.py` / `pyproject.toml` 包配置
4. 运行全部测试确认通过
5. 运行实际构建确认功能正常

---

## 七、预计成果

| 指标 | 当前 | 优化后 | 变化 |
|------|------|--------|------|
| 顶层 `.py` 文件数（包内） | 19+ 文件 | ~6 文件 | ↓ **68%** |
| 子包/目录数 | 6 个 | 1 个 | ↓ **83%** |
| 冗余 `.py` 文件 | ~6 个 | 0 | 全部清除 |
| 历史文档 | 4-5 个 | 1-2 个 | ↓ **60%** |
| 测试通过率 | 28/28 | 28/28 | ✅ 保持 |
