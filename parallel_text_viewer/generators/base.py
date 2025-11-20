"""
生成器抽象基类
"""

from abc import ABC, abstractmethod
from pathlib import Path


class Generator(ABC):
    """生成器抽象基类"""

    @abstractmethod
    def generate(self, output_path: Path) -> None:
        """生成输出文件"""
        pass