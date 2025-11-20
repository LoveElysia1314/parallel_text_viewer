"""
命令调度器 - v2.0 版本

支持以下命令：
- gen-config: 从文件系统生成 Config v2.0
- gen-config-crawler: 从爬虫输出生成 Config v2.0
- validate-config: 验证 Config v2.0
- book_index: 生成书籍索引 HTML
"""

import sys
from pathlib import Path
from typing import Dict, Any

from ..generators import GeneratorFactory


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
        from .parser import ArgumentParser
        parser = ArgumentParser()
        parser.parser.print_help()
        sys.exit(1)

    def _add_output_structure_to_config(self, config_file: Path, output_structure: str = "by_volume") -> None:
        """为配置文件添加输出结构配置"""
        import json
        from pathlib import Path
        
        config_file = Path(config_file)
        with open(config_file, "r", encoding="utf-8") as f:
            config = json.load(f)
        
        # 添加输出结构配置
        config["output_structure"] = output_structure
        config["structure_config"] = {}
        
        with open(config_file, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=2)

    def _handle_gen_config(self, config: Dict[str, Any]) -> None:
        """处理 gen-config 命令 - 从文件系统生成 Config v2.0"""
        from ..config.generator import StandardConfigGenerator, GeneratorOptions
        
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
        
        # 添加输出结构配置
        output_structure = config.get("output_structure", "by_volume")
        self._add_output_structure_to_config(output_path, output_structure)
        
        print(f"[OK] Generated config v2.0: {output_path}")
        print(f"  Book ID: {config_obj.meta.book_id}")
        print(f"  Title: {config_obj.meta.title}")
        print(f"  Works: {len(config_obj.works)}")
        for work in config_obj.works:
            print(f"    - {work.title}: {len(work.volumes)} volumes, {sum(len(v.chapters) for v in work.volumes)} chapters")

    def _handle_gen_config_crawler(self, config: Dict[str, Any]) -> None:
        """处理 gen-config-crawler 命令 - 从爬虫输出生成 Config v2.0"""
        from ..config.generator import CrawlerOutputGenerator, GeneratorOptions
        
        if not config["crawler_json"].exists():
            raise FileNotFoundError(f"Crawler JSON not found: {config['crawler_json']}")
        
        options = GeneratorOptions(
            book_id=config["book_id"],
            title=config["book_id"],  # 将由 crawler 数据覆盖
        )
        
        gen = CrawlerOutputGenerator()
        config_obj = gen.generate(options, config["crawler_json"])
        output_path = gen.save(config["output"])
        
        print(f"[OK] Generated config v2.0 from crawler: {output_path}")
        print(f"  Book ID: {config_obj.meta.book_id}")
        print(f"  Title: {config_obj.meta.title}")
        print(f"  Works: {len(config_obj.works)}")
        for work in config_obj.works:
            print(f"    - {work.title}: {len(work.volumes)} volumes, {sum(len(v.chapters) for v in work.volumes)} chapters")

    def _handle_validate_config(self, config: Dict[str, Any]) -> None:
        """处理 validate-config 命令 - 验证 Config v2.0"""
        from ..core.config_v2 import ConfigLoader
        
        if not config["config_file"].exists():
            raise FileNotFoundError(f"Config file not found: {config['config_file']}")
        
        # 加载 config
        config_obj = ConfigLoader.load_file(config["config_file"])
        
        # 验证
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