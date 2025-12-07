# Parallel Text Viewer - API 参考文档

## 目录

1. [高级 API（推荐）](#高级-api)
2. [图片和文件处理](#图片和文件处理)
3. [路径解析和工作目录发现](#路径解析和工作目录发现)
4. [配置和验证](#配置和验证)
5. [命令调度器](#命令调度器)
6. [使用示例](#使用示例)

---

## 高级 API

### `build_from_data()`

**模块:** `parallel_text_viewer.core.build`

端到端的构建 API，自动处理工作目录发现、配置生成、验证和 HTML 输出。

#### 签名

```python
def build_from_data(options: BuildOptions) -> BuildResult:
    """
    从 data 文件夹构建完整的 HTML 输出（5步流程）。
    
    参数:
        options: BuildOptions 对象，包含构建配置
    
    返回:
        BuildResult 对象，包含构建结果和统计信息
    """
```

#### BuildOptions 数据类

```python
@dataclass
class BuildOptions:
    """构建选项配置"""
    
    # 必需参数
    data_root: Path | str = "data"
        """数据根目录路径"""
    
    output_dir: Path | str = "output"
        """输出目录路径"""
    
    book_id: str = "2930"
        """书籍 ID（用于发现工作目录）"""
    
    # 可选参数
    patterns: Dict[str, str] | None = None
        """自定义路径模式字典，支持占位符: {book_id}, {volume}, {chapter}, {lang}"""
    
    candidates: List[str] | None = None
        """工作目录候选名称列表（发现顺序）"""
    
    validate_config: bool = True
        """是否验证配置文件"""
    
    copy_images: bool = True
        """是否复制图片文件"""
    
    preserve_image_structure: bool = True
        """复制图片时是否保留目录结构"""
    
    search_recursive_images: bool = False
        """是否递归搜索所有子目录中的图片"""
```

#### BuildResult 数据类

```python
@dataclass
class BuildResult:
    """构建结果对象"""
    
    success: bool
        """是否成功"""
    
    config_file: Path | None = None
        """生成的配置文件路径"""
    
    output_dir: Path | None = None
        """输出目录路径"""
    
    working_dir: Path | None = None
        """发现的工作目录路径"""
    
    images_copied: int = 0
        """成功复制的图片数量"""
    
    images_failed: int = 0
        """复制失败的图片数量"""
    
    errors: List[str] = field(default_factory=list)
        """错误消息列表"""
```

#### 执行步骤

1. **工作目录发现**: 在 `data_root` 中查找包含书籍资源的实际目录
2. **配置生成**: 从工作目录的文件结构生成 ConfigV2 格式的配置文件
3. **配置验证**: 验证生成的配置文件的有效性
4. **HTML 生成**: 使用配置生成 HTML 输出
5. **图片复制**: 将图片从源复制到输出目录（可选）

#### 基本示例

```python
from parallel_text_viewer.core.build import build_from_data, BuildOptions
from pathlib import Path

# 简单使用（使用默认值）
result = build_from_data(BuildOptions(
    data_root="data",
    output_dir="output",
    book_id="2930"
))

if result.success:
    print(f"✓ 构建成功！")
    print(f"  输出位置: {result.output_dir}")
    print(f"  配置文件: {result.config_file}")
    print(f"  图片复制: {result.images_copied} 张")
else:
    for error in result.errors:
        print(f"✗ {error}")
```

#### 高级示例

```python
# 使用自定义模式和候选项
result = build_from_data(BuildOptions(
    data_root=Path("d:/data"),
    output_dir=Path("output"),
    book_id="2930",
    patterns={
        "config": "{data_root}/novels/{book_id}/config.json",
        "chapters": "{data_root}/novels/{book_id}/chapters",
    },
    candidates=["novel_{book_id}", "{book_id}", "chapters"],
    validate_config=True,
    copy_images=True,
    preserve_image_structure=True,
    search_recursive_images=False
))

if result.success:
    print(f"构建完成!")
    print(f"  工作目录: {result.working_dir}")
    print(f"  输出目录: {result.output_dir}")
    print(f"  成功复制: {result.images_copied}/{result.images_copied + result.images_failed} 图片")
else:
    print(f"构建失败，共 {len(result.errors)} 个错误:")
    for error in result.errors:
        print(f"  - {error}")
```

### PatternPathResolver

**模块:** `parallel_text_viewer.core.build`

路径模式解析器，支持占位符和 glob 通配符。

#### 签名

```python
class PatternPathResolver:
    """支持占位符和 glob 通配符的路径模式解析器"""
    
    def expand_pattern(pattern: str, **context) -> List[Path]:
        """
        展开路径模式。
        
        参数:
            pattern: 模式字符串，支持占位符 {book_id}, {volume}, {chapter}, {lang}
            context: 占位符的值（会自动添加 book_id）
        
        返回:
            匹配的 Path 对象列表
        """
```

#### 支持的占位符

- `{book_id}`: 自动从 BuildOptions 注入
- `{volume}`: 卷标识符（如 "vol_1"）
- `{chapter}`: 章节标识符
- `{lang}`: 语言代码（如 "en", "zh"）
- `*`: 匹配任意长度的字符序列
- `?`: 匹配单个字符

#### 示例

```python
from parallel_text_viewer.core.build import PatternPathResolver
from pathlib import Path

resolver = PatternPathResolver()

# 简单替换
paths = resolver.expand_pattern(
    "data/novels/{book_id}/chapters/*.md",
    book_id="2930"
)

# 包含 glob 通配符
paths = resolver.expand_pattern(
    "data/{book_id}/vol_*/chapter_*.md",
    book_id="2930"
)
```

---

## 图片和文件处理

### `copy_images_from_config()`

**模块:** `parallel_text_viewer.utils.image_utils`

根据配置文件中的图片路径引用复制图片到输出目录。

#### 签名

```python
def copy_images_from_config(
    config_path: Path | str,
    data_root: Path | str,
    output_dir: Path | str,
    preserve_structure: bool = True,
    search_recursive: bool = False,
    overwrite: bool = False,
    dry_run: bool = False
) -> Tuple[int, int]:
    """
    从配置文件中复制图片。
    
    参数:
        config_path: 配置文件路径（JSON 格式）
        data_root: 数据根目录
        output_dir: 输出目录
        preserve_structure: 是否保留原始目录结构
        search_recursive: 是否递归搜索子目录
        overwrite: 是否覆盖现有文件
        dry_run: 仅列出将复制的文件，不实际复制
    
    返回:
        (成功复制数, 失败数) 元组
    """
```

#### 示例

```python
from parallel_text_viewer.utils.image_utils import copy_images_from_config

# 基本用法
success, failed = copy_images_from_config(
    config_path="output/config.json",
    data_root="data",
    output_dir="output"
)

print(f"成功复制 {success} 张，失败 {failed} 张")

# 递归搜索图片（更慢但更全面）
success, failed = copy_images_from_config(
    config_path="output/config.json",
    data_root="data",
    output_dir="output",
    search_recursive=True,
    overwrite=True
)

# 预览模式（不实际复制）
success, failed = copy_images_from_config(
    config_path="output/config.json",
    data_root="data",
    output_dir="output",
    dry_run=True
)

print(f"将复制 {success} 张图片")
```

### `copy_files()`

**模块:** `parallel_text_viewer.utils.image_utils`

通用文件复制函数，支持通配符和过滤。

#### 签名

```python
def copy_files(
    sources: List[str],
    data_root: Path | str,
    output_dir: Path | str,
    preserve_structure: bool = True,
    overwrite: bool = False,
    dry_run: bool = False
) -> Tuple[int, int]:
    """
    复制文件列表到输出目录。
    
    参数:
        sources: 源文件路径列表（支持相对路径和通配符）
        data_root: 数据根目录
        output_dir: 输出目录
        preserve_structure: 是否保留目录结构
        overwrite: 是否覆盖现有文件
        dry_run: 仅列出将复制的文件
    
    返回:
        (成功复制数, 失败数) 元组
    """
```

#### 示例

```python
from parallel_text_viewer.utils.image_utils import copy_files

# 复制多个文件模式
success, failed = copy_files(
    sources=[
        "vol_1/images/*.jpg",
        "vol_2/images/*.png",
        "common/cover.jpg"
    ],
    data_root="data/book2930",
    output_dir="output"
)

print(f"复制结果: {success} 成功, {failed} 失败")
```

---

## 路径解析和工作目录发现

### `find_working_directory()`

**模块:** `parallel_text_viewer.utils.path_utils`

在给定的根目录中自动发现包含实际资源的工作目录。

#### 签名

```python
def find_working_directory(
    data_root: Path | str,
    book_id: str,
    candidates: List[str] | None = None
) -> Path | None:
    """
    查找实际的工作目录。
    
    参数:
        data_root: 数据根目录
        book_id: 书籍 ID
        candidates: 候选目录名称列表（优先级顺序）
    
    返回:
        发现的工作目录 Path，未找到则返回 None
    
    默认候选项（按优先级）:
        1. {root}/novel_{book_id}
        2. {root}/{book_id}
        3. {root}/chapters/{book_id}
        4. {root}（回退值）
    """
```

#### 搜索算法

1. 尝试用户提供的候选项（如果有）
2. 使用默认候选项列表：`novel_{book_id}` → `{book_id}` → `chapters/{book_id}` → `.`
3. 返回第一个存在的目录
4. 如果都不存在，返回根目录本身

#### 示例

```python
from parallel_text_viewer.utils.path_utils import find_working_directory

# 使用默认候选项
working_dir = find_working_directory("data", "2930")
if working_dir:
    print(f"工作目录: {working_dir}")

# 自定义候选项
working_dir = find_working_directory(
    "data",
    "2930",
    candidates=["novel_{book_id}", "Book_{book_id}", "{book_id}"]
)
```

---

## 配置和验证

### ConfigLoader

**模块:** `parallel_text_viewer.core.config_v2`

加载和解析 ConfigV2 格式的配置文件。

#### 签名

```python
class ConfigLoader:
    """ConfigV2 配置加载器"""
    
    @classmethod
    def load(cls, config_path: Path | str, working_dir: Path | str) -> dict:
        """
        加载配置文件。
        
        参数:
            config_path: 配置文件路径
            working_dir: 工作目录（用于相对路径解析）
        
        返回:
            解析后的配置字典
        
        异常:
            FileNotFoundError: 文件不存在
            ValueError: 配置格式无效
        """
    
    @classmethod
    def validate(cls, config: dict) -> Tuple[bool, List[str]]:
        """
        验证配置的有效性。
        
        参数:
            config: 配置字典
        
        返回:
            (是否有效, 错误消息列表) 元组
        """
```

#### 示例

```python
from parallel_text_viewer.core.config_v2 import ConfigLoader

# 加载配置
config = ConfigLoader.load("output/config.json", "data")

# 验证配置
is_valid, errors = ConfigLoader.validate(config)
if not is_valid:
    for error in errors:
        print(f"验证错误: {error}")
```

---

## 命令调度器

### CommandDispatcher

**模块:** `parallel_text_viewer.cli.dispatcher`

命令调度器，管理 gen-config、validate-config、book_index 等命令。

#### 签名

```python
class CommandDispatcher:
    """命令调度器"""
    
    def dispatch(self, config: dict) -> bool:
        """
        分发和执行命令。
        
        参数:
            config: 配置字典，必须包含 'mode' 字段
        
        返回:
            命令执行是否成功
        
        支持的模式:
            - "gen-config": 生成配置文件
            - "validate-config": 验证配置文件
            - "book_index": 生成 HTML 输出
        """
```

#### 示例

```python
from parallel_text_viewer.cli.dispatcher import CommandDispatcher

dispatcher = CommandDispatcher()

# 生成配置
config = {
    "mode": "gen-config",
    "book_id": "2930",
    "working_dir": "/path/to/data",
    "output": "/path/to/output/config.json"
}
success = dispatcher.dispatch(config)

# 生成 HTML
html_config = {
    "mode": "book_index",
    "index": "/path/to/output/config.json",
    "output_dir": "/path/to/output"
}
success = dispatcher.dispatch(html_config)
```

---

## 使用示例

### 示例 1: 最小化用法

```python
from parallel_text_viewer.core.build import build_from_data, BuildOptions

result = build_from_data(BuildOptions(book_id="2930"))
if result.success:
    print("✓ 构建成功")
```

### 示例 2: 自定义路径

```python
from pathlib import Path
from parallel_text_viewer.core.build import build_from_data, BuildOptions

result = build_from_data(BuildOptions(
    data_root=Path("D:/MyBooks/data"),
    output_dir=Path("D:/MyBooks/output"),
    book_id="2930"
))
```

### 示例 3: 跳过某些步骤

```python
from parallel_text_viewer.core.build import build_from_data, BuildOptions

result = build_from_data(BuildOptions(
    book_id="2930",
    validate_config=False,  # 跳过验证
    copy_images=False       # 不复制图片
))
```

### 示例 4: 自定义候选目录

```python
from parallel_text_viewer.core.build import build_from_data, BuildOptions

result = build_from_data(BuildOptions(
    book_id="2930",
    candidates=[
        "Book_{book_id}",
        "{book_id}",
        "novel_{book_id}"
    ]
))
```

### 示例 5: 使用自定义模式

```python
from parallel_text_viewer.core.build import build_from_data, BuildOptions

result = build_from_data(BuildOptions(
    book_id="2930",
    patterns={
        "chapters": "novels/{book_id}/chapters_zh/*.md",
        "images": "novels/{book_id}/images/vol_*/*.jpg"
    }
))
```

### 示例 6: 仅复制图片

```python
from parallel_text_viewer.utils.image_utils import copy_images_from_config

success, failed = copy_images_from_config(
    config_path="output/config.json",
    data_root="data",
    output_dir="output",
    preserve_structure=True,
    search_recursive=True
)

print(f"复制 {success} 张，失败 {failed} 张")
```

### 示例 7: 命令行使用

```bash
# 使用默认参数
python scripts/build_from_data.py

# 自定义参数
python scripts/build_from_data.py data output_book 2930

# 跳过图片复制
python scripts/build_from_data.py data output 2930 --no-images

# 跳过配置验证
python scripts/build_from_data.py data output 2930 --no-validate
```

---

## 错误处理

所有 API 函数都遵循一致的错误处理模式：

1. **BuildResult**: 包含 `success` 布尔值和 `errors` 列表
2. **返回元组**: 返回 `(success_count, failed_count)` 元组
3. **异常**: 关键错误会抛出异常，允许调用者自定义处理

### 推荐的错误处理模式

```python
from parallel_text_viewer.core.build import build_from_data, BuildOptions

try:
    result = build_from_data(BuildOptions(book_id="2930"))
    
    if not result.success:
        # 处理构建失败
        for error in result.errors:
            logger.error(f"构建错误: {error}")
        return False
    
    # 处理成功情况
    logger.info(f"输出位置: {result.output_dir}")
    
except Exception as e:
    # 处理异常
    logger.error(f"构建过程异常: {e}")
    return False
```

---

## 性能建议

1. **`search_recursive=True`**: 递归搜索所有子目录会显著降低性能，仅在必要时使用
2. **`preserve_structure=True`**: 保留目录结构的复制速度通常与覆盖式复制相同
3. **`dry_run=True`**: 在大规模复制前使用预览模式验证配置
4. **批量操作**: 对于多个书籍，多次调用 `build_from_data()` 不会产生性能问题

---

## 注意事项

1. **路径处理**: 所有路径参数都接受 `str` 或 `Path` 对象
2. **相对路径**: 相对路径相对于当前工作目录解析
3. **编码**: 所有文件 I/O 操作使用 UTF-8 编码
4. **日志**: 使用 Python 标准库的 `logging` 模块，可通过 `logging.getLogger()` 配置
5. **线程安全**: 所有 API 都是线程安全的（假设输出目录不冲突）

---

## 版本历史

### V2.0（当前）

- ✅ 高级 `build_from_data()` API
- ✅ Pattern 支持和 glob 通配符
- ✅ 工作目录自动发现
- ✅ 配置生成和验证
- ✅ 图片复制和文件管理
- ✅ 完整的命令行接口

### V1.0

- ConfigV2 基础架构
- HTML 生成引擎
- 基础图片处理

---

## 获取帮助

- **文档**: 查看 `README.md` 了解项目概况
- **示例**: 查看 `examples/` 目录的使用示例
- **脚本**: 参考 `scripts/build_from_data.py` 的命令行使用
- **测试**: 查看 `tests/` 目录了解 API 使用方式
