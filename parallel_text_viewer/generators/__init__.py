"""
生成器模块初始化
"""

from .base import Generator
from .single_file import SingleFileGenerator
from .book_index import BookIndexGenerator
from .factory import GeneratorFactory

__all__ = ["Generator", "SingleFileGenerator", "BookIndexGenerator", "GeneratorFactory"]