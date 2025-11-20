"""
Config 生成器包

提供从各种数据源自动生成 Config v2.0 的工具
"""

from .generator import (
    ConfigGenerator,
    StandardConfigGenerator,
    CrawlerOutputGenerator,
    CSVConfigGenerator,
    GeneratorRegistry,
)

__all__ = [
    "ConfigGenerator",
    "StandardConfigGenerator",
    "CrawlerOutputGenerator",
    "CSVConfigGenerator",
    "GeneratorRegistry",
]
