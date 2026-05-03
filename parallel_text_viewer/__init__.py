"""
Parallel Text Viewer

一个用于将两份逐行对应文本生成为离线查看 HTML 的工具。
"""

__version__ = "0.7.0"
__author__ = "LoveElysia1314"

from .generators import SingleFileGenerator, BookIndexGenerator, GeneratorFactory
from .core import parse_lines, validate_line_counts

__all__ = [
    "SingleFileGenerator",
    "BookIndexGenerator",
    "GeneratorFactory",
    "parse_lines",
    "validate_line_counts",
]
