"""
单文件生成器

负责生成单个双语对照HTML文件。
"""

import html as html_module
import json
import hashlib
from pathlib import Path

from .base import Generator
from ..core.text_processor import parse_lines, validate_line_counts
from ..templates.renderer import TemplateRenderer
from ..templates.state_manager import get_state_manager_code


class SingleFileGenerator(Generator):
    """单文件HTML生成器"""

    def __init__(
        self,
        main_file: Path,
        side_file: Path,
        title: str = "Bilingual Viewer",
        primary: str = "a",
        orientation: str = "vertical",
        sync: bool = False,
        ignore_empty: bool = True,
    ):
        """
        初始化单文件生成器。

        Args:
            main_file: 主文档文件路径
            side_file: 从文档文件路径
            title: HTML页面标题
            primary: 默认主文档 ('a' 或 'b')
            orientation: 页面布局方向
            sync: 是否启动时显示同步模式
            ignore_empty: 是否忽略空白行
        """
        self.main_file = main_file
        self.side_file = side_file
        self.title = title
        self.primary = primary
        self.orientation = orientation
        self.sync = sync
        self.ignore_empty = ignore_empty
        self.renderer = TemplateRenderer()

        # 验证文件存在
        if not main_file.exists():
            raise FileNotFoundError(f"Main file not found: {main_file}")
        if not side_file.exists():
            raise FileNotFoundError(f"Side file not found: {side_file}")

    def generate(self, output_path: Path) -> None:
        """
        生成单个HTML文件。

        Args:
            output_path: 输出文件路径
        """
        # 读取和解析文本
        main_lines = parse_lines(self.main_file, ignore_empty=self.ignore_empty)
        side_lines = parse_lines(self.side_file, ignore_empty=self.ignore_empty)

        # 提取文件标题
        main_title = self._get_title(self.main_file, main_lines)
        side_title = self._get_title(self.side_file, side_lines)

        # 移除第一行（标题），从第二行开始作为正文
        main_lines = main_lines[1:] if len(main_lines) > 1 else []
        side_lines = side_lines[1:] if len(side_lines) > 1 else []

        # 验证和对齐行数，传入文件路径以便在发生不一致时输出问题文件名
        main_lines, side_lines = validate_line_counts(
            main_lines, side_lines, str(self.main_file), str(self.side_file)
        )

        # 生成行对
        pairs = [
            [
                html_module.escape(a, quote=False),
                html_module.escape(b, quote=False),
            ]
            for a, b in zip(main_lines, side_lines)
        ]

        # 生成文档ID（用于本地存储隔离）
        pairs_json = json.dumps(pairs, ensure_ascii=False)
        doc_id = hashlib.sha1(pairs_json.encode("utf-8")).hexdigest()[:10]

        # 生成标题JSON
        titles_json = json.dumps({"a": main_title, "b": side_title}, ensure_ascii=False)

        # 获取状态管理器代码
        state_manager_code = get_state_manager_code(doc_id)

        # 渲染模板
        # 在渲染前可选地输出调试信息（通过环境变量启用），以便验证计数来源
        import os
        if os.environ.get('PTV_DEBUG_COUNTS') == '1':
            print(f"DEBUG COUNTS (single_file): main={len(main_lines)} side={len(side_lines)} pairs={len(pairs)}")

        html_content = self.renderer.render_single_file(
            title=self.title,
            count=len(pairs),
            pairs_json=pairs_json,
            titles_json=titles_json,
            state_manager_code=state_manager_code,
            orientation=self.orientation,
        )

        # 写入输出文件
        output_path.write_text(html_content, encoding="utf-8")

    def _get_title(self, file_path: Path, lines: list[str]) -> str:
        """从文件内容或路径提取标题"""
        if lines and file_path.suffix.lower() == ".md" and lines[0].strip().startswith("#"):
            title_line = lines[0].strip()
            # 去掉#和前后的空格
            return title_line.lstrip("#").strip()
        else:
            # 使用文件名作为标题
            return file_path.stem