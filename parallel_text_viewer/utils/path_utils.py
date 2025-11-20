"""
路径工具

提供路径处理的实用函数。
"""

from pathlib import Path


def resolve_path(base_path: Path, relative_path: str) -> Path:
    """解析相对路径为绝对路径"""
    path = Path(relative_path)
    if path.is_absolute():
        return path
    return base_path / path