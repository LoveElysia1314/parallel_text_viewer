"""
生成器工厂
"""

from pathlib import Path
from typing import Optional

from .single_file import SingleFileGenerator
from .book_index import BookIndexGenerator


class GeneratorFactory:
    """生成器工厂类"""

    def create_single_file_generator(
        self,
        main_file: Path,
        side_file: Path,
        title: str = "Bilingual Viewer",
        primary: str = "a",
        orientation: str = "vertical",
        sync: bool = False,
        ignore_empty: bool = True,
    ) -> SingleFileGenerator:
        """创建单文件生成器"""
        return SingleFileGenerator(
            main_file=main_file,
            side_file=side_file,
            title=title,
            primary=primary,
            orientation=orientation,
            sync=sync,
            ignore_empty=ignore_empty,
        )

    def create_book_index_generator(self, config_file: Path) -> BookIndexGenerator:
        """创建书目索引生成器"""
        return BookIndexGenerator(config_file)