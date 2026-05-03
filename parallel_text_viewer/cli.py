"""
命令行界面 - 参数解析与命令分发

合并自: cli/parser.py, cli/dispatcher.py
"""

import argparse
import sys
import json
from pathlib import Path
from typing import Dict, Any

from .generators import GeneratorFactory

# ═══════════════════════════════════════════════════════════
# ArgumentParser
# ═══════════════════════════════════════════════════════════


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

        subparsers = parser.add_subparsers(dest="command", help="Sub-commands")

        # gen-config 命令
        gen_config_parser = subparsers.add_parser(
            "gen-config", help="Generate Config v2.0 from file system"
        )
        gen_config_parser.add_argument("--book-id", required=True, help="Book ID")
        gen_config_parser.add_argument("--title", required=True, help="Book title")
        gen_config_parser.add_argument(
            "--working-dir", type=Path, default=Path("."), help="Working directory to scan"
        )
        gen_config_parser.add_argument(
            "-o", "--output", type=Path, required=True, help="Output config file path"
        )
        gen_config_parser.add_argument(
            "--volume-pattern", default="vol_{:03d}", help="Volume directory pattern"
        )
        gen_config_parser.add_argument(
            "--image-strategy",
            choices=["directory", "filename", "custom"],
            default="directory",
            help="Image association strategy",
        )

        # gen-config-crawler 命令
        crawler_parser = subparsers.add_parser(
            "gen-config-crawler", help="Generate Config v2.0 from crawler JSON output"
        )
        crawler_parser.add_argument("--book-id", required=True, help="Book ID")
        crawler_parser.add_argument("crawler_json", type=Path, help="Crawler output JSON file")
        crawler_parser.add_argument(
            "-o", "--output", type=Path, required=True, help="Output config file path"
        )

        # validate-config 命令
        validate_parser = subparsers.add_parser("validate-config", help="Validate Config v2.0 file")
        validate_parser.add_argument("config_file", type=Path, help="Config file to validate")
        validate_parser.add_argument(
            "--working-dir",
            type=Path,
            default=Path("."),
            help="Working directory for path resolution",
        )

        # book_index 命令
        book_index_parser = subparsers.add_parser("book_index", help="Generate book index HTML")
        book_index_parser.add_argument(
            "--index", type=Path, required=True, help="Path to book index config JSON file"
        )
        book_index_parser.add_argument(
            "-d", "--output-dir", type=Path, default=Path("book_output"), help="Output directory"
        )

        return parser

    def parse_args(self, args=None) -> Dict[str, Any]:
        """解析参数并返回配置字典"""
        parsed = self.parser.parse_args(args)

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

        self.parser.print_help()
        raise SystemExit(0)


# ═══════════════════════════════════════════════════════════
# CommandDispatcher
# ═══════════════════════════════════════════════════════════


class CommandDispatcher:
    """命令调度器"""

    def __init__(self):
        self.factory = GeneratorFactory()

    def dispatch(self, config: Dict[str, Any]) -> None:
        """根据配置调度任务"""
        mode = config["mode"]

        try:
            if mode == "gen-config":
                self._handle_gen_config(config)
            elif mode == "gen-config-crawler":
                self._handle_gen_config_crawler(config)
            elif mode == "validate-config":
                self._handle_validate_config(config)
            elif mode == "book_index":
                self._handle_book_index(config)
            else:
                self._show_help()
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)

    def _handle_book_index(self, config: Dict[str, Any]) -> None:
        """处理书目索引模式"""
        if not config["index"].exists():
            raise FileNotFoundError(f"Config file not found: {config['index']}")

        generator = self.factory.create_book_index_generator(config["index"])
        generator.generate(config["output_dir"])
        print(f"Book index generated in {config['output_dir']}")

    def _show_help(self) -> None:
        """显示帮助"""
        parser = ArgumentParser()
        parser.parser.print_help()
        sys.exit(1)

    def _add_output_structure_to_config(
        self, config_file: Path, output_structure: str = "by_volume"
    ) -> None:
        """为配置文件添加输出结构配置"""
        config_file = Path(config_file)
        with open(config_file, "r", encoding="utf-8") as f:
            config = json.load(f)
        config["output_structure"] = output_structure
        config["structure_config"] = {}
        with open(config_file, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=2)

    def _handle_gen_config(self, config: Dict[str, Any]) -> None:
        """处理 gen-config 命令 - 从文件系统生成 Config v2.0"""
        from .core import StandardConfigGenerator, GeneratorOptions

        options = GeneratorOptions(
            book_id=config["book_id"],
            title=config["title"],
            working_dir=str(config["working_dir"]),
            volume_pattern=config["volume_pattern"],
            image_strategy=config["image_strategy"],
        )

        gen = StandardConfigGenerator()
        config_obj = gen.generate(options)
        output_path = gen.save(config["output"])

        output_structure = config.get("output_structure", "by_volume")
        self._add_output_structure_to_config(output_path, output_structure)

        print(f"[OK] Generated config v2.0: {output_path}")
        print(f"  Book ID: {config_obj.meta.book_id}")
        print(f"  Title: {config_obj.meta.title}")
        print(f"  Works: {len(config_obj.works)}")
        for work in config_obj.works:
            print(
                f"    - {work.title}: {len(work.volumes)} volumes, {sum(len(v.chapters) for v in work.volumes)} chapters"
            )

    def _handle_gen_config_crawler(self, config: Dict[str, Any]) -> None:
        """处理 gen-config-crawler 命令 - 从爬虫输出生成 Config v2.0"""
        from .core import CrawlerOutputGenerator, GeneratorOptions

        if not config["crawler_json"].exists():
            raise FileNotFoundError(f"Crawler JSON not found: {config['crawler_json']}")

        options = GeneratorOptions(
            book_id=config["book_id"],
            title=config["book_id"],
        )

        gen = CrawlerOutputGenerator()
        config_obj = gen.generate(options, config["crawler_json"])
        output_path = gen.save(config["output"])

        print(f"[OK] Generated config v2.0 from crawler: {output_path}")
        print(f"  Book ID: {config_obj.meta.book_id}")
        print(f"  Title: {config_obj.meta.title}")
        print(f"  Works: {len(config_obj.works)}")
        for work in config_obj.works:
            print(
                f"    - {work.title}: {len(work.volumes)} volumes, {sum(len(v.chapters) for v in work.volumes)} chapters"
            )

    def _handle_validate_config(self, config: Dict[str, Any]) -> None:
        """处理 validate-config 命令 - 验证 Config v2.0"""
        from .core import ConfigLoader

        if not config["config_file"].exists():
            raise FileNotFoundError(f"Config file not found: {config['config_file']}")

        config_obj = ConfigLoader.load_file(config["config_file"])

        is_valid, errors = ConfigLoader.validate(config_obj, config["working_dir"])

        print(f"Validating config: {config['config_file']}")
        print(f"Book ID: {config_obj.meta.book_id}")
        print(f"Title: {config_obj.meta.title}")
        print(f"Works: {len(config_obj.works)}")

        for work in config_obj.works:
            total_chapters = sum(len(v.chapters) for v in work.volumes)
            print(f"  - {work.title}: {len(work.volumes)} volumes, {total_chapters} chapters")

        if is_valid:
            print("\n[OK] Config is valid!")
        else:
            print("\n[ERROR] Config has errors:")
            for error in errors:
                print(f"  - {error}")
