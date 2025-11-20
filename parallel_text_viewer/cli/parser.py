"""
命令行参数解析器 - v2.0 版本

支持以下命令：
- gen-config: 从文件系统生成 Config v2.0
- gen-config-crawler: 从爬虫输出生成 Config v2.0
- validate-config: 验证 Config v2.0
- book_index: 生成书籍索引 HTML
"""

import argparse
from pathlib import Path
from typing import Dict, Any


class ArgumentParser:
    """命令行参数解析器"""

    def __init__(self):
        self.parser = self._create_parser()

    def _create_parser(self) -> argparse.ArgumentParser:
        """创建参数解析器"""
        parser = argparse.ArgumentParser(
            description="Parallel Text Viewer - Generate bilingual HTML from data.",
            epilog="""
Examples:
  python -m parallel_text_viewer gen-config --book-id 2930 --title "Book Title" --working-dir ./data/2930 -o config.json
  python -m parallel_text_viewer validate-config config.json
  python -m parallel_text_viewer book_index --index config.json -d output/
            """,
        )

        # Config v2.0 生成命令
        subparsers = parser.add_subparsers(dest="command", help="Sub-commands")
        
        # gen-config 命令
        gen_config_parser = subparsers.add_parser(
            "gen-config",
            help="Generate Config v2.0 from file system"
        )
        gen_config_parser.add_argument(
            "--book-id",
            required=True,
            help="Book ID"
        )
        gen_config_parser.add_argument(
            "--title",
            required=True,
            help="Book title"
        )
        gen_config_parser.add_argument(
            "--working-dir",
            type=Path,
            default=Path("."),
            help="Working directory to scan"
        )
        gen_config_parser.add_argument(
            "-o", "--output",
            type=Path,
            required=True,
            help="Output config file path"
        )
        gen_config_parser.add_argument(
            "--volume-pattern",
            default="vol_{:03d}",
            help="Volume directory pattern"
        )
        gen_config_parser.add_argument(
            "--image-strategy",
            choices=["directory", "filename", "custom"],
            default="directory",
            help="Image association strategy"
        )
        
        # gen-config-crawler 命令
        crawler_parser = subparsers.add_parser(
            "gen-config-crawler",
            help="Generate Config v2.0 from crawler JSON output"
        )
        crawler_parser.add_argument(
            "--book-id",
            required=True,
            help="Book ID"
        )
        crawler_parser.add_argument(
            "crawler_json",
            type=Path,
            help="Crawler output JSON file"
        )
        crawler_parser.add_argument(
            "-o", "--output",
            type=Path,
            required=True,
            help="Output config file path"
        )
        
        # validate-config 命令
        validate_parser = subparsers.add_parser(
            "validate-config",
            help="Validate Config v2.0 file"
        )
        validate_parser.add_argument(
            "config_file",
            type=Path,
            help="Config file to validate"
        )
        validate_parser.add_argument(
            "--working-dir",
            type=Path,
            default=Path("."),
            help="Working directory for path resolution"
        )
        
        # book_index 命令
        book_index_parser = subparsers.add_parser(
            "book_index",
            help="Generate book index HTML"
        )
        book_index_parser.add_argument(
            "--index",
            type=Path,
            required=True,
            help="Path to book index config JSON file"
        )
        book_index_parser.add_argument(
            "-d", "--output-dir",
            type=Path,
            default=Path("book_output"),
            help="Output directory for book index generation"
        )

        return parser

    def parse_args(self, args=None) -> Dict[str, Any]:
        """解析参数并返回配置字典"""
        parsed = self.parser.parse_args(args)

        # 检查命令类型
        if parsed.command in ["gen-config", "gen-config-crawler", "validate-config", "book_index"]:
            return {
                "mode": parsed.command,
                "book_id": getattr(parsed, "book_id", None),
                "title": getattr(parsed, "title", None),
                "working_dir": getattr(parsed, "working_dir", Path(".")),
                "output": getattr(parsed, "output", None),
                "volume_pattern": getattr(parsed, "volume_pattern", "vol_{:03d}"),
                "image_strategy": getattr(parsed, "image_strategy", "directory"),
                "crawler_json": getattr(parsed, "crawler_json", None),
                "config_file": getattr(parsed, "config_file", None),
                "index": getattr(parsed, "index", None),
                "output_dir": getattr(parsed, "output_dir", Path("book_output")),
            }
        
        # 显示帮助
        self.parser.print_help()
        raise SystemExit(0)